import os
from langchain_community.vectorstores.azuresearch import AzureSearch
import helpers.langchain_helper as langchain_helper
import helpers.storage_helper as storage_helper
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (SearchIndex, SearchableField, SearchField, SearchFieldDataType, SimpleField, VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration)
from azure.search.documents import SearchClient

def get_metadata_from_docs(chunks, field = "source") -> list[str]:
	urls = [chunk.metadata[field] for chunk in chunks]
	return urls

def get_parentdoc_from_chunks(relevant_chunks, field = "source", container_name = "") -> tuple[list[str], dict[str, str]]:
	parents = {}
	source_urls = [chunk.metadata[field] for chunk in relevant_chunks]
	for source_url in source_urls:
			content = storage_helper.get_blob_content(container_name, source_url)
			if source_url not in parents:
				parents[source_url] = content
	return source_urls, parents

def get_store(index_name: str):

	embedding_function = langchain_helper.get_embedding().embed_query

	fields = [
		SimpleField(
			name="id",
			type=SearchFieldDataType.String, key=True, filterable=True,
		),
		SearchableField(
			name="content",
			type=SearchFieldDataType.String,
			searchable=True,
		),
		SearchField(
			name="content_vector",
			type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
			searchable=True,
			vector_search_dimensions=len(embedding_function("Text")),
			vector_search_profile_name="my-vector-config",
		),
		SearchableField(
			name="metadata",
			type=SearchFieldDataType.String, searchable=True,
		),
		SearchableField(
			name="title",
			type=SearchFieldDataType.String, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="source",
			type=SearchFieldDataType.String, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="chunk",
			type=SearchFieldDataType.Int32, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="offset",
			type=SearchFieldDataType.Int32, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="description", type=SearchFieldDataType.String, searchable=True
		)
	]

	azure_search_service : str = os.getenv("AZURE_SEARCH_SERVICE") or ""
	azure_search_key : str = os.getenv("AZURE_SEARCH_KEY") or ""

	vector_store: AzureSearch = AzureSearch(azure_search_endpoint=azure_search_service, 
										azure_search_key=azure_search_key, 
										index_name=index_name,
										embedding_function=embedding_function,
										fields=fields)
	return vector_store

def get_index_list_with_totals() -> list[list]:
	credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
	search_client = SearchIndexClient(os.environ["AZURE_SEARCH_SERVICE"], credential)

	result = []
	indexes = search_client.list_indexes()
	for index in indexes:

		index_client = SearchClient(endpoint=os.environ["AZURE_SEARCH_SERVICE"], index_name=index.name, credential=credential)

		# Esegue una query di conteggio sui documenti
		results = index_client.search(search_text="*", select=[], include_total_count=True)

		# Stampare il conteggio totale dei documenti
		total_documents = results.get_count()

		result.append([index.name, total_documents])
	return result

def get_index_total(index_name: str) -> int:
	credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
	index_client = SearchClient(endpoint=os.environ["AZURE_SEARCH_SERVICE"], index_name=index_name, credential=credential)
	results = index_client.search(search_text="*", select=[], include_total_count=True)
	total_documents = results.get_count()
	return total_documents

def get_index_list() -> list[str]:
	credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
	search_client = SearchIndexClient(os.environ["AZURE_SEARCH_SERVICE"], credential)

	result = []
	indexes = search_client.list_indexes()
	for index in indexes:
		result.append(index.name)
	return result

def get_index_fields(index_name : str) -> list[dict]:
	credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
	search_client = SearchIndexClient(os.environ["AZURE_SEARCH_SERVICE"], credential)

	index = search_client.get_index(index_name)
	
	fields_properties = []
	
	for field in index.fields:
		field_info = {
			"name": field.name,
			"type": field.type,
			"searchable": field.searchable,
			"filterable": field.filterable,
			"facetable": field.facetable
		}
		fields_properties.append(field_info)
	
	return fields_properties

def create_index(index_name: str):
	credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
	index_client = SearchIndexClient(os.environ["AZURE_SEARCH_SERVICE"], credential)

	embeddings = langchain_helper.get_embedding()
	embedding_function = embeddings.embed_query

	fields = [
		SimpleField(
			name="id",
			type=SearchFieldDataType.String, key=True, filterable=True,
		),
		SearchableField(
			name="content",
			type=SearchFieldDataType.String,
			searchable=True,
		),
		SearchField(
			name="content_vector",
			type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
			searchable=True,
			vector_search_dimensions=len(embedding_function("Text")),
			vector_search_profile_name="my-vector-config",
		),
		SearchableField(
			name="metadata",
			type=SearchFieldDataType.String, searchable=True,
		),
		SearchableField(
			name="title",
			type=SearchFieldDataType.String, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="source",
			type=SearchFieldDataType.String, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="chunk",
			type=SearchFieldDataType.Int32, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="offset",
			type=SearchFieldDataType.Int32, searchable=True, facetable=True, filterable=True,
		),
		SearchableField(
			name="description", type=SearchFieldDataType.String, searchable=True
		)
	]

	vector_search = VectorSearch(
			profiles=[VectorSearchProfile(name="my-vector-config", algorithm_configuration_name="my-algorithms-config")],
			algorithms=[HnswAlgorithmConfiguration(name="my-algorithms-config")],
	)

	index_definition = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
	index_client.create_index(index_definition)

def delete_index(index_name: str):
	credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
	index_client = SearchIndexClient(os.environ["AZURE_SEARCH_SERVICE"], credential)
	index_client.delete_index(index_name)

def search_by_query(selected_index_name: str, keyword: str, filter: str):
	store = get_store(selected_index_name)
	client = store.client
	results = client.search(search_text=keyword, filter=filter, include_total_count=False)
	return results