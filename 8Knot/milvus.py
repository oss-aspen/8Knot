from pymilvus import MilvusClient
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv("env.list")

client = MilvusClient("8Knot/milvus_demo.db")

# Load graphs.json
with open("8knot/graphs.json", "r") as f:
    graphs = json.load(f)

def calculate_embedding(text: str) -> list:
    """
    Calculate the embedding for a given text using the Nomic API.
    """

    url = f"{os.getenv('NOMIC_URL')}"

    headers = {"Authorization": f"Bearer {os.getenv('NOMIC_API_KEY')}"}

    payload = {
        "encoding_format" : "float",
        "input": text,
        "model": "/mnt/models/",
        "user" : "null"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        raise Exception(f"Error calculating embedding: {response.text}")
    
# Create a vector database collection
client.create_collection(
    collection_name="demo_collection",
    dimension=768,  # The vectors we will use in this demo has 768 dimensions
)

i = 0
for graph in graphs:
    print(f"Processing graph {i+1}/{len(graphs)}: {graph['name']}")
    embedding = calculate_embedding(graph["name"] + graph["about"])
    
    # Create an entity with the graph name and its embedding
    entity = {
        "id": i,
        "vector": embedding,
        "title": graph['name'],
        "about": graph['about'],
        "identifier" : graph['id'],
    }
    
    # Insert the entity into the collection
    client.upsert(collection_name="demo_collection", data=[entity])
    i += 1