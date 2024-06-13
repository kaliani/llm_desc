import os
from pydantic import ValidationError
from elasticsearch import Elasticsearch
from models import PoliticanDocs

es = Elasticsearch(os.getenv("ELASTICSEARCH_URL"))

def validate_document(document: dict):
    try:
        validated_document = PoliticanDocs(**document)
        return validated_document
    
    except ValidationError as e:
        print(f"Validation Error: {e.json()}")
        return None

def index_document(index: str, id: str, document: dict):
    try:
        if id:
            response = es.index(index=index, id=id, document=document)
        else:
            response = es.index(index=index, document=document)
        return response

    except Exception as e:
        print(f"Error indexing document: {e}")
        return None
