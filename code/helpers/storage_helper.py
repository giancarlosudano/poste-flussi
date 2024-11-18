import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

def get_service_client():
	storage_connection_string : str = os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
	blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
	return blob_service_client

def create_container(container_name : str):
	blob_service_client = get_service_client()
	blob_service_client.create_container(container_name)

def delete_container(container_name : str):
	blob_service_client = get_service_client()
	blob_service_client.delete_container(container_name)

def get_container_list() -> list[str]:
	storage_connection_string : str = os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
	blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
	container_list = blob_service_client.list_containers()
	result = []
	for container in container_list:
		result.append(container.name)
	return result

def get_container_list_with_count() -> list[tuple[str, int]]:
	storage_connection_string : str = os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
	blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
	container_list = blob_service_client.list_containers()
	result = []
	for container in container_list:
		container_client = get_container_client(str(container.name))
		blob_list = container_client.list_blobs()
		result.append([container.name, len(list(blob_list))])
	return result

def get_container_blob_count(container : str) -> int:
	container_client = get_container_client(container)
	blob_list = container_client.list_blobs()
	return len(list(blob_list))

def get_container_client(container : str):
	storage_connection_string : str = os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
	blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
	container_client = blob_service_client.get_container_client(container)
	return container_client

def get_blob_client(container :str, blob_name: str):
	storage_connection_string : str = os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
	blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
	blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
	return blob_client

def get_blob_content(container :str, blob_name : str):
	blob_client = get_blob_client(container, blob_name)
	blob_content = blob_client.download_blob().readall()
	blob_content_decoded = blob_content.decode("utf-8")
	return blob_content_decoded

def get_blob_content_url(container :str, blob_name : str) -> str:

	blob_service_client = get_blob_client(container, blob_name)
	
	# Imposta le opzioni per il SAS
	sas_token = generate_blob_sas(
		account_name= str(blob_service_client.account_name),
		container_name=container,
		blob_name=blob_name,
		account_key=blob_service_client.credential.account_key,
		permission=BlobSasPermissions(read=True),
		expiry=datetime.utcnow() + timedelta(hours=1)  # Il token scade dopo 1 ora
	)

	# Crea l'URL completo con il SAS token
	url_with_sas = f"{blob_service_client.url}?{sas_token}"
	return url_with_sas

def get_blob_list(container : str):
	container_client = get_container_client(container)
	blob_list = container_client.list_blobs()
	return blob_list

def get_connectionstring():
	storage_connection_string : str = os.getenv("AZURE_BLOB_CONNECTION_STRING") or ""
	return storage_connection_string

def recreate_container(container_name : str):
	blob_service_client = get_service_client()
	blob_service_client.delete_container(container_name)
	blob_service_client.create_container(container_name)
	return

