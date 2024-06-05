import os
import subprocess
import threading
import time
import uuid

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from conversation_state_store import *

chat_history = st.empty()
client = RedisClient()


def init_session():
    if 'session_id' not in st.session_state:
        session_id = str(uuid.uuid4())
        st.session_state['session_id'] = session_id
        client.set(session_id, list())
    return st.session_state['session_id']


def clear_session():
    st.session_state.clear()
    return init_session()


def start_heartbeat(session_id):
    def run_heartbeat():
        entrypoints = client.get(ENTRYPOINT)
        if session_id not in entrypoints:
            client.append(ENTRYPOINT, session_id)

        while True:
            chat_log = client.get(session_id)
            chat_history.write(chat_log)
            time.sleep(2)

    thread = threading.Thread(target=run_heartbeat)
    thread.daemon = True
    add_script_run_ctx(thread)
    thread.start()


def extract_text_from_file(uploaded_file):
    if uploaded_file is not None:
        text = uploaded_file.read().decode('utf-8')
        return text
    return ""


def app():
    session_id = init_session()

    if 'heartbeat_started' not in st.session_state:
        start_heartbeat(session_id)
        st.session_state['heartbeat_started'] = True

    st.write(f"Session ID: {session_id}")

    st.title('Product Query Interface')

    st.write("Conversation Log: ")
    if st.button("Refresh"):
        messages = client.get(session_id)
        for message in messages:
            st.write(message)

    uploaded_file = st.file_uploader("Upload a .txt file", type="txt")
    if uploaded_file is not None:
        file_text = extract_text_from_file(uploaded_file)
        client.append(UNPROCESSED_DOCUMENTS, file_text)

    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        client.append(session_id, ('user', query))


if __name__ == '__main__':
    init_session()
    app()

    command = ["streamlit", "run", __file__, f"--server.port={os.getenv('PORT', 5003)}"]
    subprocess.run(command)
