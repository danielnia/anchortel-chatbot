from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load your Anchortel text rom file or string
with open("./anchortel_info.txt", "r") as f:
    raw_text = f.read()

# Split the text into manageable chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.create_documents([raw_text])


embeddings = OpenAIEmbeddings()
vector_db = FAISS.from_documents(docs, embeddings)

# Save index locally
vector_db.save_local("backend/anchortel_faiss_index")
