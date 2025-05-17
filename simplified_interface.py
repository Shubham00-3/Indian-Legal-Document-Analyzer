import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.title("Legal Document Analyzer")

# Check for API keys and display status (don't stop execution)
groq_key = os.getenv("GROQ_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

st.write("API Keys Status:")
if groq_key:
    st.success("✅ GROQ API key found")
else:
    st.error("❌ GROQ API key missing")
    
if pinecone_key:
    st.success("✅ Pinecone API key found")
else:
    st.error("❌ Pinecone API key missing")

st.write("This is a simplified test of the Legal Document Analyzer interface.")