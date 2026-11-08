
import time

from google import genai
from google.genai import errors

from config import GEMINI_API_KEY, GEMINI_MODEL

from PIL import Image


PROMPT_CITOLOGICO = """
Analizá la imagen como asistencia educativa
para la revisión de citología ginecológica.

Evaluá exclusivamente estas categorías:

1. Gardnerella / vaginosis bacteriana.
2. Micosis / Candida.
3. Trichomonas vaginalis.
4. Actinomyces.

Para cada categoría indicá:

- Hallazgos morfológicos observables.
- Hallazgos compatibles.
- No identificados.
- Indeterminado o no evaluable.

ESTRUCTURA DEL INFORME:

CALIDAD DE IMAGEN:

GARDNERELLA:

MICOSIS:

TRICOMONAS:

ACTINOMYCES:

RESUMEN DE HALLAZGOS:

CONDUCTA Y PRUEBAS CONFIRMATORIAS:

LIMITACIONES:

CONCLUSIÓN:

REGLAS IMPORTANTES:

No inventes hallazgos.
No confirmes infecciones exclusivamente por fotografía.
No confundas ausencia visual con ausencia de infección.
No prescribas medicamentos ni dosis.
No diagnostiques otras enfermedades.
Si no existe evidencia suficiente, indicá indeterminado.

"""


def analizar_citologia(imagen, api_key=None):

    clave = api_key or GEMINI_API_KEY

    if not clave:
        raise ValueError("Falta la API Key de Gemini.")

    if not isinstance(imagen, Image.Image):
        raise TypeError("La imagen proporcionada no es válida.")

    cliente = genai.Client(api_key=clave)

    imagen = imagen.convert("RGB")

    max_intentos = 4

    for intento in range(max_intentos):

        try:

            respuesta = cliente.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    PROMPT_CITOLOGICO,
                    imagen
                ]
            )

            if not respuesta.text:
                raise ValueError(
                    "Gemini devolvió una respuesta vacía."
                )

            return respuesta.text

        except errors.APIError as error:

            codigo = getattr(error, "code", None)

            if codigo not in (429, 500, 502, 503, 504):
                raise

            if intento == max_intentos - 1:
                raise RuntimeError(
                    f"Gemini continúa sin estar disponible. "
                    f"Código HTTP: {codigo}. "
                    "Intentá nuevamente más tarde."
                ) from error

            espera = 2 ** (intento + 1)

            print(
                f"Gemini ocupado. "
                f"Reintento {intento + 1}/{max_intentos - 1} "
                f"en {espera} segundos."
            )

            time.sleep(espera)

    raise RuntimeError("No fue posible completar el análisis.")

