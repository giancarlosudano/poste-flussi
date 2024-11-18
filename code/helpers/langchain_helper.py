import os
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import helpers.formatting_helper as fmt_hlp

def get_gpt(streaming : bool = False, temperature : float = 0.0):
	azure_endpoint: str = os.getenv("AZURE_OPENAI_BASE") or ""
	api_key = os.getenv("AZURE_OPENAI_API_KEY") or ""
	api_version: str = os.getenv("AZURE_OPENAI_API_VERSION") or ""
	azure_openai_deployment : str = os.getenv("AZURE_OPENAI_MODEL") or ""
	llm = AzureChatOpenAI(azure_deployment=azure_openai_deployment, temperature=temperature, streaming=False, azure_endpoint=azure_endpoint, api_key=api_key, api_version=api_version)
	return llm

def get_embedding():
	azure_endpoint: str = os.getenv("AZURE_OPENAI_BASE") or ""
	api_key = os.getenv("AZURE_OPENAI_API_KEY") or ""
	azure_embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL") or ""
	embeddings = AzureOpenAIEmbeddings(azure_endpoint=azure_endpoint, api_key=api_key, azure_deployment=azure_embedding_deployment)
	return embeddings

def summarize_text(content: str) -> str:
	from langchain_core.output_parsers import StrOutputParser
	from langchain.prompts import PromptTemplate
	llm = get_gpt()
	prompt_template = """Dato il seguente documento delimitato da `````, produci un riassunto dettagliato del contenuto in 30 righe
Non aggiungere commenti oltre al riassunto stesso

Documento:
`````
{documento}
`````

Riassunto:
"""
	prompt = PromptTemplate(template=prompt_template, input_variables=["documento"])
	chain = prompt | llm | StrOutputParser()
	summary = chain.invoke({"documento": content})
	return summary

def rephrase_question_plus_messages(history, prompt_rephrase) -> str:

	llm = get_gpt()

	history_text = fmt_hlp.format_all_messages(history)

	input_variables = ["history"]
	prompt_template = PromptTemplate(template=prompt_rephrase, input_variables=input_variables)
	chain = prompt_template | llm | StrOutputParser()

	generation = chain.invoke({"history": history_text})
	return generation