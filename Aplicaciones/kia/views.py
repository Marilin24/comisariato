from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import mysql.connector
import os
from dotenv import load_dotenv
import openai # Importar la librería de OpenAI

# Cargar las variables del .env al inicio de este archivo
load_dotenv()

# Configurar la clave de la API de OpenAI (asegúrate de que esté en tu .env)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Importar la función process_query desde el mismo directorio de la app
from .process_query import process_query 

# --- Configuración de la Base de Datos MySQL usando variables de entorno ---
DB_CONFIG = {
    'host': os.getenv("DATABASE_HOST", "localhost"),
    'user': os.getenv("DATABASE_USER", "root"),
    'password': os.getenv("DATABASE_PASSWORD", "root"), # Cadena vacía para sin contraseña
    'database': os.getenv("DATABASE_NAME", "comisariato_kia"),
    'port': int(os.getenv("DATABASE_PORT", 3306))
}

@csrf_exempt # Desactiva la protección CSRF para esta vista (solo para desarrollo/pruebas rápidas)
             # En producción, usa un token CSRF en el frontend.
def chatbot_view(request):
    """
    Vista principal del chatbot que procesa las solicitudes del usuario.
    1. Recibe el mensaje del usuario.
    2. Genera una consulta SQL usando la LLM (process_query).
    3. Ejecuta la consulta SQL en la base de datos.
    4. Envía los resultados de la DB de vuelta a la LLM para generar una respuesta amigable.
    5. Devuelve la respuesta amigable al frontend.
    """
    db_connection = None
    db_cursor = None

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('mensaje', '').strip() # Obtener y limpiar el mensaje del usuario

            if not user_message:
                return JsonResponse({'error': 'Mensaje vacío'}, status=400)

            # Paso 1: Generar la consulta SQL usando process_query (LLM)
            sql_query, query_type = process_query(user_message)

            # Si hay un error en la generación de la consulta SQL por parte de la LLM
            if query_type == "error":
                return JsonResponse({
                    'mensaje_usuario': user_message,
                    'tipo_respuesta': 'error_llm',
                    'respuesta_bot': sql_query # Aquí sql_query contiene el mensaje de error de la LLM
                }, status=200) # Devolver 200 OK para que el frontend muestre el error de forma amigable

            db_results = []
            column_names = []
            db_operation_status = "No ejecutado"
            final_bot_response = "" # Variable para la respuesta final del bot

            try:
                # Paso 2: Establecer conexión a la base de datos MySQL
                db_connection = mysql.connector.connect(**DB_CONFIG)
                db_cursor = db_connection.cursor()

                # Paso 3: Ejecutar la consulta SQL
                # ADVERTENCIA DE SEGURIDAD: La ejecución directa de SQL generada por LLM
                # puede ser vulnerable a inyección SQL. Para producción, considera:
                # - Validar/sanitizar la SQL generada.
                # - Usar un ORM (Django ORM) y que la LLM genere "intenciones" que tu ORM procese.
                db_cursor.execute(sql_query)

                # Paso 4: Determinar el tipo de consulta y procesar los resultados
                if sql_query.strip().upper().startswith("SELECT"):
                    if db_cursor.description: # Solo si la consulta devuelve columnas
                        column_names = [i[0] for i in db_cursor.description] 
                    
                    rows = db_cursor.fetchall() # Obtener todas las filas
                    
                    # Formatear los resultados como una lista de diccionarios para facilitar el JSON
                    for row in rows:
                        db_results.append(dict(zip(column_names, row)))
                    db_operation_status = "Datos recuperados"

                    # Paso 5: Enviar los resultados de la DB de vuelta a ChatGPT para una respuesta amigable
                    prompt_for_final_response = f"""
                    El usuario preguntó: "{user_message}"
                    Los datos obtenidos de la base de datos son los siguientes (formato JSON):
                    {json.dumps(db_results, indent=2, default=str)} 
                    
                    Basado en la pregunta del usuario y estos datos, genera una respuesta clara, concisa y amigable en español.
                    Si los datos son sobre ingresos o precios, formatea los montos como moneda (ej. $123.45).
                    Si los datos son una lista de elementos, preséntalos de forma estructurada (ej. lista con viñetas o tabla simple).
                    Si no hay datos, indica que no se encontraron.
                    No incluyas la consulta SQL en tu respuesta final.
                    
                    Ejemplos de respuestas deseadas:
                    - "Ingresos totales: $1092.00"
                    - "Producto más vendido: Manzanas (80 unidades)"
                    - "Ingresos por categoría: Naturales: $277.00, Temporada: $185.00"
                    - "No se encontraron productos en stock."
                    """
                    
                    response_final = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", # Puedes usar gpt-4 si tienes acceso
                        messages=[
                            {"role": "system", "content": "Eres un asistente amigable que resume datos de la base de datos para el usuario."},
                            {"role": "user", "content": prompt_for_final_response}
                        ],
                        temperature=0.5 # Un poco más de creatividad para la respuesta final
                    )
                    final_bot_response = response_final.choices[0].message.content.strip()

                else:
                    # Para INSERT, UPDATE, DELETE, etc., confirmamos los cambios
                    db_connection.commit()
                    db_operation_status = f"Operación DML ejecutada. Filas afectadas: {db_cursor.rowcount}"
                    final_bot_response = f"La operación de base de datos se ejecutó exitosamente. Filas afectadas: {db_cursor.rowcount}."

            except mysql.connector.Error as err:
                db_operation_status = f"Error de base de datos: {err.msg}"
                print(f"Error de base de datos: {err}")
                final_bot_response = f"Lo siento, hubo un problema al obtener datos de la base de datos: {err.msg}"
            except openai.error.OpenAIError as err:
                db_operation_status = f"Error de la API de OpenAI al generar respuesta final: {err}"
                print(f"Error de la API de OpenAI: {err}")
                final_bot_response = f"Lo siento, no pude generar una respuesta amigable. Error de la IA: {err}"
            except Exception as err:
                db_operation_status = f"Error inesperado en DB: {str(err)}"
                print(f"Error inesperado en DB: {err}")
                final_bot_response = f"Ocurrió un error inesperado al procesar tu solicitud: {str(err)}"
            finally:
                # Asegurarse de cerrar el cursor y la conexión
                if db_cursor:
                    db_cursor.close()
                if db_connection and db_connection.is_connected():
                    db_connection.close()
                    print("Conexión a la base de datos MySQL cerrada.")

            # Paso 6: Devolver la respuesta final del bot al frontend
            return JsonResponse({
                'mensaje_usuario': user_message,
                'tipo_respuesta': 'respuesta_final_llm', # Indica que esta es la respuesta final formateada
                'respuesta_bot': final_bot_response, # La respuesta amigable para el usuario
                'consulta_sql_generada': sql_query, # Opcional: para depuración
                'estado_db_interno': db_operation_status, # Opcional: para depuración
                'resultados_db_crudos': db_results # Opcional: para depuración
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error general en la vista: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def plantilla(request):
    """
    Renderiza la plantilla HTML del chatbot.
    """
    return render(request, "chatbot.html")

