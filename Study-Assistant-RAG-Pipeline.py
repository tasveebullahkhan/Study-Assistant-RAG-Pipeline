# Import libraries
import os
import dotenv
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Loading api key
dotenv.load_dotenv()

# Function to format the retrieved data
def format_docs(docs):
    source = ""
    for doc in docs:
        source += f"\n\n Source: {doc.metadata['source']}\n{doc.page_content}"
    return source

# Fucntion to split documents into chunks
def split_docs(document, chunk_size, chunk_overlap, separators):
    splitter = RecursiveCharacterTextSplitter(
        chunk_overlap = chunk_overlap,
        chunk_size = chunk_size,
        separators= separators
    )
    docs = splitter.split_documents(document)
    print(f"total no of chunks is {len(docs)}")
    return docs

# Loading the docx and pptx files
docx_loader = UnstructuredWordDocumentLoader("CN_Logical_IPv4_IPv6_Notes.docx")
docx_data = docx_loader.load()

# Loading the pptx files
pptx_loader = UnstructuredPowerPointLoader("Hub, Switch and Router.pptx")
pptx_data = pptx_loader.load()

# Split the documents in chunks
docx_docs = split_docs(docx_data, 2000, 200, ["\n\n", "\n", " "])
pptx_docs = split_docs(pptx_data, 1000, 0, ["\n\n", "\n", " ", ""])

# Combing all documents in one list
documents = docx_docs + pptx_docs

# Set up google gemini embedding model to embed the docs
embedding_function = GoogleGenerativeAIEmbeddings(model = "gemini-embedding-001")

# Intitialize an chroma database
persist_dir_path = os.path.join(os.getcwd(), "chromadb")

# Loading existing vectorstore
if os.path.exists(persist_dir_path) and os.listdir(persist_dir_path):
    vector_store = Chroma(
    embedding_function= embedding_function,
    persist_directory= persist_dir_path
)
    print("Database successfully updated locally!")

# First run create and embed
else:
    vector_store = Chroma.from_documents(
        documents,
        embedding = embedding_function,
        persist_directory = persist_dir_path,
    )
    print("Database successfully built locally!")

# Converting users query into embeddings and execute similarity search
retriever = vector_store.as_retriever(
    search_type = "similarity",
    search_kwargs = {"k": 3}
)


# Message string for prompt template
message = """
Answer the following question using the context provided.
Also cite the source document used for its answer.
The name of source must be same as file name used for the answer.
No guessing by the model or creating your own name.

Context:
{context}

Question:
{question}:

Answer:
"""

# Creating prompt to augment into llm from message string
prompt = ChatPromptTemplate.from_messages(
    [("human", message)],
    )


# Intitialzing the llm
llm = GoogleGenerativeAI(model = "gemini-3.1-flash-lite-preview")

# Chaning the retriever, llm and prompt
chain = (
    {"context": retriever | format_docs, "question":RunnablePassthrough()}
    | prompt
    | llm
)

# Invoking the chain to generate responses
response = chain.invoke("How does a router's use of IP addresses relate to logical addressing, and how is that different from how a switch uses MAC addresses?")
print(response)