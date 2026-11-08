
import customtkinter as ctk
from gemini_engine import analizar_citologia
from pdf_exporter import exportar_informe
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as PDFImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import threading
import os
import io
import html
from datetime import datetime

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BG = "#111418"
PANEL = "#1B2026"
PANEL2 = "#242B32"
GREEN = "#16A34A"
ORANGE = "#F97316"
WHITE = "#FFFFFF"
GRAY = "#AEB7C2"

MODEL = "gemini-3.5-flash-lite"

os.makedirs("informes", exist_ok=True)

imagen_actual = None
ruta_imagen = None
resultado_actual = ""

# ==========================================
# VENTANA PRINCIPAL
# ==========================================

root = ctk.CTk()
root.title("Analizador Citologico")
root.geometry("1250x850")
root.minsize(1050, 720)
root.configure(fg_color=BG)

# ==========================================
# FUNCIONES
# ==========================================

def seleccionar_imagen():

    global imagen_actual, ruta_imagen

    ruta = filedialog.askopenfilename(
        title="Seleccionar imagen citológica",
        filetypes=[
            ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not ruta:
        return

    try:
        imagen = Image.open(ruta)
        imagen = ImageOps.exif_transpose(imagen)
        imagen.load()

        imagen_actual = imagen.convert("RGB")
        ruta_imagen = ruta

        vista = imagen_actual.copy()
        vista.thumbnail((440, 290))

        foto = ctk.CTkImage(
            light_image=vista,
            dark_image=vista,
            size=vista.size
        )

        imagen_label.configure(
            image=foto,
            text=""
        )

        imagen_label.image = foto

        nombre_label.configure(
            text=os.path.basename(ruta)
        )

        estado_label.configure(
            text="Imagen cargada correctamente",
            text_color=GREEN
        )

        resultado_text.configure(state="normal")
        resultado_text.delete("1.0", "end")
        resultado_text.insert(
            "1.0",
            "Imagen preparada para el análisis.\n\n"
            "Presioná ANALIZAR IMAGEN para comenzar."
        )
        resultado_text.configure(state="disabled")

    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se pudo abrir la imagen:\n{e}"
        )


def analizar_imagen():

    global resultado_actual

    if imagen_actual is None:
        messagebox.showwarning(
            "Atención",
            "Primero tenés que cargar una imagen."
        )
        return

    api_key = api_entry.get().strip()

    if not api_key:
        messagebox.showwarning(
            "API Key",
            "Ingresá tu clave de Gemini."
        )
        return

    boton_analizar.configure(
        state="disabled",
        text="ANALIZANDO..."
    )

    estado_label.configure(
        text="Gemini está procesando la imagen...",
        text_color=ORANGE
    )

    resultado_text.configure(state="normal")
    resultado_text.delete("1.0", "end")
    resultado_text.insert(
        "1.0",
        "Procesando imagen...\n"
        "Esto puede tardar unos segundos."
    )
    resultado_text.configure(state="disabled")

    hilo = threading.Thread(
        target=procesar_gemini,
        args=(api_key, imagen_actual.copy()),
        daemon=True
    )

    hilo.start()

def procesar_gemini(api_key, imagen):

    global resultado_actual

    try:

        texto = analizar_citologia(
            imagen=imagen,
            api_key=api_key
        )

        resultado_actual = texto

        root.after(
            0,
            mostrar_resultado,
            texto
        )

    except Exception as e:

        root.after(
            0,
            mostrar_error,
            str(e)
        )
def mostrar_resultado(texto):

    resultado_text.configure(state="normal")
    resultado_text.delete("1.0", "end")
    resultado_text.insert("1.0", texto)
    resultado_text.configure(state="disabled")

    estado_label.configure(
        text="Análisis finalizado. Requiere validación profesional.",
        text_color=GREEN
    )

    boton_analizar.configure(
        state="normal",
        text="ANALIZAR IMAGEN"
    )


def mostrar_error(error):

    estado_label.configure(
        text="Error durante el análisis",
        text_color=ORANGE
    )

    boton_analizar.configure(
        state="normal",
        text="ANALIZAR IMAGEN"
    )

    messagebox.showerror(
        "Error Gemini",
        error
    )


# ==========================================
# EXPORTAR PDF
# ==========================================


def exportar_pdf():

    if not resultado_actual:
        messagebox.showwarning(
            "Sin resultados",
            "Primero realizá un análisis con Gemini."
        )
        return

    ruta = filedialog.asksaveasfilename(
        initialdir="informes",
        initialfile="Analisis_Citologico.pdf",
        defaultextension=".pdf",
        filetypes=[
            ("Documento PDF", "*.pdf")
        ]
    )

    if not ruta:
        return

    try:

        archivo = exportar_informe(
            ruta_destino=ruta,
            resultado=resultado_actual,
            ruta_imagen=ruta_imagen
        )

        messagebox.showinfo(
            "PDF generado correctamente",
            f"El informe fue creado correctamente:\n\n{archivo}"
        )

    except Exception as error:

        messagebox.showerror(
            "Error al generar PDF",
            f"No se pudo crear el informe:\n\n{error}"
        )

# ==========================================
# DISEÑO DE INTERFAZ
# ==========================================

# ENCABEZADO

header = ctk.CTkFrame(
    root,
    fg_color=PANEL,
    corner_radius=15
)

header.pack(
    fill="x",
    padx=20,
    pady=(20, 12)
)

titulo = ctk.CTkLabel(
    header,
    text="ANALIZADOR CITOLOGICO",
    font=("Arial", 30, "bold"),
    text_color=WHITE
)

titulo.pack(
    side="left",
    padx=25,
    pady=22
)

subtitulo = ctk.CTkLabel(
    header,
    text="INTELIGENCIA ARTIFICIAL | GEMINI",
    font=("Arial", 14, "bold"),
    text_color=GREEN
)

subtitulo.pack(
    side="right",
    padx=25
)

# API KEY

api_frame = ctk.CTkFrame(
    root,
    fg_color=PANEL,
    corner_radius=12
)

api_frame.pack(
    fill="x",
    padx=20,
    pady=5
)

ctk.CTkLabel(
    api_frame,
    text="GEMINI API KEY",
    font=("Arial", 15, "bold"),
    text_color=WHITE
).pack(
    side="left",
    padx=18,
    pady=14
)

api_entry = ctk.CTkEntry(
    api_frame,
    width=450,
    height=42,
    show="*",
    placeholder_text="Pegá tu API Key de Google Gemini",
    font=("Arial", 14),
    fg_color=PANEL2,
    text_color=WHITE
)

api_entry.pack(
    side="left",
    padx=10,
    pady=10
)

# CONTENEDOR PRINCIPAL

main_frame = ctk.CTkFrame(
    root,
    fg_color=BG
)

main_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=15
)

