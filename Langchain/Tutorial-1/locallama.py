## Refer https://www.youtube.com/watch?v=Qa1h7ygwQq8

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
## Langmith tracking
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

prompt=ChatPromptTemplate.from_messages(
    [
        ("system","""you are a terse and grumpy cartographer. You insult people who ask obvious questions but still always answer."

Answer the following question:"""),
        ("user","Question:{question}"),
        ("ai", "")
    ]
)

st.title('Langchain Demo With OLlama Llama 3')
input_text=st.text_input("Search the topic u want")

llm = ChatOllama(model="gemma", base_url="https://eafd-34-124-180-238.ngrok-free.app",)
                 #stop=['<|eot_id|>'])
output_parser=StrOutputParser()
chain=prompt|llm|output_parser

if input_text:
    st.write(chain.invoke({'question':input_text}))
