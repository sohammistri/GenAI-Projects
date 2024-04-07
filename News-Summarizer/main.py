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
    # assistant_id = config.get('General', 'assistant_id')
    # thread_id = config.get('General', 'thread_id')
    model = config.get('General', 'model')
    # message_file = config.get('Inference', 'message_file')
    # instructions = config.get('Inference', 'instructions')
    # response_file = config.get('Inference', 'response_file')

    # Return a dictionary with the retrieved values
    config_values = {
        # 'assistant_id': assistant_id,
        # 'thread_id': thread_id,
        'model': model,
        # 'message_file': message_file,
        # 'instructions': instructions,
        # "response_file": response_file
    }
 
    return config_values

config_values = read_config()

load_dotenv()
news_api_key = os.environ.get("NEWS_API_KEY")

client = openai.OpenAI()

def get_news(topic):
    url = (f"""https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5""")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = json.dumps(response.json(), indent=4)
            news_json = json.loads(news)

            data = news_json

            # Access all the fiels == loop through
            status = data["status"]
            total_results = data["totalResults"]
            articles = data["articles"]
            final_news = []

            # Loop through articles
            for article in articles:
                source_name = article["source"]["name"]
                author = article["author"]
                title = article["title"]
                description = article["description"]
                url = article["url"]
                content = article["content"]
                title_description = f"""
                   Title: {title}, 
                   Author: {author},
                   Source: {source_name},
                   Description: {description},
                   URL: {url}
            
                """
                final_news.append(title_description)

            return final_news
        else:
            return []

    except requests.exceptions.RequestException as e:
        print("Error occured during API Request", e)

class NewsSummarizerAssistant:
    def __init__(self, config_values) -> None:
        self.client = client
        if "assistant_id" not in config_values:
            self.assistant_id = None
        else:
            self.assistant_id = config_values["assistant_id"]

        if "thread_id" not in config_values:
            self.thread_id = None
        else:
            self.thread_id = config_values["thread_id"]
        
        self.run_id = None
        self.summary = None

    def create_assistant(self, name, instructions, tools, model) -> None:
        if not self.assistant_id:
            assistant = self.client.beta.assistants.create(
                name=name, instructions=instructions,
                tools=tools, model=model
            )
            self.assistant_id = assistant.id

    def create_thread(self) -> None:
        if not self.thread_id:
            thread_obj = self.client.beta.threads.create()
            self.thread_id = thread_obj.id
    
    def add_message_to_thread(self, role, content) -> None:
        if self.thread_id:
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id, role=role, content=content
            )

    def run_assistant(self, instructions) -> None:
        if self.thread_id and self.asistant_id:
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.asistant_id,
                instructions=instructions,
            )
            self.run_id = run.id
    
    def process_message(self) -> None:
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
    print(get_news("bitcoin")[0])

if __name__=="__main__":
    main()