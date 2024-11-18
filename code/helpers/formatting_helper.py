
# funzione per formattare una lista di messaggi (role e content) in un'unica stringa
def format_all_messages(messages):
	# Creazione di una lista vuota per contenere i messaggi formattati
	messages_formatted = []

	# Iterazione attraverso i messaggi nella lista
	for message in messages:
		# Aggiunta del messaggio formattato alla lista
		messages_formatted.append(f"{message['role']}: {message['content']}")

	# Unione di tutti i messaggi formattati in una singola stringa, separandoli con un newline per chiarezza
	return "\n\n".join(messages_formatted)


def format_user_messages(messages):
	# Creazione di una lista vuota per contenere i messaggi formattati
	messages_formatted = []

	# Iterazione attraverso i messaggi nella lista
	for message in messages:
		if message['role'] == 'user':
			messages_formatted.append(f"{message['role']}: {message['content']}")

	# Unione di tutti i messaggi formattati in una singola stringa, separandoli con un newline per chiarezza
	return "\n\n".join(messages_formatted)

def format_chunks(docs):
	return "\n\n".join(doc.page_content for doc in docs)

def format_fewshot(docs):
	return "\n\n".join(doc.page_content for doc in docs)

def format_parents(parents):
	elementi_formattati = []

	# Iterazione attraverso le coppie chiave-valore nel dizionario
	for chiave, valore in parents.items():
		# Aggiunta della stringa formattata alla lista
		elementi_formattati.append(f"file: {chiave}\n{valore}")

	# Unione di tutte le stringhe formattate in una singola stringa, separandole con due newline per chiarità
	stringa_unica = "\n\n".join(elementi_formattati)
	return stringa_unica

def format_strings(strings):
	return "\n\n".join(strings)

def print_chain_summary(title, relevant_chunks, parents, fewshots, generation):
	print("Metodo: " + title)
	print("Chunk rilevati:" + str(len(relevant_chunks)))
	print('\n'.join([chunk.metadata["source"] for chunk in relevant_chunks]))
	print("Parent rilevati:" + str(len(parents)))
	print('\n'.join(parents.keys()))
	# print("Fewshots:" + str(len(fewshots)))
	print("Generation:")
	print(generation)
