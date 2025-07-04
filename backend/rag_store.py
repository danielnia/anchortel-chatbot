# backend/rag_store.py
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embedding = OpenAIEmbeddings()
vector_db = FAISS.load_local("anchortel_faiss_index", embedding, allow_dangerous_deserialization=True)
retriever = vector_db.as_retriever()
