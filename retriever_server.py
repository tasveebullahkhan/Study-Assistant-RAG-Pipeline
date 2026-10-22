import asyncio
import mcp
import os
from mcp.server.mcpserver import MCPServer
from helpers import format_docs, PERSIST_DIR_PATH
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Initializing embedding function and persist chroma directory
embedding_function = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")


# Opening the existing vector store
vector_store = Chroma(
        embedding_function= embedding_function,
        persist_directory = PERSIST_DIR_PATH
    )

# Instantiating mcp server
mcp = MCPServer("Notes Retriever")

# Tool that will retrieve k number of chunks according to clients needs
@mcp.tool()
async def notes_retriever(query:str, k: int = 3):
    """ Retrieves k chunks on the basis of similarity provided that the 
    asked query is related to CN121 course notes and not something which
    is unrelated to these course notes.

    Args:
        query: The question or query string regarding which the user want chunks
        k: The integer number of chunks that user wants.

    Returns:
        If matches are found return string containing chunks + citation.
        If no matches are found return this string "No relevant notes found for this query. This knowledge base only covers CN121 course material."
    """

    # Retriver controlling "k" requests based on clients needs
    retriever = await asyncio.to_thread(vector_store.similarity_search_with_relevance_scores, query, k)

    # Checking if chunks are found and returning value accordingly
    if retriever == [] or retriever[0][1] < 0.5:
        return "No relevant notes found for this query. This knowledge base only covers CN121 course material."
    else:
        docs = [doc for doc, score in retriever]
        result = format_docs(docs)
        return result

if __name__ == "__main__":
    mcp.run(transport="stdio")