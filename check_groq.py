
"""Smoke test: check that the Groq API key and model in .env work."""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model=os.getenv("GROQ_MODEL"), temperature=0)
response = llm.invoke("Reply only with: 'Groq works'")
print(response.content)
