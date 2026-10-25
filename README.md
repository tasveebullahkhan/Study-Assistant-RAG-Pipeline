# Study-Assistant-RAG-Pipeline
A retrieval-augmented generation (RAG) system that answers questions about my Computer Networks coursework, grounded in my own study materials rather than the model's general knowledge. Every answer cites which source document it came from.
 
## Development Roadmap
* ✅ Phase 1 — Advanced RAG Complete.
* ✅ Phase 2 — AI Agents + crewAI.
* ✅ Phase 3 — MCP server — with DataCamp's "Introduction to MCP" as guided prep.
* ✅ Phase 4 — Observability/LangSmith
* ✅ Phase 5 — Multimodal RAG
* ⏳ Phase 6 — AI Safety/red teaming
* ⏳ Phase 7 — Fine-tuning (Phi-3 mini)
## Why this project
Used my own semester's notes so I know whether retrieval and generation actually work or just look like it works. 
 
## Project structure
* `helpers.py` — reusable logic: document loaders, chunking, retriever setup, context formatting, shared constants
* `main.py` — the interactive study assistant (ask a question, get a cited answer)
* `agent.py` — CrewAI agent layer that wraps the retriever as a tool and adds conversational memory.
* `observability.py` — LangSmith/OpenTelemetry tracing setup (`setup_tracing()`), kept separate from agent logic
* `evaluate.py` — retrieval evaluation script, run independently to check retrieval quality against a known test set
* `evaluate_agent.py` — Agent evaluation script, to check agents output quality against a known test.
* `retriever_server.py` — The MCP server whose purpose is to wrap the retriever as a tool.
* `retriever_client.py` — Client that is used to validate the working of the MCP server.
* `multimodal_rag.py` — Captioning all the images and adding them as documents in vector store
* `evaluate_multimodal.py` —  To check image retrieval quality against a known test
## Tech Stack
* langchain-community, langchain-text-splitters, langchain-chroma, langchain-core
* langchain-google-genai (gemini-embedding-001 for embeddings, gemini-3.1-flash-lite-preview for text generation)
* ChromaDB (local, persisted)
* crewai (agent orchestration)
* Groq API (`qwen/qwen3.8-27b`) — used for the agent layer; landed here after testing Gemini (chat completions hit a free-tier quota wall, so it can't be used in the agent unless a payment method is added), Mistral (free tier proved too unreliable for consistent testing) and Groq's `openai/gpt-oss-120b` (failed the agent evaluation, see Developer Log)
* LangSmith + OpenTelemetry (opentelemetry-instrumentation-crewai, openinference-instrumentation-litellm) — distributed tracing for both main.py and agent.py
* google and google.genai (genai client and types object respectively)
* Gemini (`[CAPTION_MODEL_NAME]`, through `google.genai`) — writes the captions for the diagrams in `multimodal_rag.py`
## Pipeline
* Documents (.docx, .pptx) and diagrams (.png)
* Loaders (UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader)
* Chunking (RecursiveCharacterTextSplitter — different chunk_size/overlap per format)
* Image ingestion (`multimodal_rag.py`, a separate script) — a vision model captions each diagram with one general prompt, one caption = one document (no splitting), id = image filename, metadata = `source` (filename) and `media_type` (image)
* Embeddings (GoogleGenerativeAIEmbeddings) → Chroma (persisted locally, text chunks and image captions in the same store)
* Build fresh or load existing vector_store depending on persisted chroma directory already existing or not
* Retriever (similarity search, k=3 (phase-1), k=2(phase-2), k=3(phase-3))
* `format_docs()` — attaches source filename to each retrieved chunk (images cite the original .png)
* Prompt (instructs the model to cite the exact source filename, no guessing)
* LLM → Answer + Sources
## Running it
1. Set the required API keys in a `.env` file:
   - `GOOGLE_API_KEY=...` (embeddings, used by `main.py` and `helpers.py`; also image captioning in `multimodal_rag.py`)
   - `GROQ_API_KEY=...` (LLM provider for `agent.py`)
   - For tracing: `LANGSMITH_API_KEY=...`, `LANGSMITH_TRACING=true`, `OTEL_EXPORTER=otlp_http`, `OTEL_ENDPOINT=https://api.smith.langchain.com/otel`, `OTEL_HEADERS=x-api-key=<your LangSmith API key>`
2. pip install -r requirements.txt
3. Place source documents in the project directory. Add your own source documents this repo doesn't include the original files (lecture slides are the instructor's material, not mine to redistribute). Place a `.docx` and a `.pptx` of your own in the project directory and update the filenames in the script (DOCX_FILE, PPTX_FILE) to match.
4. Run `main.py` for the core RAG assistant, or `agent.py` for the agent layer with tool-use judgment, conversational memory, and LangSmith tracing — first run builds and persists the vector store, subsequent runs load the existing one.
5. Run `multimodal_rag.py` after `main.py` or `agent.py` for image ingestion. Images must be in the images folder, captions get generated from them and stored in caption folder. If the database is deleted and rebuild the image documents are gone so image ingestion must be rerun after rebuild
6. Run everything from the project root because the vector store path depends on the directory from which it is launched.
## main.py: Design decisions & Source material (Phase-1)
* **Source material:** `CN_Logical_IPv4_IPv6_Notes.docx` (logical addressing, IPv4/IPv6 addressing and packet structure, transition mechanisms) and `Hub, Switch and Router.pptx` (device comparison across OSI layers, functionality, advantages/disadvantages). Two different formats deliberately, to force the loader and chunking logic to handle more than one document type.
* **Chunking:** Different chunk settings per format. The docx are chunked at 2000 chars with 200 overlap so multi-part explanations don't get cut off mid-concept. The pptx slides are short, so it's chunked smaller 1000 chars with no overlap. 10% rule of the chunk_size is applied for chunk overlap.
## Agent Layer (Phase-2)
`agent.py` adds a CrewAI agent that decides for itself whether a question needs course notes to answer or can be answered from general knowledge, and states whether the answer was from course notes or general knowledge to avoid blending as if it were grounded.
* The agent retrieves top 2 k chunks (k=2) and there is no special cutoff case as in MCP Server (read phase 3 for more understanding).
* One agent, one tool (the retriever from `helpers.py`, wrapped)
* The task requires three labeled parts, one answer from course material, second from llm's own knowledge and third is source citation.
* Conversational memory is hand built not CrewAI's built-in `memory=True` a simple side-step.
* The agent is told in its prompt not to retry searches, to avoid rate-limit errors.
* **Provider notes:** Went through three LLM providers, and two Groq models, over the course of this project.
  - **Gemini** was tried first for the agent layer. Chat completions hit a free-tier quota wall almost immediately — separate from the embeddings API, which worked fine and is still used for that.
  - **Mistral** replaced Gemini and held up well for early multi-turn testing and evaluation (see the rate-limit note in the Developer Log below for the tool-call-related limits hit at that stage). It stayed the default provider through Phase 3.
  - During **Phase 4** observability work, Mistral's free tier started returning frequent, unexplained `429 Rate limit exceeded` errors — even after long idle periods with zero other traffic. Mistral's own support confirmed this is expected: free-tier access is best-effort with no reserved capacity, so requests can be rejected regardless of actual usage or timing.
  - Given that unpredictability made consistent testing impossible, the agent was switched to **Groq**, first with `openai/gpt-oss-120b`. That model failed the agent evaluation that Mistral had passed (see Testing & Evaluation and the Developer Log), so the agent now runs on `qwen/qwen3.8-27b`, also on Groq, where the evaluation passes again.
