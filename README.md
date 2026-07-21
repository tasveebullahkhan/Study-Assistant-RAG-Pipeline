# Study-Assistant-RAG-Pipeline
A retrieval-augmented generation (RAG) system that answers questions about my Computer Networks coursework, grounded in my own study materials rather than the model's general knowledge. Every answer cites which source document it came from.

## Why this project
Used my own semester's notes so i know that weather retrieval and generation actually works or just look like it works. 

## Pipeline
- Documents (.docx, .pptx)
- Loaders (UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader)
- Chunking (RecursiveCharacterTextSplitter — different chunk_size/overlap per format)
- Embeddings (GoogleGenerativeAIEmbeddings) → Chroma (persisted locally)
- Build fresh or load existing vector_store depending on persisted chroma directory already existing or not
- Retriever (similarity search, k=3)
- format_docs() — attaches source filename to each retrieved chunk
- Prompt (instructs the model to cite the exact source filename, no guessing)
- Gemini (gemini-3.1-flash-lite-preview) → Answer + Sources
  
## Source material
- CN_Logical_IPv4_IPv6_Notes.docx — logical addressing, IPv4/IPv6 addressing and packet structure, transition mechanisms
- Hub, Switch and Router.pptx — device comparison across OSI layers, functionality, advantages/disadvantages

Two different formats deliberately, to force the loader and chunking logic to handle more than one document type.

 ## Design decisions
Different chunk settings per format. The docx are chunked at 2000 chars with 200 overlap so multi-part explanations don't get cut off mid-concept. The pptx is one distinct topic per slide, so it's chunked smaller 1000 chars with no overlap. 20% rule of the chunk_size is applied for chunk overlap

## A real limitation I found
While testing retrieval quality for the question "What is a MAC address?" I only found one result that was actually relevant the rest were not. The reason was not the "search_type" or retrieval bug but it was because the documents itself did not contain enough of the information about MAC addressing. This was the reason why I used files of my own and that is the why of the project. Changing the "search_type" would not fix anything if the material itself was not enough.

This is because when I tested on a different question like "What is the difference between IPv4 and IPv6" with the same settings it returned three actually very relevant results. Same pipeline different results. Documenting this because it actually help me understand the difference between pipeline bug and content gap.

## Bugs hit and fixed along the way
- Wrong docx package was installed but uninstalled it and installed right package (python-docx)
- Combining the documents into a single list after chunking using ".extend()" method return none instead use concatenation
- ChatPromptTemplate.from_messages(["human", message]) created two seprate messages instead of one
- "persist_dir_path" pointed at a literal string `"os.getcwd"` instead of an actual call to os.getcwd()

## Stack
- langchain-community, langchain-text-splitters, langchain-chroma, langchain-core
- langchain-google-genai (gemini-embedding-001 for embeddings, gemini-3.1-flash-lite-preview for generation)
- ChromaDB (local, persisted)

## Running it
1. Set a Gemini API key in a ".env" file (`GOOGLE_API_KEY=...`)
2. pip install -r requirements.txt
3. Place source documents in the project directory. Add your own source documents this repo doesn't include the original files (lecture slides are the instructor's material, not mine to redistribute). Place a ".docx" and a ".pptx" of your own in the project directory, and update the filenames in the script to match.
4. Run the script — first run builds and persists the vector store, subsequent runs load the existing one
