# cv_analyzer.py

import os
import json
import fitz  # PyMuPDF
from file_reader import read_file
from groq import Groq

from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text_content = ""
    # On boucle sur toutes les pages pour récupérer tout le texte
    for page in doc:
        text_content += page.get_text() + "\n"
        
    return text_content


def analyze_cv_text(cv_path: str, prompt_text: str) -> dict:

    cv_text = extract_text_from_pdf(cv_path)
    
    api_key = os.environ["GROQ_API_KEY"]
   
    client = Groq(api_key=api_key)
    
    full_content = f"{read_file('prompts/prompt_cv.txt')}\n\n--- CONTENU DU CV ---\n{cv_text}"

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": full_content
            }
        ],

        model="meta-llama/llama-4-scout-17b-16e-instruct", 
        
        response_format={"type": "json_object"}, 
        temperature=0.1
    )
    
    return json.loads(chat_completion.choices[0].message.content)