## MCP Server (Phase-3)
`retriever_server.py` adds an MCP server. The server consists of a tool (`notes_retriever`) that retrieves chunks on the basis of similarity. This tool only covers retrieval, not the whole agent. The purpose isn't to give LLM-generated output — the client already has its own model for that — so the retrieved chunks themselves carry more value than a synthesized answer would. That's why only retrieval was wrapped as a tool, not the full agent.
 
Since the client (`retriever_client.py`) can ask for any number of chunks, I added a function next to the Phase 1 retriever builder that builds just the vector store instead of a pre-configured retriever. This removes the baked-in `k` value, so `k` is now passed per request and the client controls how many chunks it gets back. Conversation output is formatted by reusing `format_docs` from `helpers.py`.
 
**Relevance threshold (Content Gap detection for MCP tool):** `similarity_search` alone always returns the top-k closest matches regardless of whether they're actually relevant — an off-topic query (e.g. "cooking recipe of burger") still gets *something* back, since vector similarity search doesn't have a built-in "nothing matches" case. To catch this, `notes_retriever` uses `similarity_search_with_relevance_scores` and checks the top result's score against a 0.5 threshold before returning chunks, so if the top chunk passes, the weaker chunks come along with it. Below 0.5, the tool returns a scope-aware message ("This knowledge base only covers CN121 course material") instead of irrelevant chunks. The 0.5 cutoff was derived empirically, not guessed — tested against known in-scope queries across both indexed docs (IPv4/IPv6 doc: ~0.56–0.61, router/switch/hub doc: ~0.56+, a cross-document query touching both: ~0.58+) versus known out-of-scope queries (Border Gateway Protocol, a networking-adjacent topic *not* covered in these notes: ~0.44; an unrelated "burger recipe" query: ~0.32). The gap between relevant (~0.56+) and irrelevant (~0.44 and below) held consistently across documents, which is why 0.5 was chosen as the cutoff.
 
