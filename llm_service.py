import time
from pathlib import Path

from langchain import hub
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.llms import LlamaCpp
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from vector_store import DocumentIndexer
from conversation_state_store import *

redis_client = RedisClient()
vector_store_client = DocumentIndexer()
retriever = vector_store_client.get_retriever()
rag_prompt = hub.pull("rlm/rag-prompt")

current_directory = Path(__file__).parent
file_name = "model/llama-2-7b-chat.Q2_K.gguf"
file_path = current_directory / file_name
llm = LlamaCpp(
    model_path=str(file_path),
    temperature=0.75,
    max_tokens=2000,
    top_p=1,
    verbose=True
)

contextualize_q_system_prompt = """
[INST]
<<SYS>>
Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is.
<</SYS>>
[/INST]"""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("assistant", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("user", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

qa_system_prompt = """
[INST]
<<SYS>>
You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.
<</SYS>>

{context}[/INST]"""
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("assistant", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("user", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

chat_history = []


def run():
    while True:
        # todo: switch to pub-sub for lock-free message retrieval
        # [(role, message), ...]
        conversation_ids = redis_client.get(ENTRYPOINT)

        if not conversation_ids:
            time.sleep(1)
            continue

        conversation_id = conversation_ids.pop(0)
        redis_client.set(ENTRYPOINT, conversation_ids)

        messages = redis_client.get(conversation_id)

        if messages and messages[-1][0] == 'user':
            chat_history = []
            for agent, content in messages:
                chat_history.append(content if agent == 'ai' else HumanMessage(content))

            question = messages[-1][1] + '\n'
            print(f"conversation_id: {conversation_id} | processing...")
            ai_msg = rag_chain.invoke({"input": question, "chat_history": chat_history})
            redis_client.append(conversation_id, ('ai', ai_msg["answer"]))
            print(f"conversation_id: {conversation_id}, message: {ai_msg['answer']}")

        redis_client.append(ENTRYPOINT, conversation_id)


if __name__ == '__main__':
    run()
