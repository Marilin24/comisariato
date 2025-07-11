from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import mysql.connector
import os
from dotenv import load_dotenv
import openai
from .process_query import process_query

# Cargar variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuración base de datos
DB_CONFIG = {
    'host': os.getenv("DATABASE_HOST", "localhost"),
    'user': os.getenv("DATABASE_USER", "root"),
    'password': os.getenv("DATABASE_PASSWORD", ""),
    'database': os.getenv("DATABASE_NAME", "comisariato_kia"),
    'port': int(os.getenv("DATABASE_PORT", 3306))
}

@csrf_exempt
def chatbot_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message') or data.get('mensaje', '')
        user_message = user_message.strip()

        if not user_message:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)

        sql_query, tipo = process_query(user_message)

        if tipo == "error":
            return JsonResponse({
                'respuesta_bot': sql_query,
                'tipo_respuesta': 'error_llm',
                'mensaje_usuario': user_message,
            })

        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            cursor.execute(sql_query)

            if sql_query.strip().upper().startswith("SELECT"):
                column_names = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                data_rows = [dict(zip(column_names, row)) for row in rows]

                prompt = f"""
                El usuario preguntó: "{user_message}"
                Resultado de la base de datos:
                {json.dumps(data_rows, indent=2, default=str)}

                Crea una respuesta clara y en español. Usa listas o tablas si es posible.
                """

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un asistente amigable de datos MySQL."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )

                texto = response.choices[0].message.content.strip()
            else:
                connection.commit()
                texto = f"La consulta se ejecutó correctamente. Filas afectadas: {cursor.rowcount}."

        except mysql.connector.Error as db_err:
            texto = f"❌ Error en la base de datos: {db_err.msg}"

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return JsonResponse({
            'respuesta_bot': texto,
            'consulta_sql_generada': sql_query
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error general: {str(e)}'}, status=500)

def plantilla(request):
    return render(request, "chatbot.html")
