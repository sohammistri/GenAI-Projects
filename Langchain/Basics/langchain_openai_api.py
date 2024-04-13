from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
import os

load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

st.title("LangChain demo with OpenAI API")
input_text =st.text_input("Enter your prompt")

llm = ChatOpenAI(api_key=openai_api_key, temperature=0.0, model="gpt-4-turbo-2024-04-09")


if input_text:
    st.write(llm.invoke(input_text).content)
