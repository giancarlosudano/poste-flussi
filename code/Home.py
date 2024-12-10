import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit_authenticator as stauth
import traceback
from dotenv import load_dotenv

try:
	load_dotenv()
	
	st.set_page_config(page_title="Poste KB Multimodal", page_icon=os.path.join('images','favicon.ico'), layout="wide", menu_items=None)
	st.title("Poste KB Multimodal")
	st.sidebar.image(os.path.join('images','logo-poste.png'), use_column_width=True)
	st.sidebar.write("Version 0.1.1")
	
	st.markdown("""Benvenuti nel prototipo dell'applicazione sviluppata per Poste Italiane. Desideriamo informarvi che tutti i dati inseriti in questa applicazione transitano attraverso un datacenter situato in Azure East US. Garantiamo che i dati sono crittografati durante il transito per assicurare la massima protezione e sicurezza delle informazioni.
Inoltre, vogliamo sottolineare che i dati forniti non vengono utilizzati per il training di versioni successive dei modelli OpenAI. Tutte le interazioni con l'applicazione sono mantenute esclusivamente per scopi di debugging e miglioramento del servizio, nel rispetto della vostra privacy.
La tutela della vostra privacy e la sicurezza delle vostre informazioni sono per noi di fondamentale importanza""")
	
	import yaml
	from yaml.loader import SafeLoader

	with open('config.yaml') as file:
		config = yaml.load(file, Loader=SafeLoader)

	authenticator = stauth.Authenticate(
		config['credentials'],
		config['cookie']['name'],
		config['cookie']['key'],
		config['cookie']['expiry_days']
	)
	authenticator.logout(location='sidebar')
	authenticator.login(location='main')
	
	if st.session_state['authentication_status']:
		st.write(f'Welcome, you are logged in as {st.session_state["username"]}!')

except Exception:
	st.error(traceback.format_exc())