## Observability (Phase-4)
 
Added distributed tracing across the project, replacing manual print-statement debugging with real, inspectable traces on LangSmith.
 
### Phase 4a — `main.py` (LangChain LCEL chain)
 
Traced natively via LangSmith's standard `LANGSMITH_TRACING`/`LANGSMITH_API_KEY` environment variables — no code changes needed. Each step of the chain (retriever, prompt formatting, LLM call) appears as a separate span with real inputs, outputs, and token counts.
 
### Phase 4b — `agent.py` (CrewAI agent)
 
Required a different approach, since CrewAI isn't LangSmith-native and doesn't always route through LiteLLM the way it might appear to.
 
- **Gemini models bypass LiteLLM entirely.** CrewAI doesn't talk to Gemini through LiteLLM — it uses Google's own SDK directly for Gemini calls, so no LiteLLM-based tracing can see them.
- **Mistral and Groq models route through LiteLLM**, so they can be traced — but LiteLLM's own native tracing option (`litellm.callbacks = ['otel']`) doesn't produce a trace when the call happens inside CrewAI's execution, even for a provider that does use LiteLLM.
- **Working setup:** two separate instrumentors, since CrewAI's own execution (agents, tasks) and the underlying LiteLLM completion call are two different things to trace — `CrewAIInstrumentor` (from `opentelemetry-instrumentation-crewai`) watches agent/task-level execution, and `LiteLLMInstrumentor` (from `openinference-instrumentation-litellm`) watches the actual LLM calls (model, tokens, cost). Both are wired to a shared `TracerProvider` pointed at LangSmith.
- Tracing setup lives in a standalone `observability.py` (a single `setup_tracing()` function), kept separate from `agent.py`'s actual business logic.
- **Known warning:** every `agent.py` run prints a `DependencyConflict` message at startup (requested `crewai >= 1.0.0`, found `crewai 0.157.0`).
Currently using Groq as the traced provider.
 
## Multimodal-RAG (Phase-5)
The three diagrams used (`dns_lookup_sequence.png`, `ethernet_frame_path.png`, `tcp_vs_udp.png`) are AI-generated, not course material, and some of their labels are garbled.
 
