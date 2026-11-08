
import os
import re
import html
from io import BytesIO
from datetime import datetime

from PIL import Image as PILImage, ImageOps

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
    KeepTogether
)


# ==========================================
# CONFIGURACIÓN VISUAL
# ==========================================

AZUL = colors.HexColor("#172B4D")
VERDE = colors.HexColor("#16834A")
NARANJA = colors.HexColor("#F07824")
GRIS = colors.HexColor("#596579")
GRIS_CLARO = colors.HexColor("#F1F4F7")
BLANCO = colors.white


# ==========================================
# FUENTES
# ==========================================

def registrar_fuentes():

    ruta_normal = r"C:\Windows\Fonts\arial.ttf"
    ruta_negrita = r"C:\Windows\Fonts\arialbd.ttf"

    if os.path.exists(ruta_normal) and os.path.exists(ruta_negrita):

        pdfmetrics.registerFont(
            TTFont("ArialCustom", ruta_normal)
        )

        pdfmetrics.registerFont(
            TTFont("ArialCustomBold", ruta_negrita)
        )

        return "ArialCustom", "ArialCustomBold"

    return "Helvetica", "Helvetica-Bold"


# ==========================================
# ESTILOS
# ==========================================

def crear_estilos():

    fuente, fuente_bold = registrar_fuentes()

    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name="TituloPrincipal",
        fontName=fuente_bold,
        fontSize=21,
        leading=26,
        alignment=TA_CENTER,
        textColor=AZUL,
        spaceAfter=5
    ))

    estilos.add(ParagraphStyle(
        name="Subtitulo",
        fontName=fuente,
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=GRIS,
        spaceAfter=12
    ))

    estilos.add(ParagraphStyle(
        name="Seccion",
        fontName=fuente_bold,
        fontSize=12,
        leading=16,
        textColor=VERDE,
        spaceBefore=12,
        spaceAfter=7
    ))

    estilos.add(ParagraphStyle(
        name="ContenidoPDF",
        fontName=fuente,
        fontSize=9.5,
        leading=14,
        textColor=AZUL,
        alignment=TA_LEFT,
        spaceAfter=6,
        wordWrap="LTR"
    ))

    estilos.add(ParagraphStyle(
        name="Aviso",
        fontName=fuente,
        fontSize=8,
        leading=12,
        textColor=GRIS
    ))

    return estilos


# ==========================================
# PIE DE PÁGINA
# ==========================================

def dibujar_pie(canvas, doc):

    canvas.saveState()

    ancho, alto = A4

    canvas.setStrokeColor(colors.HexColor("#D9E0E7"))

    canvas.line(
        2 * cm,
        1.55 * cm,
        ancho - 2 * cm,
        1.55 * cm
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)

    canvas.drawString(
        2 * cm,
        1.1 * cm,
        "ANALIZADOR CITOLOGICO | Informe orientativo"
    )

    canvas.drawRightString(
        ancho - 2 * cm,
        1.1 * cm,
        f"Página {doc.page}"
    )

    canvas.restoreState()


# ==========================================
# FORMATEAR RESULTADOS
# ==========================================

def agregar_resultados(texto, estilos):

    elementos = []

    secciones = {
        "CALIDAD DE IMAGEN",
        "GARDNERELLA",
        "MICOSIS",
        "TRICOMONAS",
        "ACTINOMYCES",
        "POSIBLES COMBINACIONES",
        "COMBINACIONES",
        "RESUMEN",
        "RESUMEN DE HALLAZGOS",
        "CONDUCTA",
        "CONDUCTA Y PRUEBAS CONFIRMATORIAS",
        "LIMITACIONES",
        "CONCLUSIÓN",
        "CONCLUSION"
    }

    for linea in texto.splitlines():

        linea = linea.strip()

        if not linea:
            elementos.append(Spacer(1, 4))
            continue

        # Detectar encabezados
        titulo = linea.rstrip(":").strip().upper()

        if titulo in secciones:

            elementos.append(
                Paragraph(
                    html.escape(titulo),
                    estilos["Seccion"]
                )
            )

        else:

            # Resaltar etiquetas al comienzo de una línea
            partes = re.match(
                r"^([^:]{1,55}:)\s*(.*)$",
                linea
            )

            if partes:

                contenido = (
                    f"<b>{html.escape(partes.group(1))}</b> "
                    f"{html.escape(partes.group(2))}"
                )

            else:

                contenido = html.escape(linea)

            elementos.append(
                Paragraph(
                    contenido,
                    estilos["ContenidoPDF"]
                )
            )

    return elementos


