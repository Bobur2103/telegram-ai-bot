import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()

# Tokenni o‘qib olish
token = os.getenv("HUGGINGFACE_TOKEN")
if not token:
    raise ValueError("HUGGINGFACE_TOKEN .env faylda topilmadi!")

# Hugging Face klientini yaratish
client = InferenceClient(token=token)
