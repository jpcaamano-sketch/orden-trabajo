"""Servicio IA — transcripción y parseo de audio con Gemini."""

import json
from google import genai
from google.genai import types
from .config import GOOGLE_API_KEY

_PROMPT = """Eres un asistente para solicitudes de trabajo de mantenimiento y servicios.
Recibes un audio donde alguien describe los trabajos que necesita realizar.

Tu tarea:
1. Transcribir el audio en español
2. Identificar los participantes mencionados (personas presentes o nombradas)
3. Identificar cada trabajo mencionado
4. Para cada trabajo: extraer descripción, ubicación (si se menciona) y categoría más adecuada

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, con esta estructura exacta:
{
  "transcripcion": "texto completo transcrito del audio",
  "notas": "resumen general de la solicitud en 1-2 oraciones",
  "participantes": "nombres separados por coma, o vacío si no se mencionan",
  "trabajos": [
    {
      "descripcion": "descripción clara del trabajo a realizar",
      "ubicacion": "dónde se realiza (puede ser vacío si no se menciona)",
      "categoria_sugerida": "Mantención|Instalación|Reparación|Inspección|Limpieza|Otro"
    }
  ]
}

Reglas:
- Si solo hay un trabajo, el array tiene un elemento
- Si hay varios trabajos distintos, incluye uno por elemento
- La categoria_sugerida debe ser EXACTAMENTE una de las opciones listadas
- Si la ubicación no se menciona, deja el campo vacío ""
- Si no se mencionan participantes, deja participantes como ""
"""


def transcribir_y_parsear(audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
    """Transcribe audio y parsea en estructura de solicitud usando Gemini 2.0 Flash."""
    client = genai.Client(api_key=GOOGLE_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            _PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)
