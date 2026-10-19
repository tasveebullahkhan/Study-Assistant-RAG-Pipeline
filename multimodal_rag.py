from pathlib import Path
from google.genai import types
from google import genai
from dotenv import load_dotenv

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
def caption_image(path:Path) -> str:
    # Checking if the file already exists
    output_path = CAPTION_DIR / f"{path.stem}.txt"
    # Skip the writing if file exists on disk
    if output_path.exists():
        print(f"File already exists on the disk.\n\nFILE_PATH:{path}")
        return
    
    # Writing the file on the disk if doesn't exists on disk
    print(f"Saving caption file on the disk.")
    image_bytes = path.read_bytes()
    image_parts = types.Part.from_bytes(data = image_bytes, mime_type="image/png")
    response = client.models.generate_content(
        model = CHAT_MODEL,
        contents = [image_parts, CAPTION_PROMPT]
    )
    caption_output = f"RESPONSE: {response.text} \n\n SOURCE_TEXT_FILE: {path}"

    # Write the file
    output_path.write_text(caption_output, encoding="utf-8")
    print(f"File saved on disk.\n\nFILE_NAME: {output_path.name}")

result = caption_image(IMAGE_DIR / "tcp_vs_udp.png")