* **Captioning-then-embed** This method of Captioning then embed is chosen on purpose because it uses the already built text pipeline and treat caption same as any other text which makes the captions readable as well as debuggable. The captions are written by Gemini (`gemini-3.5-flash-lite`).
* **Caption-Prompt** The caption prompt is designed to teach the students main concept, relationship and workflow with clearly stating unreadable words and correct clearly misspelled words. The model is told not to invent any information by itself. The model is advised not to describe colors, icons and font style and generate plain text only so that it can be more student oriented (concepts and workflows are necessary as compared to font style for learning purposes.)
* **Adding-images-to-store** The same vector store is opened and images are added as one document per image with `source` and `media_type` metadata. One document per image because splitting a caption could separate a diagram's steps from its explanation.
* **Relevance-threshold** Image caption top score were (ethernet_frame_path.png:0.56, dns_lookup_sequence.png:0.66, tcp_vs_udp.png:0.64) above 0.5 the same way as before so the 0.5 threshold held meaning all the images top scores were above 0.5 and out of scope question (What is a BGP?) score (0.48) below it. The ~0.44 BGP figure in Phase 3 was measured with different wording.
* **Why not CLIP-style models** Because images are label heavy and captions are debuggable and readable.
* **ID-selection** filename is id so rerunning ingestion doesn't create duplicates.
* **No image-rebuilt** If chromadb is deleted and rebuilt the image documents are lost so need to rerun ingestion again.
* **No query-side change** The tools, agent and format_docs find the image documents as they were so no need to change them.
## Testing & Evaluation
### Base Retrieval (`evaluate.py`)
* To check the retrievals correctness `evaluate.py` is used. It checks that the retrieved sources and expected sources matches each other, so the retrieved information is from the correct source. 
* It checks on the basis of presence(uniqueness) of source not how many times the source is actually used. So even if the source is used more than once due to multiple chunks using the source multiple times it wouldn't matter and ignore those duplicates or order.
* There are 4 single source cases and one multiple source case. Current result is "5/5 Passed".
* This is just a simple hand-built metric not a sophisticated LLM-graded eval like RAGAS.
### Agent Evaluation (`evaluate_agent.py`)
* To check the agents' correctness `evaluate_agent.py` is used. It first checks whether answer is found in our course notes or not on the basis of which it tells us if answer is from course notes or general knowledge. It then checks if the source cited is "General Knowledge (External)" for an outcome on the basis of that tell us whether answer is from general knowledge or not. Finally, if both cases are true test is passed otherwise failed.
* There are total 5 cases 4 single source cases and one multiple source case (Among 4 single source cases 2 are "in_notes" cases and two are "not-in-notes" cases. The multiple source case contains both notes files).
* Results by provider/model:
  - **Mistral** (through Phase 3): "5/5 Passed" (each case run separately, due to the rate limits discussed below).
  - **Groq `openai/gpt-oss-120b`** (early Phase 4): regressed. Almost all cases failed and only the IPv4 case passed. Failure types: empty LLM responses, source filenames not matching exactly, and output not following the expected format.
  - **Groq `qwen/qwen3.8-27b`** (current): passes again, matching the Mistral-era result. Each case is still run separately because of the rate limits discussed below.
