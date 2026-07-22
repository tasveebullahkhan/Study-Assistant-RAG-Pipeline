# Import libraries
from helpers import build_retriever, format_docs, DOCX_FILE, PPTX_FILE
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

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
retriever = build_retriever(DOCX_FILE, PPTX_FILE, 3)
chain = (
    {"context": retriever | format_docs, "question":RunnablePassthrough()}
    | prompt
    | llm
)

# Invoking the chain to generate responses
response = chain.invoke(input("Ask a Question: "))
print(response)