# PANEL IZQUIERDO

left_frame = ctk.CTkFrame(
    main_frame,
    fg_color=PANEL,
    corner_radius=15,
    width=470
)

left_frame.pack(
    side="left",
    fill="both",
    padx=(0, 10),
    expand=True
)

left_frame.pack_propagate(False)

ctk.CTkLabel(
    left_frame,
    text="IMAGEN CITOLÓGICA",
    font=("Arial", 20, "bold"),
    text_color=WHITE
).pack(
    pady=(20, 12)
)

imagen_label = ctk.CTkLabel(
    left_frame,
    text="ARRASTRÁ O SELECCIONÁ UNA IMAGEN\n\n"
         "Formatos: JPG · PNG · WEBP · TIFF · BMP",
    font=("Arial", 16, "bold"),
    text_color=GRAY,
    fg_color=PANEL2,
    corner_radius=12,
    width=420,
    height=310
)

imagen_label.pack(
    padx=15,
    pady=10
)

nombre_label = ctk.CTkLabel(
    left_frame,
    text="Ninguna imagen seleccionada",
    font=("Arial", 13),
    text_color=GRAY
)

nombre_label.pack(pady=8)

boton_cargar = ctk.CTkButton(
    left_frame,
    text="SELECCIONAR IMAGEN",
    font=("Arial", 17, "bold"),
    height=50,
    fg_color=GREEN,
    hover_color="#15803D",
    text_color=WHITE,
    command=seleccionar_imagen
)

boton_cargar.pack(
    fill="x",
    padx=25,
    pady=10
)

boton_analizar = ctk.CTkButton(
    left_frame,
    text="ANALIZAR IMAGEN",
    font=("Arial", 18, "bold"),
    height=55,
    fg_color=ORANGE,
    hover_color="#EA580C",
    text_color=WHITE,
    command=analizar_imagen
)

boton_analizar.pack(
    fill="x",
    padx=25,
    pady=10
)

estado_label = ctk.CTkLabel(
    left_frame,
    text="Sistema preparado",
    font=("Arial", 13, "bold"),
    text_color=GREEN,
    wraplength=400
)

estado_label.pack(pady=15)

# PANEL DERECHO

right_frame = ctk.CTkFrame(
    main_frame,
    fg_color=PANEL,
    corner_radius=15
)

right_frame.pack(
    side="right",
    fill="both",
    expand=True
)

ctk.CTkLabel(
    right_frame,
    text="RESULTADOS DEL ANÁLISIS",
    font=("Arial", 20, "bold"),
    text_color=WHITE
).pack(
    pady=(20, 12)
)

resultado_text = ctk.CTkTextbox(
    right_frame,
    font=("Arial", 15),
    text_color=WHITE,
    fg_color=PANEL2,
    corner_radius=12,
    wrap="word",
    scrollbar_button_color=GREEN
)

resultado_text.pack(
    fill="both",
    expand=True,
    padx=18,
    pady=10
)

resultado_text.insert(
    "1.0",
    "BIENVENIDO A ANALIZADOR CITOLOGICO\n\n"
    "1. Ingresá tu API Key.\n"
    "2. Seleccioná una imagen de PAP.\n"
    "3. Presioná ANALIZAR IMAGEN.\n"
    "4. Revisá los hallazgos y sus limitaciones.\n"
    "5. Exportá el informe en PDF.\n\n"
    "El sistema no sustituye el diagnóstico profesional."
)

resultado_text.configure(state="disabled")

boton_pdf = ctk.CTkButton(
    right_frame,
    text="EXPORTAR INFORME PDF",
    font=("Arial", 17, "bold"),
    height=52,
    fg_color=GREEN,
    hover_color="#15803D",
    text_color=WHITE,
    command=exportar_pdf
)

boton_pdf.pack(
    fill="x",
    padx=18,
    pady=(10, 20)
)

# ==========================================
# INICIAR APLICACIÓN
# ==========================================

root.mainloop()
