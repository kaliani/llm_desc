import json
from datetime import datetime
from models import MetadataItem, PoliticanDocs
from utils import (
    clean_data,
    extract_returning_sources,
    filter_wikipedia_results,
    generate_politician_dossier,
    process_latest_result,
    search_elasticsearch,
    enrich_political_person,
)
from elastic import validate_document  # index_document


def get_context_and_sources(wikidataid: str, max_tokens: int = 29000):
    es_query_raw = {"query": {"match": {"meta.id": wikidataid}}}

    response_raw = search_elasticsearch(index="eye-raw-data", query=es_query_raw)

    latest_result_raw = filter_wikipedia_results(response_raw)
    if latest_result_raw:
        context = process_latest_result(latest_result_raw)
        context = clean_data(context)[:max_tokens]
        returning_sources = extract_returning_sources(latest_result_raw)

        (
            picture_source,
            positions,
            political_parties,
            citizenship,
            facebook,
            instagram,
            twitter,
        ) = enrich_political_person(response_raw)
    else:
        context = ""
        returning_sources = "empty"
        picture_source = None
        positions = None
        political_parties = None
        citizenship = None
        facebook = []
        instagram = []
        twitter = []

    return (
        context,
        returning_sources,
        picture_source,
        positions,
        political_parties,
        citizenship,
        facebook,
        instagram,
        twitter,
    )


def create_politician_json(name: str, wikidataid: str, template):
    (
        context,
        returning_sources,
        picture_source,
        positions,
        political_parties,
        citizenship,
        facebook,
        instagram,
        twitter,
    ) = get_context_and_sources(wikidataid)

    output = generate_politician_dossier(name, context, template)
    main_info = json.loads(output.content[8:-3])
    main_info["ReturningSources"] = returning_sources
    main_info["PictureSource"] = picture_source
    main_info["Position"] = positions
    main_info["Citizenship"] = citizenship
    main_info["PoliticalParty"] = political_parties
    main_info["Facebook"] = facebook
    main_info["Instagram"] = instagram
    main_info["Twitter"] = twitter

    record_id, created_at = get_record_id_and_creation_time(wikidataid)

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    metadata_item = MetadataItem(sub_question="", answer="")

    politician_docs = PoliticanDocs(
        id=record_id or wikidataid[1:],
        wikidataid=wikidataid,
        title=name,
        type=1,
        data=main_info,
        metadata=[metadata_item],
        createdAt=created_at,
        updatedAt=updated_at,
    )

    document_dict = politician_docs.model_dump()

    validated_document = validate_document(document_dict)
    if not validated_document:
        return None

    return document_dict
    # response = index_document(index="eye-clean-data", id=record_id, document=document_dict)
    # if response:
    #     return f"LLM Processing complete for Wikidata ID: {wikidataid}"
    # else:
    #     return None


def get_record_id_and_creation_time(wikidataid: str):
    es_query_clean = {"query": {"match": {"wikidataid": wikidataid}}}

    response_clean = search_elasticsearch(index="eye-clean-data", query=es_query_clean)
    hits = response_clean.get("hits", {}).get("hits", [])

    if hits:
        existing_record = hits[0]["_source"]
        record_id = hits[0]["_id"]
        created_at = existing_record["createdAt"]
    else:
        record_id = None
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return record_id, created_at
