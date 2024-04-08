import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
from datetime import datetime, timedelta
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
    news_url = config.get('News', 'url')
    news_query = config.get('Inference', 'query')
    instructions = config.get('Inference', 'instructions')

    # Return a dictionary with the retrieved values
    config_values = {
        'assistant_id': assistant_id,
        'thread_id': thread_id,
        'model': model,
        'news_url': news_url,
        'news_query': news_query,
        'instructions': instructions
    }
 
    return config_values

config_values = read_config()

load_dotenv()
news_api_key = os.environ.get("NEWS_API_KEY")

client = openai.OpenAI()

def get_news(topic, timeframe=7):
    start_date = datetime.today() - timedelta(days=timeframe)
    start_date = start_date.strftime('%Y-%m-%d')
    url = (f"""{config_values["news_url"]}?q={topic}&from={start_date}&apiKey={news_api_key}&pageSize=5""")
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
            print(arguments)

            if func_name in self.available_functions:
                func = self.available_functions[func_name]
                # arg_list = 
                # if "topic" in arguments:
                #     arg_list.append(arguments.get("topic"))
                # if "timeframe" in arguments:
                #     arg_list.append(arguments.get("timeframe"))

                output = func(**arguments)
                # print(f"STUFFFFF;;;;{output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"], 
                                     "output": final_str})
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")
        # print(tool_outputs)
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
                    required_actions=run.required_action.submit_tool_outputs.model_dump()
                    print(required_actions)
                    self.call_required_functions(
                        required_actions=required_actions
                    )

def main():
    available_functions = {
        "get_news": get_news,
    } 

    assistant = NewsSummarizerAssistant(config_values, available_functions)

    print("Creating assistant...")
    assistant_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_news",
                "description": "Get the current news on a given topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic on which the news is to fetched.",
                        },
                        "timeframe": {
                            "type": "integer",
                            "description": "The number of days before today's date from which we fetch news",
                        },
                    },
                    "required": ["topic"],
                },
            },
        }
    ]
    assistant.create_assistant(name="News Summarizer Bot",\
                                instructions="You are a assistant which summarized several news article content to brief readable format.",\
                                    model=config_values["model"], tools=assistant_tools)
    
    print("Creating thread...")
    assistant.create_thread()

    print("Adding message to thread...")
    assistant.add_message_to_thread(role="user", content=f"""Give me the relevant headlines on {config_values["news_query"]} from the past 30 days.""")

    print("Creating run...")
    assistant.run_assistant(instructions=config_values["instructions"])

    print("Running..")
    assistant.wait_for_completion()

if __name__=="__main__":
    main()