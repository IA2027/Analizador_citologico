
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_MODEL = "gemini-3.5-flash-lite"

APP_NAME = "Analizador Citologico"

CARPETAS = [
    "informes",
    "imagenes"
]

for carpeta in CARPETAS:
    os.makedirs(carpeta, exist_ok=True)
