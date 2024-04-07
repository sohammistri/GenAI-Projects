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
    message_file = config.get('Inference', 'message_file')
    instructions = config.get('Inference', 'instructions')
    response_file = config.get('Inference', 'response_file')

    # Return a dictionary with the retrieved values
    config_values = {
        'assistant_id': assistant_id,
        'thread_id': thread_id,
        'model': model,
        'message_file': message_file,
        'instructions': instructions,
        "response_file": response_file
    }
 
    return config_values

config_values = read_config()
print(config_values)

load_dotenv()
# openai.api_key = os.environ.get("OPENAI_API_KEY")
# defaults to getting the key using os.environ.get("OPENAI_API_KEY")
# if you saved the key under a different environment variable name, you can do something like:
# client = OpenAI(
#   api_key=os.environ.get("CUSTOM_ENV_NAME"),
# )
# openai_api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI()

## Uncomment when trying to create you own assistant

# """Create the assistant"""
# personal_trainer_assistant = client.beta.assistants.create(
#     name="Personal Trainer",
#     instructions="""You are the best personal trainer and nutritionist who knows how to get clients to build lean muscles.
# You've trained high-caliber athletes and movie stars.""",
# model=model
# )

# asistant_id = personal_trainer_assistant.id
# print(asistant_id)

# """Create a thread"""
# thread = client.beta.threads.create(
#     messages=[
#         {
#             "role": "user",
#             "content": "Suggest me a diet plan for future muscle building as a person who gains fat easily."
#         }
#     ]
# )

# thread_id = thread.id
# print(thread_id)

# run = client.beta.threads.runs.create(
#     thread_id=thread_id,
#     assistant_id=asistant_id,
#     # instructions="Please address the user as James Bond",
# )


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """

    Waits for a run to complete and prints the elapsed time.:param client: The OpenAI client object.
    :param thread_id: The ID of the thread.
    :param run_id: The ID of the run.
    :param sleep_interval: Time in seconds to wait between checks.
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                return response
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            return None
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)


def run_helper(config_values):
    try:
        response_list = []

        with open(config_values["message_file"]) as f:
            for message in f:
                message_obj = client.beta.threads.messages.create(
                    thread_id=config_values["thread_id"], role="user", content=message
                )

                run = client.beta.threads.runs.create(
                    assistant_id=config_values["assistant_id"],
                    thread_id=config_values["thread_id"],
                    model=config_values["model"],
                    instructions=config_values["instructions"]
                )

                response = wait_for_run_completion(client=client, thread_id=config_values["thread_id"],\
                                run_id=run.id)
                response_list.append({
                    "User": message,
                    "Assistant": response
                })

        return response_list
    except Exception as e:
        print(e)
        return None

# ## Run the request
if __name__=="__main__":
    response_list = run_helper(config_values)

    if response_list is not None:
        with open(config_values["response_file"], "w") as f:
            for response in response_list:
                for key, value in response.items():
                    f.write("{}: {}".format(key, value))
                    f.write('\n')

                f.write(("="*100))
                f.write('\n')


# # ==== Steps --- Logs ==
# run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run.id)
# print(f"Steps---> {run_steps.data[0]}")



