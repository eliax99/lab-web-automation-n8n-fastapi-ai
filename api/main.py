from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

tareas_db = []

class TareaEntrada(BaseModel):
    titulo: str
    prioridad: str
    descripcion: str | None = None


async def notificar_n8n(webhook_url: str, payload: dict):
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
    except:
        pass


@app.post("/tareas", status_code=201)
async def crear_tarea(tarea: TareaEntrada, background_tasks: BackgroundTasks):

    nueva = tarea.model_dump()
    nueva["id"] = len(tareas_db) + 1
    tareas_db.append(nueva)

    background_tasks.add_task(
        notificar_n8n,
        os.getenv("N8N_WEBHOOK_TAREAS", ""),
        {"evento": "tarea_creada", "tarea": nueva}
    )

    return {"ok": True, "data": nueva}


@app.get("/tareas")
def get_tareas():
    return tareas_db