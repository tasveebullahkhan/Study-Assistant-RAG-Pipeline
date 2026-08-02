# Import Libraries
import os
import dotenv
from helpers import build_retriever, DOCX_FILE, PPTX_FILE, format_docs
from crewai import Agent, Task, Crew, LLM, Process
from crewai.tools import tool

# Load api keys
dotenv.load_dotenv()

# Build the retriever once 
retriever = build_retriever(DOCX_FILE, PPTX_FILE, k=3)

# Wrap the search course notes function under the tool
@tool("CN course search tool")
def search_course_notes(question: str) -> str:
    """ Since agents take input and output as a string we are trying 
    to use retriever in way that can take input and output as string."""

    # Getting the final output of the retriever
    docs = retriever.invoke(f"Answer the question: {question}")

    # retrurning that output into string
    return format_docs(docs)

# An llm that will generate responses 
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.environ["GROQ_API_KEY"]
)

# Agent that will answer our queries
course_agent = Agent(
    role="Teaching Expert Specializing in Computer Networks",
    goal="Craft a clear answer of the asked question along with citing the source. Keeping in mind that only the answer to question is mentioned in the answer nothing else.",
    backstory=""" You have 15 years of experience in Teaching computer 
    networks. First check your notes first if answer is present there than
    use that as a source. If it is not present there than cite other sources.
    Always cite sources at the last.""",
    llm=llm,
    tools=[search_course_notes]
)

# Task that is needed to be done
course_task = Task(
    description="Answer accurately according to this asked question regarding computer networks: {question}",
    expected_output=
    """Answer in two clearly labeled parts:
    1. 'From your course notes:' — only include information actually 
        retrieved from the search tool, cited by the specific document name.
    2. 'General knowledge (not in your course notes):' — anything else, 
        with a note that this wasn't verified against your course material.
    3. 'Source Citation:' After answering cite sources from where that part is cited after that answer another part and cite source of another part.
    If the tool returns no relevant results, state that clearly instead 
of guessing.""",
    agent=course_agent
)

# Wrapping task and agents together
course_crew = Crew(
    tasks=[course_task],
    agents=[course_agent],
    process=Process.sequential
)

# Getting the agents output and printing it
result = course_crew.kickoff(inputs={"question": "How does routing work on the internet?"})
print(result.raw)