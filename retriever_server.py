import asyncio
import mcp
from mcp.server.mcpserver import MCPServer
from helpers import build_vector_store, format_docs, DOCX_FILE, PPTX_FILE

# Vector store of notes to avoid building it repeatedly
vector_store = build_vector_store(DOCX_FILE, PPTX_FILE)

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
    retriever = await asyncio.to_thread(vector_store.similarity_search, query, k)

    # Checking if chunks are found and returning value accordingly
    if retriever == []:
        return "No relevant notes found for this query. This knowledge base only covers CN121 course material."
    else:
        result = format_docs(retriever)
        return result

if __name__ == "__main__":
    mcp.run(transport="stdio")