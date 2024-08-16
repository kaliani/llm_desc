import ast
import json
import os
import re
from typing import Dict, Optional

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain import hub
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_community.document_loaders import WikipediaLoader
from langchain_openai import ChatOpenAI

from models import DataItem

load_dotenv()

# Environment variables setup
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

# Initialize OpenAI and LangChain
llm = ChatOpenAI(model="gpt-4-0125-preview")
prompt_template = os.getenv("PROMPT_TEMPLATE")
prompt = hub.pull(prompt_template)


def get_wiki_info(name: str) -> Optional[str]:
    try:
        docs = WikipediaLoader(query=name, load_max_docs=1).load()
        return docs
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def generate_politician_dossier(name: str, context: str, template: str = prompt.template) -> DataItem:
    parser = PydanticOutputParser(pydantic_object=DataItem)

    prompt = ChatPromptTemplate(
        messages=[HumanMessagePromptTemplate.from_template(template)],
        input_variables=["context", "name"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
        },
    )

    final_rag_chain = prompt | llm
    output = final_rag_chain.invoke({"context": context, "name": name})
    return output


es_url = os.getenv("ELASTICSEARCH_URL")

if es_url is None:
    raise ValueError("ELASTICSEARCH_URL is not set in environment variables")

es = Elasticsearch(es_url)


def search_elasticsearch(index: str, query: Dict) -> Dict:
    response = es.search(index=index, body=query)
    return response


def filter_wikipedia_results(response: Dict) -> Optional[Dict]:
    wikipedia_results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]["meta"]["source"]
        timestamp = hit["_source"]["meta"]["timestamp"]
        if re.search(r"wikipedia\.org", source):
            wikipedia_results.append({"hit": hit, "timestamp": timestamp})

    if wikipedia_results:
        latest_result = max(wikipedia_results, key=lambda x: x["timestamp"])
        return latest_result["hit"]
    else:
        return None


def filter_wikidata_results(response: Dict) -> Optional[str]:
    wikidata_results = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]["meta"]["source"]
        timestamp = hit["_source"]["meta"]["timestamp"]

        if "wikidata.org" in source:
            wikidata_results.append({"hit": hit, "timestamp": timestamp})

    if wikidata_results:
        latest_result = max(wikidata_results, key=lambda x: x["timestamp"])
        picture_source = next(
            (item["data"] for item in latest_result["hit"]["_source"]["data"] if item.get("name") == "image[0].source"),
            None,
        )

        return latest_result, picture_source

    return None


def process_latest_result(latest_result: Optional[Dict]) -> str:
    filtered_data = {}
    if latest_result:
        for item in latest_result["_source"]["data"]:
            if item["data"] and item["name"]:
                filtered_data[item["name"]] = item["data"]
        last_row_text = json.dumps(filtered_data, ensure_ascii=False, indent=2)
        return last_row_text[2:-2]
    return ""


def clean_data(text: str) -> str:
    cleaned_text = re.sub(r"\s+", " ", text)
    cleaned_text = re.sub(r"\\u[0-9A-Fa-f]{4}", "", cleaned_text)
    cleaned_text = re.sub(r"\\xa0", " ", cleaned_text)
    cleaned_text = re.sub(r"\u200b", "", cleaned_text)
    cleaned_text = cleaned_text.strip()
    return cleaned_text


def extract_returning_sources(latest_result: Optional[Dict]) -> str:
    try:
        original_event = latest_result["_source"]["event"]["original"]
        returning_sources = ast.literal_eval(original_event)["meta"]["source"]
    except (KeyError, SyntaxError, ValueError):
        returning_sources = "empty"
    return returning_sources


def process_political_info(data, category):
    results = {}
    base_key = f"{category}["

    for item in data:
        name = item.get("name", "")

        if base_key in name:
            key = int(name.split("[")[-1].split("]")[0])
            if key not in results:
                results[key] = {}

            if name.endswith("]"):
                results[key][category] = item["data"]
            elif ".start time" in name:
                results[key]["start_time"] = item["data"]
            elif ".end time" in name:
                results[key]["end_time"] = item["data"]

    return results


def get_entities(data, category):
    if not data:
        return ""

    last_key = max(data.keys(), key=int)
    return data[last_key].get(category, "")


def get_usernames(data, platform):
    pattern = re.compile(rf"^{platform} username\[\d+\]$")
    usernames = [item["data"] for item in data if pattern.search(item.get("name", ""))]
    return usernames


def enrich_political_person(response):
    position_held = "position held"
    member_pol_parties = "member of political party"
    country_citizenship = "country of citizenship"

    latest_result, picture_source = filter_wikidata_results(response)
    data = latest_result["hit"]["_source"]["data"]

    positions = get_entities(process_political_info(data, position_held), position_held)
    political_parties = get_entities(process_political_info(data, member_pol_parties), member_pol_parties)
    citizenship = get_entities(process_political_info(data, country_citizenship), country_citizenship)
    facebook = get_usernames(data, "Facebook")
    instagram = get_usernames(data, "Instagram")
    twitter = get_usernames(data, "X")

    return picture_source, positions, political_parties, citizenship, facebook, instagram, twitter
