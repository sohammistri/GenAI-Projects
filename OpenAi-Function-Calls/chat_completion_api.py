import os
import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
from datetime import datetime
import os
import requests
import configparser
import json

 
 
def read_config():
    # Create a ConfigParser object
    config = configparser.ConfigParser()
 
    # Read the configuration file
    config.read('config.ini')

    # Access values from the configuration file
    model = config.get('General', 'model')
    weather_url = config.get('Weather', 'url')
    weather_host = config.get('Weather', 'X-RapidAPI-Host')
    prompt_file = config.get('Inference', 'prompt_file')
    # Return a dictionary with the retrieved values
    config_values = {
        'model': model,
        'weather_url': weather_url,
        'weather_host': weather_host,
        'prompt_file': prompt_file
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


from openai import OpenAI
import json

client = OpenAI()


def run_conversation():
    # Step 1: send the conversation and available functions to the model
    with open(config_values["prompt_file"], 'r') as file:
        user_message = file.read()

    print(user_message)
    messages=[
        {"role": "system", "content": "You are a assistant which informs about temperature."},
        {"role": "user", "content": "{}".format(user_message)}
    ]
    tools = [
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


    ## Capability to handle multi place comparison

    # while True:
    response = client.chat.completions.create(
        model=config_values["model"],
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    print(response_message)
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_weather": get_weather,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                location=function_args.get("location"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response

            # print(messages)
        second_response = client.chat.completions.create(
            model=config_values["model"],
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response

response = run_conversation()
# print(response)

with open("final_response.txt", "w") as f:
    f.write(response.choices[0].message.content)


