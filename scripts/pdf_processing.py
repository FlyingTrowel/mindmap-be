import sys
import json
import PyPDF2
import re
import os
import google.generativeai as genai
from typing import Dict, List, Union
from google.ai.generativelanguage_v1beta.types import content

# Configure Gemini API
genai.configure(api_key="AIzaSyCVsvT8_0fUBbsVsOnD-Iblk3lqZPOj2qA")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file and return it as a single string
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            full_text = ''
            for page in pdf_reader.pages:
                full_text += page.extract_text() + '\n'
            return full_text
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File {pdf_path} not found")
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def is_research_paper(text: str) -> bool:
    """
    Detect if the document is a research paper by checking for common section headers
    """
    section_indicators = [
        r'(?i)\b(abstract)\b',
        r'(?i)\b(introduction)\b',
        r'(?i)\b(methodology|methods|method)\b',
        r'(?i)\b(results)\b',
        r'(?i)\b(discussion)\b',
        r'(?i)\b(conclusion|conclusions)\b',
        r'(?i)\b(references|bibliography)\b'
    ]
    
    section_count = 0
    for pattern in section_indicators:
        if re.search(pattern, text):
            section_count += 1
    
    return section_count >= 5

def segment_research_paper(text: str) -> Dict[str, str]:
    """
    Segment research paper into its major sections using regex
    """
    sections_patterns = {
        'abstract': r'(?i)(Abstract\s*\n+)(.+?)(?=\n*[0-9IVX]+[\.\s]*Introduction|$)',
        'introduction': r'(?i)([0-9IVX]+[\.\s]*Introduction\s*\n+)(.+?)(?=\n*[0-9IVX]+[\.\s]*(?:Background|Literature Review|Methodology|Method|Methods|Related Work)|$)',
        'methodology': r'(?i)([0-9IVX]+[\.\s]*(?:Methodology|Method|Methods|Experimental Setup)\s*\n+)(.+?)(?=\n*[0-9IVX]+[\.\s]*(?:Results|Discussion|Implementation)|$)',
        'results': r'(?i)([0-9IVX]+[\.\s]*Results\s*\n+)(.+?)(?=\n*[0-9IVX]+[\.\s]*(?:Discussion|Conclusion)|$)',
        'discussion': r'(?i)([0-9IVX]+[\.\s]*Discussion\s*\n+)(.+?)(?=\n*[0-9IVX]+[\.\s]*(?:Conclusion|Future Work)|$)',
        'conclusion': r'(?i)([0-9IVX]+[\.\s]*(?:Conclusion|Conclusions)[\s\n]+)(.+?)(?=\n*[0-9IVX]+[\.\s]*(?:References|Bibliography|Acknowledgments)|$)',
        'references': r'(?i)(References|Bibliography\s*\n+)(.+?)(?=\n*(?:Appendix|$))',
    }
    
    sections = {}
    for section_name, pattern in sections_patterns.items():
        matches = re.search(pattern, text, re.DOTALL)
        if matches:
            sections[section_name] = matches.group(2).strip()
        else:
            sections[section_name] = "Section not found"
    
    return sections

