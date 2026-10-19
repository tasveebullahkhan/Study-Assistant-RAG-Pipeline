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

# Convert image to raw bytes and give to gemini as parts object
def caption_image(path:Path) -> str:
    image_bytes = path.read_bytes()
    image_parts = types.Part.from_bytes(data = image_bytes, mime_type="image/png")
    response = client.models.generate_content(
        model = CHAT_MODEL,
        contents = [image_parts, CAPTION_PROMPT]
    )
    return f"RESPONSE: {response.text} \n\n SOURCE:{path}"

result = caption_image(IMAGE_DIR / "dns_lookup_sequence.png")
print(result)