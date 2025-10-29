import os
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chat_models import init_chat_model
from typing import Optional

from backend.Prompt_template import prompt

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash", api_key=google_api_key)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


def create_vectorstore(docs, persist_directory: str):
    """
    Create or load a chroma vectorstore at persist_directory.
    Idempotent: won't duplicate if already exists (Chroma handles persistence).
    """
    os.makedirs(persist_directory, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    texts = splitter.split_documents(docs)
    vectordb = Chroma.from_documents(texts, embedding=embeddings, persist_directory=persist_directory)
    vectordb.persist()
    return vectordb


def load_vectorstore_if_exists(persist_directory: str) -> Optional[Chroma]:
    if os.path.exists(persist_directory):
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return None


def get_conversational_chain(vectordb):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
    )
    return qa_chain
