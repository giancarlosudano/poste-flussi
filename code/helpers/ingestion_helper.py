import os
import re
import shutil
import streamlit as st
import helpers.azure_search_helper as azure_search_helper
import helpers.utility_helper as utility_helper
import helpers.storage_helper as storage_helper
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import helpers.logger_helper as logger_helper

# Function to load the content of an include file
def load_include_content(includes_dir, filename):
	with open(os.path.join(includes_dir, filename), 'r', encoding='utf-8') as file:
		return file.read().strip()

# Function to replace the INCLUDE tags with the actual content
def replace_includes_in_file(file_path, include_map, include_pattern, st_container):
	with open(file_path, 'r', encoding='utf-8') as file:
		content = file.read()
	
	# Replace all INCLUDE tags with the corresponding content
	def replace_match(match):
		include_file = match.group(1)
		st_container.write("Substituting " + include_file + " inside file " + file_path)
		return include_map.get(include_file, match.group(0))  # Default to the original match if not found
	
	new_content = include_pattern.sub(replace_match, content)
	
	with open(file_path, 'w', encoding='utf-8') as file:
		file.write(new_content)

def upload(container:str, file_path:str, blob_name:str):
	
	# Legge il contenuto del file
	with open(file_path, 'r', encoding='utf-8') as file:
		lines = file.readlines()

	# Trova la fine del blocco YAML iniziale
	end_of_yaml_index = None
	for i, line in enumerate(lines):
		if line.strip() == '---':
			if end_of_yaml_index is None:  # Inizio del blocco YAML
				end_of_yaml_index = i
			else:  # Fine del blocco YAML trovata
				end_of_yaml_index = i  # Aggiorna per inserire prima della fine del blocco
				break

	# Se è stato trovato un blocco YAML, inserisce la riga all'interno di questo blocco
	if end_of_yaml_index is not None:
		lines.insert(end_of_yaml_index, f"rfpcopilot.filepath: {blob_name}\n")
	else:
		lines.insert(0, f"---\nrfpcopilot.filepath: {blob_name}\n---\n")

	# Trasforma le linee modificate in una stringa
	content = ''.join(lines)

	# Carica il contenuto modificato come blob
	blob_client = storage_helper.get_blob_client(container, blob_name)
	blob_client.upload_blob(content, overwrite=True)
	print(f"File {file_path} uploaded")

def explore_and_upload(container : str, folder_path : str):
	# Esplora ricorsivamente la directory e i suoi sottodirectory
	for root, dirs, files in os.walk(folder_path):
		for file in files:
			if file.endswith(".md"):
				file_path = os.path.join(root, file)
				original_path = os.path.relpath(file_path, start=folder_path)
				upload(container, file_path, original_path)

def clean_non_md_files(folder):
	non_md_count = utility_helper.count_non_markdown_files(folder)
	i = 0
	progress_bar = st.progress(0, "Cleaning non .md files")
	# Aggiorna la barra di progresso
	
	# Trova e rimuovi i file non .md
	for dirpath, dirnames, filenames in os.walk(folder):
		for file in filenames:
			if not file.endswith(".md"):
				i += 1
				full_path = os.path.join(dirpath, file)
				os.remove(full_path)
				progress = (i + 1) / non_md_count
				if progress > 1:
					progress = 1
				progress_bar.progress(progress)

	j = 0
	# Trova e rimuovi le cartelle vuote
	for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
		# topdown=False è importante per assicurarsi che le cartelle più interne vengano visitate per prime
		if not dirnames and not filenames:
			j += 1
			shutil.rmtree(dirpath)
	
	st.write(f"Removed {i} non .md files and {j} empty directories")

def remove_local_folders(folder, folders_to_exclude):
	if folders_to_exclude:
		excluded_folders = folders_to_exclude.split(",")
		for folder_to_delete in excluded_folders:
			path_to_delete = os.path.join(folder, folder_to_delete)
			if os.path.exists(path_to_delete):
				shutil.rmtree(path_to_delete)
				st.write(f"Removed {path_to_delete}")
			else:
				st.write(f"Folder {path_to_delete} does not exist")

