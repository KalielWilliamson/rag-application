import os
import subprocess
import threading
import time
import uuid

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from conversation_state_store import RedisClient

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
        entrypoints = client.get('entrypoint')
        if session_id not in entrypoints:
            client.append('entrypoint', session_id)

        while True:
            chat_log = client.get(session_id)
            chat_history.write(chat_log)
            time.sleep(2)

    thread = threading.Thread(target=run_heartbeat)
    thread.daemon = True
    add_script_run_ctx(thread)
    thread.start()


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

    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        client.append(session_id, ('user', query))
        time.sleep(1)
        st.write("Updated Conversation Log:")
        messages = client.get(session_id)
        for message in messages:
            st.write(message)


if __name__ == '__main__':
    # Check if the Streamlit server is already running to avoid starting multiple instances
    # client.clear()
    # client.set('entrypoint', [])

    init_session()
    app()

    command = ["streamlit", "run", __file__, f"--server.port={os.getenv('PORT', 5003)}"]
    subprocess.run(command)
