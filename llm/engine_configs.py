from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import VertexAI
from google.oauth2 import service_account
from google.cloud import aiplatform
from typing import Dict, Any
import vertexai
from langchain_google_vertexai import HarmBlockThreshold, HarmCategory
import os

safety_settings = {
    HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}


GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION")
GCP_CREDENTIALS = os.getenv("GCP_CREDENTIALS")

if GCP_CREDENTIALS and GCP_PROJECT and GCP_REGION:
    aiplatform.init(
    project=GCP_PROJECT,
    location=GCP_REGION,
    credentials=service_account.Credentials.from_service_account_file(GCP_CREDENTIALS)
    )
    vertexai.init(project=GCP_PROJECT, location=GCP_REGION, credentials=service_account.Credentials.from_service_account_file(GCP_CREDENTIALS))

"""
This module defines configurations for various language models using the langchain library.
Each configuration includes a constructor, parameters, and an optional preprocessing function.
"""

ENGINE_CONFIGS: Dict[str, Dict[str, Any]] = {
        "llama3.2:latest": {
        "constructor": ChatOllama,
        "params": {
            "model": "llama3.2:latest",
            "temperature": 0,
            "max_tokens": 600,
        }
    }
}