def replace_includes(folder, include_folder, st_container):
	includes_dir = os.path.join(folder, include_folder)

	# Compile a regex pattern for matching the INCLUDE tags
	include_pattern = re.compile(r'\[!INCLUDE\[[^\]]*\]\((pn[-_]{1}[^)]+\.md)\)\]')

	# Load all include files that start with 'pn-'
	include_files = [f for f in os.listdir(includes_dir) if (f.startswith('pn-') or f.startswith('pn_'))]

	# Create a mapping of include filenames to their content
	include_map = {filename: load_include_content(includes_dir, filename) for filename in include_files}

	# Replace includes in all Markdown files in the current directory and subdirectories
	for dirpath, dirnames, filenames in os.walk(folder):
		for filename in filenames:
			if filename.endswith('.md') and not filename.startswith('pn-'):  # Avoid replacing content in include files themselves
				file_path = os.path.join(dirpath, filename)
				st_container.write("Substituting includes in " + file_path)
				replace_includes_in_file(file_path, include_map, include_pattern, st_container)

	for used_include in list(include_map.keys()):
		os.remove(os.path.join(includes_dir, used_include))

# Check if a doc exists in the index, search by field "source"
def check_parentdoc_exists_in_index(index, source):
	store = azure_search_helper.get_store(index)
	client = store.client
	results = client.search(search_text='*', select=['id'], filter=f"source eq '{source}'", include_total_count=True)
	return results.get_count() > 0

def upload_folder(folder, container, progress_bar, status_text, md_count):
	i = 0
	for dirpath, dirnames, filenames in os.walk(folder):
		for filename in filenames:
			if filename.endswith('.md'):
				i += 1			
				progress = (i + 1) / md_count
				if progress > 1:
					progress = 1
				progress_bar.progress(progress)
	
				file_path = os.path.join(dirpath, filename)
				rel_file_path = os.path.relpath(file_path, start=folder)

				status_text.text(f"{filename} {file_path} {rel_file_path}")
				upload(container, file_path, rel_file_path)

def ingestion_from_blob_storage(container:str, index:str, overwrite: bool, total: int, log_visual):

	logger = logger_helper.get_logger(__name__)

	vector_store = azure_search_helper.get_store(index)
	text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0, length_function=len, is_separator_regex=False)

	container_client = storage_helper.get_container_client(container)
	i = 0
	for blob in container_client.list_blobs():
		try:

			exist = check_parentdoc_exists_in_index(index, blob.name)

			if not exist or overwrite:
				i += 1
				content = storage_helper.get_blob_content(container, blob.name)
				document = Document(content)

				# Estrae informazioni dal front matter per passarli come metadati
				front_matter = ""
				title = ""
				description	= ""
				try:
					front_matter = utility_helper.extract_yaml_front_matter(content)
					title = front_matter.get('title', '')
					description = front_matter.get('description', '')
					filepath = front_matter.get('rfpcopilot.filepath', '')
				except Exception as fm_e:
					log_visual.error(f"Errore: {fm_e}...")

				document.metadata["source"] = blob.name
				document.metadata["title"] = title
				document.metadata["description"] = description
				document.metadata["filepath"] = filepath
				
				docs = text_splitter.split_documents([document])
				
				vector_store.add_documents(documents=docs)

				log = f"({i} of {total}) Blob: {blob.name} Chunked in {len(docs)}."
				logger.info(log)
				log_visual.write(log)
				print(log)
			else:
				log = f"({i} of {total}) Blob: {blob.name} Skipped (Already Embedded)."
				logger.info(log)
				log_visual.write(log)
				print(log)

		except Exception as e:
			logger.exception(e)
			log_visual.error(e)