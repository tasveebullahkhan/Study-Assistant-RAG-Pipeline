# Study-Assistant-RAG-Pipeline
A retrieval-augmented generation (RAG) system that answers questions about my Computer Networks coursework, grounded in my own study materials rather than the model's general knowledge. Every answer cites which source document it came from.

## Development Roadmap
* ✅ Phase 1 — Advanced RAG Complete.
* ✅ Phase 2 — AI Agents + crewAI.
* ✅ Phase 3 — MCP server — with DataCamp's "Introduction to MCP" as guided prep.
* ⏳ Phase 4 — Observability/LangSmith
* ⏳ Phase 5 — Multimodal RAG
* ⏳ Phase 6 — AI Safety/red teaming
* ⏳ Phase 7 — Fine-tuning (Phi-3 mini)

## Why this project
Used my own semester's notes so I know that weather retrieval and generation actually work or just look like it works. 

## Project structure
* `helpers.py` — reusable logic: document loaders, chunking, retriever setup, context formatting, shared constants
* `main.py` — the interactive study assistant (ask a question, get a cited answer)
* `agent.py` — CrewAI agent layer wraps the retriever as a tool and conversational memory is added.
* `evaluate.py` — retrieval evaluation script, run independently to check retrieval quality against a known test set
* `evaluate_agent.py` — Agent evaluation script, to check agents output quality against a known test.

## Tech Stack
* langchain-community, langchain-text-splitters, langchain-chroma, langchain-core
* langchain-google-genai (gemini-embedding-001 for embeddings, gemini-3.1-flash-lite-preview for generation)
* ChromaDB (local, persisted)
* crewai, crewai-tools (agent orchestration)
* Mistral API (mistral-small-latest) — used for the agent layer; Groq's free tier couldn't sustain more than 1-2 questions per session, Gemini chat had a separate quota issue

## Pipeline
* Documents (.docx, .pptx)
* Loaders (UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader)
* Chunking (RecursiveCharacterTextSplitter — different chunk_size/overlap per format)
* Embeddings (GoogleGenerativeAIEmbeddings) → Chroma (persisted locally)
* Build fresh or load existing vector_store depending on persisted chroma directory already existing or not
* Retriever (similarity search, k=3)
* `format_docs()` — attaches source filename to each retrieved chunk
* Prompt (instructs the model to cite the exact source filename, no guessing)
* Gemini (gemini-3.1-flash-lite-preview) → Answer + Sources

## Running it
1. Set a Gemini API key in a `.env` file `GOOGLE_API_KEY=...`, `MISTRAL_API_KEY=...` (only needed for `agent.py`)
2. pip install -r requirements.txt
3. Place source documents in the project directory. Add your own source documents this repo doesn't include the original files (lecture slides are the instructor's material, not mine to redistribute). Place a `.docx` and a `.pptx` of your own in the project directory and update the filenames in the script to match.
4. Run `main.py` for the core RAG assistant, or `agent.py` for the agent layer with tool-use judgment and conversational memory — first run builds and persists the vector store, subsequent runs load the existing one

## Design decisions & Source material
* **Source material:** `CN_Logical_IPv4_IPv6_Notes.docx` (logical addressing, IPv4/IPv6 addressing and packet structure, transition mechanisms) and `Hub, Switch and Router.pptx` (device comparison across OSI layers, functionality, advantages/disadvantages). Two different formats deliberately, to force the loader and chunking logic to handle more than one document type.
* **Chunking:** Different chunk settings per format. The docx are chunked at 2000 chars with 200 overlap so multi-part explanations don't get cut off mid-concept. The pptx is one distinct topic per slide, so it's chunked smaller 1000 chars with no overlap. 20% rule of the chunk_size is applied for chunk overlap.

