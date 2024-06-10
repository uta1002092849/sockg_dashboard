import streamlit as st
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.llms import Ollama

gemini_pro = GoogleGenerativeAI(
    google_api_key = st.secrets['API_KEY'],
    model= st.secrets['MODEL']
)

llama3 = Ollama(
    model="llama3",
)
