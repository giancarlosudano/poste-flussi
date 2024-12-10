import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import traceback
from dotenv import load_dotenv
import helpers.langchain_helper as lc_hlp
from langchain_core.prompts import ChatPromptTemplate
import base64


system_message = """Sei un assistente di Poste Italiane, che aiuta un'operatore call center a fare le domande corrette sul malfunzionamento del servizio PMCASA mediante l'uso di diagrammi e documenti che ti verranno forniti.
- Percorri le domande del diagramma a partire dalla domanda successiva allo step 0 "Guasto apparecchio".
- Le domande sono contrassegnate dai rombi e hanno come possibilie risposta Si o No.  
- Proponi le domande step by step e aspetta la risposta dell'utente.
- Quando l'utente risponde si o no devi percorrere il diagramma seguendo le frecce con l'etichetta corretta "Si" o "No".
- Quando attraversi il diagramma devi fornire informazioni addizionali fornite in contesto per ogni rettangolo usando l'ID corrispondente.
- Devi guidare l'operatore del call center nel percorso del diagramma e devi fornire informazioni addizionali ove possibile.
- Le tue indicazioni devono essere prese solamente dai documenti forniti.
- Le tue domande devono essere solo quelle del diagramma fornito.
- Ragiona step by step, descrivi la porzione di diagramma rilevante per la risposta e scrivi il motivo tra parentesi."""

flusso1_text = """ID (start)
Attività: GUASTO APPARECCHIO 
Descrizione:
Il cliente chiama per un problema sul telefono di PM casa (biancone)

ID 1 
Attività: VERIFICA STATO LINEA
Descrizione:
L'operatore verifica lo stato della linea:
- Entra nel tab Stato linea Fissa
- Ricerca il numero da verificare
N.B.
Per il corretto funzionamento della linea lo stato del
terminale deve essere in stato Consegnato

ID 2
Attività: CHIUSURA CONTATTO
Descrizione: 
L’operatore comunica al cliente che il telefono funziona solo
se utilizzato all’indirizzo di installazione. Questo dovrà
essere spostato all’indirizzo presente sul contratto o sarà
necessario richiedere un cambio di indirizzo (rif. 03
Istruzione - GESTIONE CAMBIO INDIRIZZO PM
CASA_TRASLOCO). L’operatore procede con la chiusura
del contatto e traccia l’esito con la seguente interazione:
Tipo Area Subarea
ASSISTENZA
FISSO
TECNICA TS – RISOLUZIONE IN
LINEA

ID 3 
Attività: SPEGNERE E RIACCENDERE IL TELEFONO
Descrizione: 
Nel caso il cliente lamenti un malfunzionamento del
telefono e sia presente sul display un messaggio di errore
relativo alla SIM (SIM non attiva, SIM non registrata) e sul
CRM la linea risulta ATTIVA, è necessario richiedere al
cliente di spegnere e riaccendere il telefono secondo la
procedura riportata di seguito, e quindi verificare
nuovamente il messaggio sul display e il corretto
funzionamento del telefono.

ID 4 
Attività: CHIUSURA CONTATTO 
Descrizione: L’operatore procede con la chiusura del contatto e traccia
l’esito con la seguente interazione
Tipo Area Subarea
ASSISTENZA
FISSO
TECNICA TS – RISOLUZIONE IN
LINEA

ID 5 
Attività: MVNE 
Descrizione: L’operatore assegna la seguente sr a MVNE
Tipo Area Subarea
ASSISTENZA
FISSO
TECNICA TS-SIM NON REGISTRATA
Inserendo nella descrizione le seguenti informazioni:
- Numero Fisso e Numero Mobile
- Indirizzo completo (Comune, Via e Nr. Civico)
- Da quanto tempo il Cliente riscontra il problema
Esito prove di TS eseguito (verifica indirizzo, stato sim
attivo, spento e riacceso telefono)
-
- Problema riscontrato

ID 6
Attività: CHIUSURA CONTATTO 
Descrizione: Non si tratta di un problema tecnico, l’operatore verifica il
motivo della sospensione che può essere dovuto a
Morosità, Frode o altri motivi.
L’operatore comunica al Cliente il motivo del
blocco delle chiamate in uscita e chiude il
contatto tracciando la seguente interazione,
indicando quanto riscontrato:
Tipo Area Subarea
ASSISTENZA
FISSO
TECNICA TS – RISOLUZIONE IN
LINEA

ID 7 
Attività: VERIFICARE INSTALLAZIONE TELEFONO
Descrizione: 
L'operatore invita il cliente a verificare il corretto
collegamento dei cavi:
- Alimentatore
- Presa tripolare (se collegata)
- Presa telefonica con cavo
- Attacco dei cavi al telefono

ID 8 
Attività: SOSTITUZIONE TELEFONO 
Descrizione: 
L'operatore informa il Cliente della necessità di
sostituire il telefono ed inserisce l’ordine di
sostituzione del terminale (Rif. GUIDA CRM - PM CASA- INSERIMENTO ORDINE POSTVENDITA) provvedendo
a tracciare l’esito con la seguente interazione:

| Tipo | Area | Subarea |
| ASSISTENZA FISSO | TECNICA SOSTITUZIONE | NON SI ACCENDE |
| ASSISTENZA FISSO | TECNICA SOSTITUZIONE | PROBLEMI AUDIO |

L’operatore dovrà inserire l’IMEI del telefono da
sostituire nelle note dell’interazione.
N.B.

Informare il Cliente che alla consegna del nuovo telefono
dovrà restituire quello vecchio e che il corriere non
effettuerà l’installazione. In caso fosse necessaria
assistenza nell’installazione dovrà ricontattarci per
richiedere appuntamento con tecnico.
ATTENZIONE:
In caso di malfunzionamento telefono, se, dopo gli
opportuni troubleshooting, si accerta telefono guasto,
l'ordine di sostituzione potrà essere inserito anche se
l’operatore non parla direttamente con l'intestatario della
linea ma con familiare

ID 9
Attività: SPEGNERE PER 6 ORE IL TELEFONO
Descrizione: L’operatore procede con la chiusura del contatto e traccia
l’esito con la seguente interazione:
| Tipo | Area | Subarea |
| ASSISTENZA FISSO |TECNICA | TS SPEGNERE 6 ORE |

ID 10
Attività: ALZARE VOLUME IN CHIAMATA 
Descrizione: L'operatore guida il cliente nella verifica dei toni impostati del telefono.
Durante la chiamata invitare il cliente a premere la freccia
destra del tasto al centro per alzare il volume in conversazione.
N.B : La modifica dei toni e del volume della suoneria
in caso di Gnp in corso non viene recepita se la
chiamata viene ricevuta sul numero da portare. La
modifica sarà attiva solo a Gnp completa

ID 11 
Attività: REGOLARE VOLUME SUONERIA
Descrizione: L’operatore guida il cliente nella regolazione del volume della suoneria.
N.B.
La modifica dei toni e del volume della suoneria in caso
di GNP in corso non viene recepita se la chiamata viene
ricevuta sul numero da portare. La modifica sarà attiva
solo a GNP completa

ID 12
Attività: RESET TELEFONO
Descrizione: L’operatore invita il cliente ad eseguire il ripristino delle
impostazioni iniziali del telefono:
- Entra nel menu “impostazioni”
- Seleziona la voce “Ripristino impostazioni iniziali”
- Inserisci la password “1234”
- Premere ok (tasto in alto a sinistra)
- " Imposta e Riavvia? "
- Premere Si

ID 13 
Attività: CHIUSURA CONTATTO 
Descrizione: L’operatore procede con la chiusura del contatto e traccia
l’esito con la seguente interazione:
| Tipo | Area | Subarea |
|ASSISTENZA FISSO | TECNICA | RESET TELEFONO |

ID 14 
Attività: VERIFICARE QUALI SONO I PROBLEMI RISCONTRATI
Descrizione:
Verificare con il cliente che tipo di problema riscontra:
- Telefoni collegati
- Fare chiamate
- Ricevere chiamate"""


