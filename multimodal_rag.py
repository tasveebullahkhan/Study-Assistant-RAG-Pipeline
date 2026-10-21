import os
import sys
from pathlib import Path
from google.genai import types
from google import genai
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

#loading api keys in environment
load_dotenv()

# Used chat model
CHAT_MODEL = "gemini-3.5-flash-lite"

# initializing google genai client
client = genai.Client()

# Captioning prompt
CAPTION_PROMPT = (
    "This image is a diagram from a computer networking course. Your description "
    "will be stored in a search index, so students can find the diagram by asking "
    "questions about it. "
    "First, explain in plain sentences what the diagram teaches: the concepts, "
    "the relationships between the parts, and the order of any steps or flow. "
    "Then list every label, field name, number, size and value that appears in it. "
    "If a label contains a typo or misspelling, explicitly state the exact text as it appears "
    "along with its intended correct meaning (for example: labeled as Recursive Rogoltor, "
    "referring to Recursive Resolver). If a label is unreadable, say that it is unreadable. "
    "Never invent text or values that are not visible. "
    "Do not describe colors, icons, borders, fonts or visual style. "
    "Do not include URLs or links. "
    "Write plain text only, with no markdown, headings, bold or bullet symbols."
)

IMAGE_DIR = Path(__file__).parent / "images" 
CAPTION_DIR = Path(__file__).parent / "captions" 

# Convert image to raw bytes and give to gemini as parts object
def caption_image(image_dir:Path) -> None: # Writes file as output
    image_paths = sorted(image_dir.glob("*.png"))
    
    for image_path in image_paths:
        # Checking if the file already exists
        output_path = CAPTION_DIR / f"{image_path.stem}.txt"

        # Skip the writing if file exists on disk
        if output_path.exists():
            print(f"File already exists on the disk.\nEXSISTING_FILE_PATH:{image_path}\n\n")
        
        # Writing the file on the disk if doesn't exists on disk
        else:
            print(f"Saving caption file on the disk.")
            image_bytes = image_path.read_bytes()
            image_parts = types.Part.from_bytes(data = image_bytes, mime_type="image/png")
            response = client.models.generate_content(
                model = CHAT_MODEL,
                contents = [image_parts, CAPTION_PROMPT]
            )
            caption_output = f"{response.text}"

            # Write the file
            output_path.write_text(caption_output, encoding="utf-8")
            print(f"File saved on disk.\n\nFILE_NAME: {output_path.name}")

# Turning each caption into documents with metadata
def Adding_documents_vector_store():
    # scanning all the .txt files dynamically
    caption_paths = sorted(CAPTION_DIR.glob("*.txt"))

    # Read texts and Build document objects along with uniqure ids
    documents = []
    ids = []
    for path in caption_paths:
        caption_text = path.read_text(encoding="utf-8")

        # Original file name from the text file path
        original_file_name = f"{path.stem}.png"

        doc = Document(
            page_content = caption_text,
            metadata = {
                "source":original_file_name,
                "media_type":"image" # Marker identifying an image
            }
        )
        documents.append(doc)
        ids.append(original_file_name)

    # Initializing embedding function and persist chroma directory
    embedding_function = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    persist_dir_path = os.path.join(os.getcwd(), "chromadb")

    # Opening the existing vector store
    vector_store = Chroma(
            embedding_function= embedding_function,
            persist_directory = persist_dir_path
        )

    # Adding documents to the store using ids
    vector_store.add_documents(
            documents = documents,
            ids = ids
        )
    print(f"Successfully updated {len(documents)} image documents", file = sys.stderr)
    return vector_store

caption_image(IMAGE_DIR)
vector_store = Adding_documents_vector_store()

# Fetch record directly by its deterministic ID
dns_ids = ["dns_lookup_sequence.png", "ethernet_frame_path.png", "tcp_vs_udp.png"]
record = vector_store.get()
print(vector_store._collection.count())

# Print record details
for doc_id, meta, text in zip(record['ids'], record['metadatas'], record['documents']):
    print(f"ID: {doc_id}")
    print(f"Metadata: {meta}")
    print(f"Page Content Snippet:\n{text[:300]}...\n")