from langchain_community.llms import HuggingFaceEndpoint
import streamlit as st
import os
# from dotenv import load_dotenv

# load_dotenv()
# huggingface_api_key = os.environ["HUGGINGFACEHUB_API_TOKEN"]

def get_response(question):
    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        max_length=128,
        temperature=0.1,
        token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
    )
    response=llm(question)
    return response

st.set_page_config(page_title="Q&A Demo")

st.header("Langchain Application")

input=st.text_input("Input: ",key="input")

submit=st.button("Ask the question")

## If ask button is clicked

if submit:
    st.subheader("The Response is")
    response  = get_response(input)
    st.write(response)


