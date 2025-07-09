import openai
import os
from dotenv import load_dotenv

# Cargar las variables del .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def process_query(user_message):
    """
    Genera una consulta SQL a partir del mensaje del usuario utilizando la API de OpenAI.
    Devuelve la consulta SQL y un tipo de respuesta ('respuesta_generada_por_llm' o 'error').
    """
    prompt = f"""
Eres un asistente SQL experto. Conviertes preguntas en lenguaje natural a consultas SQL para una base de datos MySQL.

Base de datos:
- pedido(idpedido, monto, fecha, personaid)
- detalle_pedido(id, productoid, cantidad, precio)
- producto(idproducto, nombre, stock, fecha_caducidad, categoriaid)
- categoria(idcategoria, nombre, status)
- persona(idpersona, nombres, apellidos, email_user, estado, datecreated)
- reembolso(id, pedidoid)
- modulo(idmodulo, titulo, descripcion, status)
- permisos(idpermiso, rolid, moduloid, r, w, u, d)
- tipopago(idtipopago, tipopago, status)
- suscripciones(idsuscripcion)

Devuelve solo la consulta SQL. No expliques nada.

Usuario: \"{user_message}\"

SQL:
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # puedes usar gpt-3.5-turbo si no tienes acceso a gpt-4
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        sql_query = response.choices[0].message.content.strip()
        return sql_query, "respuesta_generada_por_llm"
    
    except openai.error.OpenAIError as e:
        # Manejo de errores específicos de OpenAI (ej. cuota excedida, clave inválida)
        return f"Error de la API de OpenAI: {str(e)}", "error"
    except Exception as e:
        return f"-- Error: {str(e)}", "error"
