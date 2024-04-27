## Connect with Mongo DB sample databse

import pymongo
from dotenv import load_dotenv
import os
import requests
from openai import OpenAI

load_dotenv()

## Connect to mongodb database

mongodb_uri = os.getenv("MONGODB_URI")
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
embedding_url = os.getenv("EMBEDDING_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")

os.environ["OPENAI_API_KEY"] = openai_api_key

client = pymongo.MongoClient(mongodb_uri)
db = client.sample_mflix
collection = db.movies

## Generate embeddings

def generate_hf_embedding(text: str) -> list[float]:

  response = requests.post(
    embedding_url,
    headers={"Authorization": f"Bearer {hf_token}"},
    json={"inputs": text})

  if response.status_code != 200:
    raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")

  return response.json()

def generate_openai_embedding(text: str, model: str = "text-embedding-ada-002") -> list[float]:
    openai_client = OpenAI()
    text = text.replace("\n", " ")
    return openai_client.embeddings.create(input = [text], model=model).data[0].embedding

## Create a new field with movie plot embeddings for 50 movies with a plot

# for doc in collection.find({'plot':{"$exists": True}}).limit(50):
#   doc['plot_embedding_hf'] = generate_embedding(doc['plot'])
#   collection.replace_one({'_id': doc['_id']}, doc)


## Query and get the top movies

query = "imaginary characters from outer space at war"

# print((generate_openai_embedding(query)))

results = db.embedded_movies.aggregate([
  {
    "$vectorSearch": {
      "index": "PlotSemanticSearchOpenAI",
      "path": "plot_embedding",
      "queryVector": generate_openai_embedding(query),
      "numCandidates": 100,
      "limit": 4,
    }
  }
])

for document in results:
    print(f'Movie Name: {document["title"]},\nMovie Plot: {document["plot"]}\n')