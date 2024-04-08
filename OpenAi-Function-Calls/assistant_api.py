import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
from datetime import datetime
import os
import json
import requests

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
    weather_url = config.get('Weather', 'url')
    weather_host = config.get('Weather', 'X-RapidAPI-Host')
    prompt_file = config.get('Inference', 'prompt_file')
    instructions = config.get('Inference', 'instructions')

    # Return a dictionary with the retrieved values
    config_values = {
        'assistant_id': assistant_id,
        'thread_id': thread_id,
        'model': model,
        'weather_url': weather_url,
        'weather_host': weather_host,
        'prompt_file': prompt_file,
        'instructions': instructions
    }
 
    return config_values

config_values = read_config()
# print(config_values)

load_dotenv()
weather_api_key = os.environ.get("WEATHER_API_KEY")
client = openai.OpenAI()

def get_weather(location):
    url = config_values["weather_url"]
    querystring = {"location":location, "format":"json", "u":"c"}

    headers = {
        "X-RapidAPI-Key": weather_api_key,
        "X-RapidAPI-Host": config_values["weather_host"]
    }

    response = requests.get(url, headers=headers, params=querystring)
    # print(response.json())
    return json.dumps(response.json())


class WeatherBotAssistant:
    def __init__(self, config_values, available_functions) -> None:
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
        self.available_functions = available_functions

    def create_assistant(self, name, instructions, tools, model) -> None:
        if not self.assistant_id:
            assistant = self.client.beta.assistants.create(
                name=name, instructions=instructions,
                tools=tools, model=model
            )
            self.assistant_id = assistant.id
            print("Assistnt id: ",self.assistant_id)

    def create_thread(self) -> None:
        if not self.thread_id:
            thread_obj = self.client.beta.threads.create()
            self.thread_id = thread_obj.id
            print("Thread id: ", self.thread_id)
    
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
            print(f"SUMMARY-----> {role.capitalize()}: ==> {response}")


    def call_required_functions(self, required_actions):
        if not self.run_id:
            return
        
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name in self.available_functions:
                func = self.available_functions[func_name]
                output = func(location=arguments.get("location"),)
                print(f"STUFFFFF;;;;{output}")
                # final_str = ""
                # for item in output:
                #     final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"], 
                                     "output": output})
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id, run_id=self.run_id, tool_outputs=tool_outputs
        )


    def wait_for_completion(self):
        if self.thread_id and self.run_id:
            while True:
                time.sleep(5)
                run = client.beta.threads.runs.retrieve(thread_id=self.thread_id, run_id=self.run_id)
                if run.status == "completed":
                    self.process_message()
                    break
                elif run.status == "requires_action":
                    ## This status is for calling function
                    print("FUNCTION CALLING NOW...")
                    self.call_required_functions(
                        required_actions=run.required_action.submit_tool_outputs.model_dump()
                    )


def main():
    available_functions = {
        "get_weather": get_weather,
    } 

    assistant = WeatherBotAssistant(config_values, available_functions)

    print("Creating assistant...")
    assistant_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]
    assistant.create_assistant(name="Weather Bot",\
                                instructions="You are a assistant which informs about temperature.",\
                                    model=config_values["model"], tools=assistant_tools)
    
    print("Creating thread...")
    assistant.create_thread()

    print("Adding message to thread...")
    with open(config_values["prompt_file"], "r") as file:
        prompt = file.read()
    assistant.add_message_to_thread(role="user", content=prompt)

    print("Creating run...")
    assistant.run_assistant(instructions=config_values["instructions"])

    print("Running..")
    assistant.wait_for_completion()

if __name__=="__main__":
    main()