## Agent Layer
`agent.py` adds a CrewAI agent that decide for itself weather a question needs course notes to answer or can be answered from general knowledge and state weather the answer was from course notes or general knowledge to avoid blending as if it were grounded.
* One agent, one tool (the retriever from `helpers.py`, wrapped)
* Task forces three labeled answers, one answer from course material, second from llm's own knowledge and third is source citation.
* Conversational memory is hand built not CrewAI's built-in `memory=True` a simple side-step.
* **Provider notes:** Went through three LLM providers before landing on one that actually held up: Gemini (chat completions hit a free-tier quota wall — separate from the embeddings API, which worked fine), Groq (fast, but its free tier couldn't sustain more than 1-2 questions before rate-limiting), and finally Mistral, which has been stable for actual multi-turn testing.

## MCP Server (Phase-3)
`retriever_server.py` adds an MCP server. The server consists of a tool (notes_retriever) that retrieves chunks on the basis of similarity. This tool only covers retrieval not the whole agent because its purpose is not to give llm generated output client already has that so the retrieved chunks have more importance thus we only wrapped retrieval as a tool. Since client can ask for any number of chunks so I updated the retrieval function (of phase 1) to build just vector store so that on server side we can identify the number of parameters (k) and client can enter any number of chunks according to their needs. Conversation result is formatted by reusing format_docs from `helpers.py`. 
 **Relevance threshold (Content Gap detection for MCP tool):** `similarity_search` alone always returns the top-k closest matches regardless of whether they're actually relevant — an off-topic query (e.g. "cooking recipe of burger") still gets *something* back, since vector similarity search doesn't have a built-in "nothing matches" case. To catch this, `notes_retriever` uses `similarity_search_with_relevance_scores` and checks the top result's score against a 0.5 threshold before returning chunks. Below 0.5, the tool returns a scope-aware message ("This knowledge base only covers CN121 course material") instead of irrelevant chunks. The 0.5 cutoff was derived empirically, not guessed — tested against known in-scope queries across both indexed docs (IPv4/IPv6 doc: ~0.56–0.61, router/switch/hub doc: ~0.56+, a cross-document query touching both: ~0.58) versus known out-of-scope queries (Border Gateway Protocol, a networking-adjacent topic *not* covered in these notes: ~0.44; an unrelated "burger recipe" query: ~0.32). The gap between relevant (~0.56+) and irrelevant (~0.44 and below) held consistently across documents, which is why 0.5 was chosen as the cutoff.

## Testing & Evaluation
### Base Retrieval (`evaluate.py`)
* To check the retrievals correctness `evaluate.py` is used. It checks that the retrieved sources and expected sources matches each other, so the retrieved information is from the correct source. 
* It checks on the basis of presence(uniqueness) of source not how many times the source is actually used. So even if the source is used more than once due to multiple chunks using the source multiple times it wouldn't matter and ignore those duplicates or order.
* There are 4 single source cases and one multiple source case. Current result is "5/5 Passed".
* This is just a simple hand-built metric not a sophisticated LLM-graded eval like RAGAS.

### Agent Evaluation (`evaluate_agent.py`)
* To check the agents' correctness `evaluate_agent.py` is used. It first checks whether answer is found in our course notes or not on the basis of which it tells us if answer is from course notes or general knowledge. It then checks if the source cited is "General Knowledge (External)" for an outcome on the basis of that tell us whether answer is from general knowledge or not. Finally, if both cases are true test is passed otherwise failed.
* There are total 5 cases 4 single source cases and one multiple source case (Among 4 single source cases 2 are "in_notes" cases and two are "not-in-notes" cases. The multiple source case contains both notes files).
* Current result is "5/5 Passed" (Provided that each of them is run separately due to some limitations discussed below).
* To execute the test run `python evaluate_agent.py`.

### MCP Tool Testing (`retriever_client.py`)
* To validate the working of our MCP server I made this client which has two functions one to just list tool and other to call the tool and get its output from MCP server. Its purpose is to just test the working of the server thus query is hardcoded, but you can enter any query in the key to test its working. The queries in scope of notes that I used to validate are "What is IPv4?" and "What is a router?". The query "How does a router's use of IP addresses relate to logical addressing and how is that different from how a switch uses MAC addresses?" test across all the files of the course notes. The queries that were out of scope are "What is BGP?" and "What is cooking recipe of burger?" (Even though BGP is related to computer networks it is not covered in the course notes so keep that in mind).

## Developer Log: Limitations & Bugs
* **A real limitation I found (Content Gap vs Bug):** While testing retrieval quality for the question "What is a MAC address?" I only found one result that was actually relevant the rest were not. The reason was not the "search_type" or retrieval bug, but it was because the documents itself did not contain enough of the information about MAC addressing. This was the reason why I used files of my own and that is the why of the project. Changing the "search_type" would not fix anything if the material itself was not enough. This is because when I tested on a different question like "What is the difference between IPv4 and IPv6" with the same settings it returned three actually very relevant results. Same pipeline different results. Documenting this because it actually helps me understand the difference between pipeline bug and content gap.
  
* **Agent Limitation (Rate Limits):** The limitation I faced is that on running test cases (or `agent.py` and asking one question) the evaluation worked fine. But on running multiple cases together it showed rate limit error. The first thing i observed is that question that are answered from the notes contains one tool call while general knowledge answered questions contain 4 tool calls (BGP = 4 tool calls, IPv4 = 1 tool call). The actual limit of the model from dashboard was: 0.17 RPS, 20,000 tokens/minute. So, I added retry only once after which questions that are not from notes or require multiple sources when evaluated resulted in passed cases. This is because of relevance so for a topic outside the notes the llm calls the tool 4 times since retrieved result was not relevant to the asked question. However, on running all the cases together it still showed the same error. So, I reduced the retrying to 0 after first attempt and added a time gap of 20 seconds between each iteration and it still showed rate limit error. So finally, I ran all the test cases one by one (multiple times) due to this limitation and all of them passed (Free tier limit not a code bug).
  
* **Agent Memory Limitation:** CrewAI's built in memory system's default is OpenAI embedder, and its Google embedder option depends on the `google-generativeai` package which Google has fully deprecated. Current short-term memory is a running list of prior Q&A pairs get joined into a string and passed into the `{history}` placeholder on every call.
  
* **Bugs hit and fixed along the way:**
  * Wrong docx package was installed but uninstalled it and installed right package (`python-docx`)
  * Combining the documents into a single list after chunking using `.extend()` method return none instead use concatenation
  * `ChatPromptTemplate.from_messages(["human", message])` created two separate messages instead of one
  * `persist_dir_path` pointed at a literal string `"os.getcwd"` instead of an actual call to `os.getcwd()`
  * 
