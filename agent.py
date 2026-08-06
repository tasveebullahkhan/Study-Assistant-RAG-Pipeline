# Import Libraries
import os
import dotenv
from helpers import build_retriever, DOCX_FILE, PPTX_FILE, format_docs
from crewai import Agent, Task, Crew, LLM, Process
from crewai.tools import tool

# Load api keys
dotenv.load_dotenv()

# Build the retriever once 
retriever = build_retriever(DOCX_FILE, PPTX_FILE, k=2)

# Wrap the search course notes function under the tool
@tool("CN course search tool")
def search_course_notes(question: str) -> str:
    """Searches and retrieves relevant text passages from the Computer
    Networks course notes (DOCX and PPTX files) based on a search query
    or question. When using the CN course search tool, convert any
    pronoun or follow-up references (like 'it', 'its successor', 'that protocol')
    into explicit search queries before calling the search tool."""

    # Getting the final output of the retriever
    docs = retriever.invoke(f"{question}")

    # retrurning that output into string
    return format_docs(docs)

# To store memory of the previous conversations
conversation_history = []
def ask(question: str) -> str:
    # Checking if there is acutally previous conversation
    if conversation_history:
        history_text = "\n".join(conversation_history)
    else:
        history_text = "No previous conversations"

    # Getting the output and history of the conversation
    result = course_crew.kickoff(inputs={
        "question":question,
        "history_text":history_text
    })

    # Add this conversation to the history
    conversation_history.append(f"Question: {question}\n Answer: {result.raw}")
    return result.raw

# An llm that will generate responses 
llm = LLM(
    model="mistral/mistral-small-latest",
    temperature=0,
    api_key=os.environ["MISTRAL_API_KEY"],
    max_tokens=800
)

# Agent that will answer our queries
course_agent = Agent(
    role="Teaching Expert Specializing in Computer Networks",
    goal="Craft a clear answer of the asked question along with citing the source. Keeping in mind that only the answer to question is mentioned in the answer nothing else.",
    backstory=""" You have 15 years of experience in Teaching computer 
    networks. When using the CN course search tool, convert any pronoun or follow-up references (like 'it', 'its successor', 'that protocol') into explicit search queries before calling the search tool.""",
    llm=llm,
    tools=[search_course_notes],
    max_tokens=800,
)

# Task that is needed to be done
course_task = Task(
    description="Given this conversation history: {history_text}\n\n Answer accurately according to this asked question regarding computer networks: {question}",
    expected_output="""Answer in three clearly labeled parts:

    1. 'From your course notes:'
    - If the search tool returned valid content, summarize ONLY that content.
    - If the search tool returned 'NO_RELEVANT_COURSE_NOTES_FOUND', state: "Not mentioned in your course notes."

    2. 'General knowledge (not in your course notes):'
    - If the topic was missing from course notes, provide a full explanation here using general knowledge.
    - If covered in course notes and nothing new is needed, write: "No additional information beyond your course notes".
    - If the question's answer is enough that it covers the context of the question than say: "No additional information beyond your course notes".

    3. 'Source Citation:'
    - Cite ONLY documents returned by the search tool.
    - If no course notes were used, write: "General Knowledge (External)" or list relevant standard documentation.""",
    agent=course_agent
)

# Wrapping task and agents together
course_crew = Crew(
    tasks=[course_task],
    agents=[course_agent],
    process=Process.sequential,
)

# Getting the agents output and printing it
print("Ask me any question (Type 'exit' if you want to quit).")
while True:
    user_question = input("\nYou: ")
    if user_question.lower() == "exit":
        break
    answer = ask(user_question)
    print(f"\nAssistant:\n{answer}")