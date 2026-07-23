import os
from typing import Optional, List
from openai import OpenAI
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.vector_stores.supabase import SupabaseVectorStore
# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Imports removed to break circular dependency

import logging

logger = logging.getLogger(__name__)

PROMPT_EXTRACT_TEXT_FROM_IMAGE = "Extract all text from this image exactly as it appears. Do not describe it, just output the text."
PROMPT_FORMAT_SOLUTION = "Format the following solution into a clear, numbered step-by-step format suitable for WhatsApp messages. Ensure each step is concise and actionable."

def get_embedding(text: str) -> list:
    """Generates embedding for query."""
    try:
        logger.info(f"Generating embedding for text: '{text[:50]}...'")
        response = client.embeddings.create(
            input=text,
            model=os.getenv("EMBEDDING_MODEL", os.getenv("EMBEDDING_MODEL"))
        )
        logger.info("Embedding generated successfully.")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []

def extract_text_from_image(base64_image: str, user_input: str = "") -> str:
    """
    Extracts text/description from a base64 encoded image using GPT-4o.
    """
    image_url = base64_image if base64_image.startswith("data:") else f"data:image/jpeg;base64,{base64_image}"
    try:
        logger.info(f"Sending image to OpenAI Vision for OCR (User Input: '{user_input}')...")
        ocr_response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_EXTRACT_TEXT_FROM_IMAGE},
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": f"User's text (if any): {user_input}"}
                    ],
                }
            ],
            max_tokens=300,
        )
        result = ocr_response.choices[0].message.content
        logger.info(f"OCR Success. Result: {result[:100]}...")
        return result
    except Exception as e:
        logger.error(f"Error during image description: {e}")
        return ""

# TODO: save formatted solution in DB instead of calling OpenAI every time in format_solution. We can do this when ingesting data or when saving error logs after a chat interaction.

import base64

def extract_text_from_image_path(image_path: str) -> str:
    """
    Reads a local image file, encodes it to base64, and extracts text using GPT-4o.
    """
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # We can reuse the existing function, but let's make the prompt specific for raw text extraction
        # The existing function 'extract_text_from_image' has a specific prompt about "Describe the error message".
        # For pure OCR comparison, we might want a slightly different prompt like "Extract all text from this image."
        # But the user wants to "see response it generates in the same way", so maybe the "Describe" prompt is better?
        # Actually, Tesseract gives raw text. OpenAI "Describe" gives a description.
        # If we want to compare "OCR", we should ask OpenAI to "Extract text".
        
        return extract_text_from_image_custom_prompt(base64_image)
    except Exception as e:
        print(f"Error processing image path {image_path}: {e}")
        return ""

def extract_text_from_image_custom_prompt(base64_image: str) -> str:
    """
    Helper to call OpenAI Vision with a custom prompt.
    """
    image_url = f"data:image/jpeg;base64,{base64_image}"
    try:
        ocr_response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_EXTRACT_TEXT_FROM_IMAGE},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=1000,
        )
        return ocr_response.choices[0].message.content
    except Exception as e:
        print(f"Error during OpenAI OCR: {e}")
        return ""

# save formatted solution in DB instead of calling OpenAI every time in format_solution. We can do this when ingesting data or when saving error logs after a chat interaction.
def format_solution(solution_text: str) -> str:
    """
    Formats a solution string into a numbered step format for WhatsApp.
    """
    try:
        logger.info("Formatting solution via OpenAI...")
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            messages=[
                {
                    "role": "system", 
                    "content": PROMPT_FORMAT_SOLUTION
                },
                {
                    "role": "user",
                    "content": f'Original: "{solution_text}"'
                }
            ],
            temperature=0.2
        )
        logger.info("Solution formatted successfully.")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error formatting solution: {e}")
        return solution_text