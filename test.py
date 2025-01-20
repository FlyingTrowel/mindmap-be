from transformers import pipeline

# Initialize a simple pipeline
nlp = pipeline("sentiment-analysis")

# Test the pipeline
result = nlp("I love using Hugging Face Transformers!")
print(result)