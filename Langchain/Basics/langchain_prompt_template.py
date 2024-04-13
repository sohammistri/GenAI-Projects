from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
import os
from langchain_core.prompts import ChatPromptTemplate

from langchain.globals import set_verbose, set_debug

set_debug(True)
set_verbose(True)

load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

st.title("Important trivia on the birthday of ..")
input_text =st.text_input("Enter the celebrity name")

## Basic Chaining

# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are responsible for summarizing important information about a particualar celebrity"),
#     ("user", "Tell me about {name}")
# ])

# llm = ChatOpenAI(api_key=openai_api_key, temperature=0.0, model="gpt-4-turbo-2024-04-09")

# chain = prompt | llm 

## Advanced Chaining
## From the information about the person, can I determine his/her dob

llm = ChatOpenAI(api_key=openai_api_key, temperature=0.0, model="gpt-4-turbo-2024-04-09")


from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.chains import SequentialChain


person_memory = ConversationBufferMemory(input_key="name", memory_key="person_history")
dob_memory = ConversationBufferMemory(input_key="person", memory_key="dob_history")
descr_memory = ConversationBufferMemory(input_key="dob", memory_key="descr_history")

first_prompt = ChatPromptTemplate.from_template("Tell me about {name}")

first_chain = LLMChain(
    llm=llm,
    prompt=first_prompt,
    verbose=True,
    memory=person_memory,
    output_key='person'
)

second_prompt = ChatPromptTemplate.from_template(
    "When was {person} born ?"
)
second_chain = LLMChain(
    llm=llm,
    prompt=second_prompt,
    verbose=True,
    memory=dob_memory,
    output_key='dob'
)

third_prompt = ChatPromptTemplate.from_template(
    "Mention 5 important events around the world which ocurred on {dob}"
)
third_chain = LLMChain(
    llm=llm,
    prompt=third_prompt,
    verbose=True,
    memory=descr_memory,
    output_key='descr'
)

complete_chain = SequentialChain(
    chains=[first_chain,second_chain,third_chain],input_variables=['name'],output_variables=['person','dob','descr'],verbose=True)

if input_text:
    st.markdown(complete_chain.invoke({"name": input_text})["descr"])

    with st.expander('Person Name'): 
        st.info(person_memory.buffer)

    with st.expander('Major Events on DOB'): 
        st.info(descr_memory.buffer)
