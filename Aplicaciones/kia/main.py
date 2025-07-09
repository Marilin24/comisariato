
import json
from flask import app
from openai import BaseModel
from Aplicaciones.kia.views import build_answer, human_query_to_sql, query


class PostHumanQueryPayload(BaseModel):
    human_query: str


class PostHumanQueryResponse(BaseModel):
    result: list


@app.post(
    "/human_query",
    name="Human Query",
    operation_id="post_human_query",
    description="Gets a natural language query, internally transforms it to a SQL query, queries the database, and returns the result.",
)
async def human_query(payload: PostHumanQueryPayload):

    # Transforma la pregunta a sentencia SQL
    sql_query = await human_query_to_sql(payload.human_query)

    if not sql_query:
        return {"error": "Falló la generación de la consulta SQL"}
    result_dict = json.loads(sql_query)

    # Hace la consulta a la base de datos
    result = await query(result_dict["sql_query"])

    # Transforma la respuesta SQL a un formato más humano
    answer = await build_answer(result, payload.human_query)
    if not answer:
        return {"error": "Falló la generación de la respuesta"}

    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