def prepare_messages(system_message, image_data, question_expanded):
	# system
    messages = [("system", system_message)]

	# message history
    for msg in st.session_state.messages:
        messages.append((msg["role"], msg["content"]))

	# last message + context + image
    messages.append(("user", [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}, 
                        {"type": "text", "text": question_expanded}]))
    return messages

try:
	load_dotenv()
	st.set_page_config(page_title="Call Center Assistant", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)
	st.title("Call Center Assistant")
	st.sidebar.image(os.path.join('images','flusso01.jpg'), use_column_width=True)

	if st.sidebar.button("Nuova chat"):
		st.session_state.messages = []
		st.rerun()

	llm = lc_hlp.get_gpt(streaming=False, temperature=0.0)

	with open(os.path.join('images', 'flusso01.jpg'), "rb") as image_file:
		image_data = base64.b64encode(image_file.read()).decode("utf-8")

	if "messages" not in st.session_state:
		st.session_state.messages = []

	for message in st.session_state.messages:
		if message["role"] == "assistant":
			with st.chat_message(message["role"], avatar=os.path.join('images','pt-avatar.png')):
				st.markdown(message["content"])
		else:
			with st.chat_message(message["role"]):
				st.markdown(message["content"])

	if question := st.chat_input("Chiedi informazioni al bot", key="chat_input"):
		
		with st.chat_message("user"):
			st.markdown(question)

		with st.spinner("elaborazione risposta..."):

			question_expanded = "Informazioni addizionali:" + flusso1_text + "\n" + question
			messages = prepare_messages(system_message, image_data, question_expanded)

			prompt = ChatPromptTemplate.from_messages(messages)
			chain = prompt | llm
			response = chain.invoke({"image_data": image_data})

			with st.chat_message("assistant", avatar=os.path.join('images','pt-avatar.png')):
				st.markdown(response.content)
			
			st.session_state.messages.append({"role": "user", "content": question})
			st.session_state.messages.append({"role": "assistant", "content": response.content})

except Exception:
	st.error(traceback.format_exc())