* To execute the test run `python evaluate_agent.py`.
### MCP Tool Testing (`retriever_client.py`)
* To validate the working of our MCP server I made this client which has two functions one to just list tool and other to call the tool and get its output from MCP server. Its purpose is to just test the working of the server thus query is hardcoded, but you can enter any query in the key to test its working. The queries in scope of notes that I used to validate are "What is IPv4?" and "What is a router?". The query "How does a router's use of IP addresses relate to logical addressing and how is that different from how a switch uses MAC addresses?" test across all the files of the course notes. The queries that were out of scope are "What is BGP?" and "What is cooking recipe of burger?" (Even though BGP is related to computer networks it is not covered in the course notes so keep that in mind).
* After the images were added (Phase 5), the DNS lookup question returned the diagram's caption with `dns_lookup_sequence.png` as its citation, and "What is BGP?" still returned the scope message.
### Multimodal RAG Evaluation (evaluate_multimodal.py)
* It tests whether a question that can only be answered from a diagram makes the agent cite the right file. The cases are in separate file `evaluate_multimodal.py`.
* There are total 5 cases each image filename as the expected sources. The first 3 image cases are from LLM and lean toward images that's why two more questions were added by myself.
* The answer must say it comes from the notes and the source citation must contain the filename. The `in_notes` means that answer comes from the knowledge base (don't it confuse with notes files).
* **RESULT** All the cases were passed as long as it does not hit rate limit error. 4/4 passed in one go and 5/5 passed if cases run separately. The combined run stops at the first rate-limit error, so cases that did not run are not counted.
* **Regression-check** After adding images `evaluate_agent.py` gave the same results as before (4/4 passed until it reaches rate limit error and 5/5 passed if the cases are executed separately). This shows that image ingestion doesn't displace the docx and pptx chunks including the cross document check.
* The check proves that the right filename was cited not that the answered text is actually right since its a substring match.
* No out of scope check is here because it is already covered in MCP tool check
* The diagrams are few so it shows the approach works on these three diagrams.
* **Retrieval-level-test** images top scores were 0.56 to 0.66 and for the out-of-scope (BGP test) score was 0.48. 
## Developer Log: Limitations & Bugs
* **A real limitation I found (Content Gap vs Bug):** While testing retrieval quality for the question "What is a MAC address?" I only found one result that was actually relevant the rest were not. The reason was not the "search_type" or retrieval bug, but it was because the documents itself did not contain enough of the information about MAC addressing. This was the reason why I used files of my own and that is the why of the project. Changing the "search_type" would not fix anything if the material itself was not enough. This is because when I tested on a different question like "What is the difference between IPv4 and IPv6" with the same settings it returned three actually very relevant results. Same pipeline different results. Documenting this because it actually helps me understand the difference between pipeline bug and content gap.
  
* **Model change broke the prompt guardrails (gpt-oss-120b → Qwen):** After moving the agent to Groq's `openai/gpt-oss-120b`, the agent evaluation that passed on Mistral mostly failed: empty LLM responses, mismatched source filenames, and output that ignored the expected three-part format. In manual testing it answered "What is BGP?" (which is not in the notes) as "from your course notes", and when asked where in the notes that came from, it invented a section, a slide number and a filename that do not exist. This is exactly the false grounding the three-part output was designed to prevent. Switching to `qwen/qwen3.8-27b` restored the passing evaluation, which points to model behavior rather than retrieval or the pipeline. The lesson: instruction-following guardrails written and validated against one model did not carry over to another, and the evaluation is what caught the regression. On Qwen, the same "What is BGP?" question followed by "where in the notes is that?" no longer produces a fabricated citation.
* **Agent Limitation (Free-Tier Rate Limits):**
  * First hit on Mistral, and still present after the Phase 4 switch to Groq (see the end of this entry). On running test cases (or `agent.py` and asking one question) the evaluation worked fine. But on running multiple cases together it showed rate limit error. The first thing I observed is that questions that are answered from the notes use one tool call while general knowledge answered questions use 4 tool calls (BGP = 4 tool calls, IPv4 = 1 tool call).
  * The actual limit of the model from mistral dashboard was: 0.17 RPS, 20,000 tokens/minute. So, I added retry only once after which questions that are not from notes or require multiple sources when evaluated resulted in passed cases when ran separately. This is because of relevance so for a topic outside the notes the llm calls the tool 4 times since retrieved result was not relevant to the asked question. However, on running all the cases together it still showed the same error.
  * So, I reduced the retrying to 0 after first attempt and added a time gap of 20 seconds between each iteration and it still showed rate limit error.
  * So finally, I ran all the test cases one by one (multiple times) due to this limitation and all of them passed (Free tier limit not a code bug). Groq's free tier has similar constraints: `openai/gpt-oss-120b` and `qwen/qwen3.8-27b` each allow 30 requests/min, 1,000 requests/day, 8,000 tokens/min and 200,000 tokens/day, enforced per organization. A single agent question can trigger several tool calls, each resending the prompt, history and retrieved chunks, so the tokens-per-minute cap is the limit most likely to bind. The evaluation is therefore still run one case at a time.
  
* **Agent Memory Limitation:** CrewAI's built in memory system's default is OpenAI embedder, and its Google embedder option depends on the `google-generativeai` package which Google has fully deprecated. Current short-term memory is a running list of prior Q&A pairs get joined into a string and passed into the `{history_text}` placeholder on every call.
* **Multimodal Limitations (Phase 5):** The captions still contain some markdown links and notes about typos from the diagrams. The image documents are added to the store by a separate script and are not rebuilt with the text, so if the `chromadb` folder is deleted and rebuilt, the diagrams are gone until the ingestion script is rerun. `PERSIST_DIR_PATH` is built from the directory the script is launched from, so everything has to be run from the project root.
  
* **Bugs hit and fixed along the way:**
  * Wrong docx package was installed but uninstalled it and installed right package (`python-docx`)
  * Combining the documents into a single list after chunking using `.extend()` method return none instead use concatenation
  * `ChatPromptTemplate.from_messages(["human", message])` created two separate messages instead of one
  * `persist_dir_path` pointed at a literal string `"os.getcwd"` instead of an actual call to `os.getcwd()`
  * `helpers.py` print statements (used for debug output) were writing to stdout, which `stdio` transport reserves exclusively for JSON-RPC messages — this caused the MCP client to fail parsing responses. Fixed by redirecting those prints to stderr.
  * Upgrading `langsmith` (for OpenTelemetry support) bumped `chromadb` to a version incompatible with `crewai-tools`' pin and broke `main.py`. Since the project code never imports `crewai-tools`, it was removed and the virtual environment rebuilt from a pinned `requirements.txt`.
  * Running `evaluate_multimodal.py` before the images were ingested crashed with a Groq rate-limit error. With nothing to retrieve, the agent searched again and one completion used 989 output tokens. Not a code bug. After ingestion the DNS case passed.