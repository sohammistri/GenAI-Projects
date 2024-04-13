from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
import os

from langchain.globals import set_verbose, set_debug

from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)

set_debug(True)
set_verbose(True)

load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

## Few Shot Prompt Examples

## Source : https://python.langchain.com/docs/modules/model_io/prompts/few_shot_examples_chat/

examples = [
    {"input": "2+2", "output": "Answer is 4"},
    {"input": "2+3", "output": "Answer is 5"},
]

example_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{input}"),
        ("ai", "{output}"),
    ]
)
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

print(few_shot_prompt.format())

final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a wondrous wizard of math."),
        few_shot_prompt,
        ("human", "{input}"),
    ]
)

llm = ChatOpenAI(api_key=openai_api_key, temperature=0.0, model="gpt-3.5-turbo-0125")

chain = final_prompt | llm

print(chain.invoke({"input": "9*10"}).content)