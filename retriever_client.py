import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def get_tool_from_mcp():
    # Define the server parameters
    params = StdioServerParameters(command=sys.executable, args=["retriever_server.py"])

    # Connect to MCP server and open a session
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:

            # Initialize the session
            await session.initialize()

            # Ask the server what tools it provides
            response = await session.list_tools()
            print("Connected to MCP server!")
            print("Available tools:")
            for tool in response.tools:
                print(f"\n{tool.name}:{tool.description}")

            return response.tools
        
async def call_tool_from_mcp(tool_name:str, arguments:dict) -> str:
    # Define server parameters
    params = StdioServerParameters(command=sys.executable, args=["retriever_server.py"])

    # Connect to MCP server and open a session
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:

            # Initialize session
            await session.initialize()

            # Call the tool fetch its output and return it
            result = await session.call_tool(tool_name, arguments)
            content = result.content[0].text
            print(f"Conversation result: {content}")
            return str(content)
        
asyncio.run(get_tool_from_mcp())

# Enter your query as value of "query" key
asyncio.run(
    call_tool_from_mcp(
        "notes_retriever",
        {"query": "What is recipe of burger?",
        "k": 3,}
    )
)