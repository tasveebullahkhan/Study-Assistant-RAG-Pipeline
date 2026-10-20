from pathlib import Path
from google.genai import types
from google import genai
from dotenv import load_dotenv
from langchain_core.documents import Document

#loading api keys in environment
load_dotenv()

# Used chat model
CHAT_MODEL = "gemini-3.5-flash-lite"

# Loading client
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
            caption_output = f"RESPONSE: {response.text} \n\n SOURCE_IMAGE: {image_path.name}"

            # Write the file
            output_path.write_text(caption_output, encoding="utf-8")
            print(f"File saved on disk.\n\nFILE_NAME: {output_path.name}")

# Turning each caption into documents with metadata
def generate_caption_documents() -> list[dict]:
    # scanning all the .txt files dynamically
    caption_paths = sorted(CAPTION_DIR.glob("*.txt"))

    # Read texts and Build document objects
    documents = []
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
    print(f"GENERATING {len(documents)} DOCUMENTS")
    return documents


# Captioning all the images
generate_caption_documents()