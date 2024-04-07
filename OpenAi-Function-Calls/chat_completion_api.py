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
    user_message = config.get('Inference', 'user_message')
    # Return a dictionary with the retrieved values
    config_values = {
        'model': model,
        'weather_url': weather_url,
        'weather_host': weather_host,
        'user_message': user_message
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
    print(response.json())
    return response.json()



functions = [
        {
            "name": "get_weather",
            "description": "Get the current weather conditions in a given location",
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
        }
    ]


available_functions = {
    "get_weather": get_weather,
}

available_functions_args = {
    'get_weather': ['location']
}

messages=[
    {"role": "system", "content": "You are a assistant which informs about temperature."},
    {"role": "user", "content": "Hey there"}
]
messages.append({"role": "user", "content": config_values["user_message"]})

response1 = client.chat.completions.create(
  model=config_values["model"],
    messages=messages,
    functions=functions
)

response1_message = response1.choices[0].message
print(response1_message)

if response1_message.function_call:
    messages.append(response1_message)

    function_name = response1_message.function_call.name
    if function_name in available_functions:
        function_arg_list = []
        function_arg_dict = eval(response1_message.function_call.arguments)

        for arg in available_functions_args[function_name]:
            if arg in function_arg_dict:
                function_arg_list.append(function_arg_dict[arg])

        function_to_call = available_functions[function_name]
        function_response = function_to_call(**function_arg_dict)

        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_arg_list[0],
            }
        )

        response2 = client.chat.completions.create(
            model=config_values["model"],
            messages=messages,
            functions=functions
        )

        with open("final_response.txt", "w") as f:
            f.write(response2.choices[0].message.content)