# ==========================================
# GENERAR INFORME PDF
# ==========================================

def exportar_informe(
    ruta_destino,
    resultado,
    ruta_imagen=None
):

    if not resultado or not resultado.strip():

        raise ValueError(
            "No hay resultados para generar el PDF."
        )

    carpeta = os.path.dirname(ruta_destino)

    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    estilos = crear_estilos()

    doc = SimpleDocTemplate(
        ruta_destino,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.1 * cm,
        title="Analizador Citologico",
        author="Analizador Citologico"
    )

    elementos = []

    # --------------------------------------
    # ENCABEZADO
    # --------------------------------------

    elementos.append(
        Paragraph(
            "ANALIZADOR CITOLOGICO",
            estilos["TituloPrincipal"]
        )
    )

    elementos.append(
        Paragraph(
            "INFORME DE EVALUACIÓN CITOLÓGICA ORIENTATIVA",
            estilos["Subtitulo"]
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=VERDE,
            spaceAfter=15
        )
    )

    # --------------------------------------
    # INFORMACIÓN DEL ESTUDIO
    # --------------------------------------

    fecha = datetime.now().strftime(
        "%d/%m/%Y - %H:%M"
    )

    nombre_imagen = (
        os.path.basename(ruta_imagen)
        if ruta_imagen
        else "No proporcionada"
    )

    datos = [
        [
            Paragraph("<b>FECHA DEL INFORME</b>", estilos["ContenidoPDF"]),
            Paragraph(html.escape(fecha), estilos["ContenidoPDF"])
        ],
        [
            Paragraph("<b>IMAGEN ANALIZADA</b>", estilos["ContenidoPDF"]),
            Paragraph(html.escape(nombre_imagen), estilos["ContenidoPDF"])
        ],
        [
            Paragraph("<b>TIPO DE ESTUDIO</b>", estilos["ContenidoPDF"]),
            Paragraph("Citología ginecológica - PAP", estilos["ContenidoPDF"])
        ]
    ]

    tabla = Table(
        datos,
        colWidths=[5 * cm, 11 * cm]
    )

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9E0E7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 15))

    # --------------------------------------
    # IMAGEN ORIGINAL
    # --------------------------------------

    if ruta_imagen and os.path.isfile(ruta_imagen):

        elementos.append(
            Paragraph(
                "IMAGEN CITOLÓGICA ANALIZADA",
                estilos["Seccion"]
            )
        )

        with PILImage.open(ruta_imagen) as original:

            imagen = ImageOps.exif_transpose(original)
            imagen = imagen.convert("RGB")
            imagen.thumbnail((1400, 1400))

            buffer = BytesIO()

            imagen.save(
                buffer,
                format="JPEG",
                quality=90
            )

            buffer.seek(0)

            foto_pdf = Image(
                buffer,
                width=15 * cm,
                height=10 * cm,
                kind="proportional"
            )

            foto_pdf.hAlign = "CENTER"

            elementos.append(
                KeepTogether([
                    foto_pdf,
                    Spacer(1, 12)
                ])
            )

    # --------------------------------------
    # RESULTADOS
    # --------------------------------------

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#D9E0E7"),
            spaceAfter=8
        )
    )

    elementos.append(
        Paragraph(
            "RESULTADOS DEL ANÁLISIS",
            estilos["Seccion"]
        )
    )

    elementos.extend(
        agregar_resultados(resultado, estilos)
    )

    # --------------------------------------
    # AVISO MÉDICO
    # --------------------------------------

    elementos.append(Spacer(1, 15))

    aviso = Table(
        [[
            Paragraph(
                "<b>IMPORTANTE - ALCANCE DEL INFORME</b><br/><br/>"
                "Este documento contiene una interpretación "
                "asistida por inteligencia artificial. No constituye "
                "un diagnóstico médico definitivo. Los hallazgos "
                "requieren evaluación por un profesional y, cuando "
                "corresponda, pruebas de laboratorio confirmatorias. "
                "No debe utilizarse para iniciar tratamientos "
                "sin indicación profesional.",
                estilos["Aviso"]
            )
        ]],
        colWidths=[16 * cm]
    )

    aviso.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.8, NARANJA),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12)
    ]))

    elementos.append(aviso)

    # --------------------------------------
    # CONSTRUIR PDF
    # --------------------------------------

    doc.build(
        elementos,
        onFirstPage=dibujar_pie,
        onLaterPages=dibujar_pie
    )

    return ruta_destino