def get_mindmap_model():
    """
    Configure and return the Gemini model for mindmap generation
    """
   # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_schema": content.Schema(
        type = content.Type.OBJECT,
        enum = [],
        required = ["mindMap"],
        properties = {
        "mindMap": content.Schema(
            type = content.Type.OBJECT,
            enum = [],
            required = ["title", "nodes"],
            properties = {
            "title": content.Schema(
                type = content.Type.STRING,
            ),
            "nodes": content.Schema(
                type = content.Type.ARRAY,
                items = content.Schema(
                type = content.Type.OBJECT,
                enum = [],
                required = ["id", "title", "content", "unchangedText"],
                properties = {
                    "id": content.Schema(
                    type = content.Type.STRING,
                    ),
                    "title": content.Schema(
                    type = content.Type.STRING,
                    ),
                    "content": content.Schema(
                    type = content.Type.OBJECT,
                    enum = [],
                    required = ["keyPoints"],
                    properties = {
                        "keyPoints": content.Schema(
                        type = content.Type.ARRAY,
                        items = content.Schema(
                            type = content.Type.STRING,
                        ),
                        ),
                        "keyPointsExplanation": content.Schema(
                        type = content.Type.ARRAY,
                        items = content.Schema(
                            type = content.Type.STRING,
                        ),
                        ),
                        "externalReferences": content.Schema(
                        type = content.Type.OBJECT,
                        enum = [],
                        required = ["title", "url"],
                        properties = {
                            "title": content.Schema(
                            type = content.Type.STRING,
                            ),
                            "url": content.Schema(
                            type = content.Type.STRING,
                            ),
                        },
                        ),
                    },
                    ),
                    "unchangedText": content.Schema(
                    type = content.Type.STRING,
                    ),
                },
                ),
            ),
            },
        ),
        },
    ),
    "response_mime_type": "application/json",
    }
    
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
    )

def generate_mindmap(text: str) -> Dict:
    """
    Generate a mindmap from the given text using Gemini
    """
    try:
        model = get_mindmap_model()
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(text)
        return json.loads(response.text)
    except Exception as e:
        raise Exception(f"Error generating mindmap: {str(e)}")

def process_pdf_and_generate_mindmap(pdf_path: str) -> Dict:
    """
    Process the PDF and generate a mindmap from its contents
    """
    try:
        # Extract text from PDF
        full_text = extract_text_from_pdf(pdf_path)
        
        # Check if it's a research paper
        # is_research = is_research_paper(full_text)
        
        # Prepare text for mindmap generation
        # if is_research:
        #     sections = segment_research_paper(full_text)
        #     # Create a structured prompt for research papers
        #     mindmap_input = f"""
        #     You will receive text extracted from a PDF document. The text may be segmented into sections.

        #     Your task is to:
        #     1. Extract key information and create nodes for a mind map.
        #     2. Include the title, description: try not to make a general summarization. state all the keypoints, and the unchanged original text for each node.
        #     3. Identify external references if applicable and include them with a title and URL.

        #     Please generate the JSON output based on the given text. Here is the text for processing:
            
        #     Abstract:
        #     {sections['abstract']}
            
        #     Introduction:
        #     {sections['introduction']}
            
        #     Methodology:
        #     {sections['methodology']}
            
        #     Results:
        #     {sections['results']}
            
        #     Discussion:
        #     {sections['discussion']}
            
        #     Conclusion:
        #     {sections['conclusion']}
        #     """
        # else:
        mindmap_input = f"""
        You will receive text extracted from a PDF document. The text may be segmented into sections.

        Your task is to:
        1. Extract key information and create nodes for a mind map.
        2. Include the title, a brief description, and the unchanged original text for each node.
        3. Identify external sources for each keypoints for extra information, if applicable and include them with a title and URL.

        Please generate the JSON output based on the given text. Here is the text for processing:
        \n\n{full_text}
        """
        
        # Generate mindmap
        mindmap = generate_mindmap(mindmap_input)
        
        return {
            "success": True,
            # "is_research_paper": is_research,
            # "content_type": "research_paper" if is_research else "general_document",
            "mindmap": mindmap
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    # Check if PDF path is provided as command line argument
    if len(sys.argv) < 2:
        result = {
            "success": False,
            "error": "No PDF path provided"
        }
        print(json.dumps(result))
        sys.exit(1)
    
    # Get PDF path from command line argument
    pdf_path = sys.argv[1]
    
    # Process the PDF and generate mindmap
    result = process_pdf_and_generate_mindmap(pdf_path)
    
    # Output result as JSON
    print(json.dumps(result))

if __name__ == "__main__":
    main()