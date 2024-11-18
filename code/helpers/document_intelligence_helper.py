import os
import helpers.storage_helper as storage_helper
from langchain_community.document_loaders.doc_intelligence import AzureAIDocumentIntelligenceLoader
from langchain_core.documents import Document

def load_document(container, blobname: str) -> Document:
    sas_url = storage_helper.get_blob_content_url(container, blobname)
    endpoint = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
    key = os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"] 
    loader = AzureAIDocumentIntelligenceLoader(api_endpoint=endpoint, api_key=key, url_path=sas_url, api_model="prebuilt-layout")
    AzureAIDocumentIntelligenceLoader(api_endpoint=endpoint, api_key=key, url_path=sas_url, api_model="prebuilt-layout")
    documents = loader.load()
    return documents[0]

def load_document_from_file(file_path: str) -> Document:
    endpoint = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
    key = os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"] 
    loader = AzureAIDocumentIntelligenceLoader(api_endpoint=endpoint, api_key=key, file_path=file_path, api_model="prebuilt-layout")
    documents = loader.load()
    return documents[0]