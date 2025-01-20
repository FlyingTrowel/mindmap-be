"""
Install an additional SDK for JSON schema support Google AI Python SDK

$ pip install google.ai.generativelanguage
"""

import os
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

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
              required = ["id", "title", "unchangedText"],
              properties = {
                "id": content.Schema(
                  type = content.Type.STRING,
                ),
                "title": content.Schema(
                  type = content.Type.STRING,
                ),
                "description": content.Schema(
                  type = content.Type.STRING,
                ),
                "unchangedText": content.Schema(
                  type = content.Type.STRING,
                ),
                "references": content.Schema(
                  type = content.Type.ARRAY,
                  items = content.Schema(
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
                ),
                "children": content.Schema(
                  type = content.Type.ARRAY,
                  items = content.Schema(
                    type = content.Type.STRING,
                  ),
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

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
  generation_config=generation_config,
)

chat_session = model.start_chat(
  history=[
  ]
)

response = chat_session.send_message("INSERT_INPUT_HERE")

print(response.text)