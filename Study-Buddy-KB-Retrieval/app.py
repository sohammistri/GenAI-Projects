import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
from datetime import datetime
import os

import configparser

def read_config():
    # Create a ConfigParser object
    config = configparser.ConfigParser()
 
    # Read the configuration file
    config.read('config.ini')

    # Access values from the configuration file
    assistant_id = config.get('General', 'assistant_id')
    thread_id = config.get('General', 'thread_id')
    model = config.get('General', 'model')
    model_instructions_file = config.get('General', 'model_instructions_file')
    file_path = config.get('Inference', 'file_path')
    prompt_file = config.get('Inference', 'prompt_file')
    response_instructions = config.get('Inference', 'response_instructions')
    response_file = config.get('Inference', 'response_file')

    # Return a dictionary with the retrieved values
    config_values = {
        'assistant_id': assistant_id,
        'thread_id': thread_id,
        'model': model,
        'model_instructions_file': model_instructions_file,
        'file_path': file_path,
        'prompt_file': prompt_file,
        'response_instructions': response_instructions,
        'response_file': response_file
    }
 
    return config_values

config_values = read_config()
print(config_values)

load_dotenv()

client = openai.OpenAI()


class StudyBuddyAssistant:
    def __init__(self, config_values) -> None:
        self.client = client
        if config_values["assistant_id"]=='-1':
            self.assistant_id = None
        else:
            self.assistant_id = config_values["assistant_id"]

        if config_values["thread_id"]=='-1':
            self.thread_id = None
        else:
            self.thread_id = config_values["thread_id"]
        
        self.run_id = None
        self.summary = None
    
    def create_assistant(self, name, instructions, model) -> None:
        if not self.assistant_id:
            assistant = self.client.beta.assistants.create(
                name=name, instructions=instructions,
                model=model, tools=[{"type": "retrieval"}]
            )
            self.assistant_id = assistant.id
            print("Assistnt id: ",self.assistant_id)

    def create_thread(self) -> None:
        if not self.thread_id:
            thread_obj = self.client.beta.threads.create()
            self.thread_id = thread_obj.id
            print("Thread id: ", self.thread_id)

    def upload_file(self, file_path):
            file_obj = client.files.create(file=open(file_path, "rb"), purpose="assistants") 
            self.client.beta.assistants.files.create(assistant_id=self.assistant_id, file_id=file_obj.id)   
    
    def add_message_to_thread(self, role, content) -> None:
        if self.thread_id:
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id, role=role, content=content
            )

    def run_assistant(self, instructions) -> None:
        if self.thread_id and self.assistant_id:
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                instructions=instructions,
            )
            self.run_id = run.id
            print("Run id: ", self.run_id)

    def process_message(self):
        if self.thread_id:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
            summary = []

            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)

            self.summary = "\n".join(summary)
            # print(f"SUMMARY-----> {role.capitalize()}: ==> {response}")


    def wait_for_completion(self):
        if self.thread_id and self.run_id:
            while True:
                time.sleep(5)
                run = client.beta.threads.runs.retrieve(thread_id=self.thread_id, run_id=self.run_id)
                if run.status == "completed":
                    self.process_message()
                    break

    def get_summary(self):
        return self.summary


def main():
    print("Creating assistant...")
    assistant = StudyBuddyAssistant(config_values)
    with open(config_values["model_instructions_file"], "r") as f:
        instructions = f.read()
    assistant.create_assistant(name="Study Buddy Bot",\
                                instructions=instructions,\
                                    model=config_values["model"])
    
    # print("Uploading files...")
    # assistant.upload_file(config_values["file_path"])
    
    print("Creating thread...")
    assistant.create_thread()

    print("Adding message to thread...")
    with open(config_values["prompt_file"], "r") as f:
        prompt = f.read()
    assistant.add_message_to_thread(role="user", content=prompt)

    print("Creating run...")
    assistant.run_assistant(instructions=config_values["response_instructions"])

    print("Running..")
    assistant.wait_for_completion()

    print("Saving response")
    response = assistant.get_summary()
    with open(config_values["response_file"], "w") as f:
        f.write(response)

if __name__=="__main__":
    main()

