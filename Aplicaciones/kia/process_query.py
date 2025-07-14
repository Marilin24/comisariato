import openai
import os
import json
from dotenv import load_dotenv

# Cargar las variables del .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def process_query(user_message):
    """
    Genera una consulta SQL y sugerencias desde el mensaje del usuario utilizando OpenAI.
    Devuelve la consulta SQL, el tipo de respuesta y una lista de sugerencias.
    """
    # PROMPT para consulta SQL
    prompt_sql = f"""
Eres un asistente SQL experto. Convierte esta pregunta en una consulta SQL para una base de datos MySQL:

Base de datos:
- pedido(idpedido, monto, fecha, personaid)
- detalle_pedido(id,pedidoid, productoid, cantidad, precio)
- producto(idproducto, nombre, stock, fecha_caducidad, categoriaid)
- categoria(idcategoria, nombre, status)
- persona(idpersona, nombres, apellidos, email_user, estado, datecreated)
- reembolso(id, pedidoid)
- modulo(idmodulo, titulo, descripcion, status)
- permisos(idpermiso, rolid, moduloid, r, w, u, d)
- tipopago(idtipopago, tipopago, status)
- suscripciones(idsuscripcion)

Devuelve solo la consulta SQL sin explicaciones.

Pregunta del usuario: \"{user_message}\"

SQL:
"""

    # PROMPT para sugerencias
    prompt_sugerencias = f"""
A partir de esta pregunta del usuario: \"{user_message}\"

Sugiere 3 preguntas relacionadas que podrían interesarle, en formato JSON así:
[
  "¿Qué productos tienen bajo stock?",
  "¿Cuántas unidades se han vendido esta semana?",
  "¿Cuál es el producto más vendido?"
]
"""

    try:
        # Generar la consulta SQL
        response_sql = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_sql}],
            temperature=0
        )
        sql_query = response_sql.choices[0].message.content.strip()

        # Generar sugerencias relacionadas
        response_sugerencias = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_sugerencias}],
            temperature=0.7
        )
        sugerencias_raw = response_sugerencias.choices[0].message.content.strip()

        try:
            sugerencias = json.loads(sugerencias_raw)
        except:
            # Si el formato JSON falla, devuélvelo como texto
            sugerencias = [sugerencias_raw]

        return sql_query, "respuesta_generada_por_llm", sugerencias

    except openai.error.OpenAIError as e:
        return f"Error de la API de OpenAI: {str(e)}", "error", []
    except Exception as e:
        return f"-- Error: {str(e)}", "error", []
