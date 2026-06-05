from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

# -------------------------
# MODELOS
# -------------------------
class TareaEntrada(BaseModel):
    titulo: str
    prioridad: str = "normal"


class ChatInput(BaseModel):
    session_id: str
    mensaje: str


# -------------------------
# "BASE DE DATOS FAKE"
# -------------------------
tareas = []


def guardar_en_db(tarea: TareaEntrada):
    nueva = {
        "id": len(tareas) + 1,
        "titulo": tarea.titulo,
        "prioridad": tarea.prioridad
    }
    tareas.append(nueva)
    return nueva


# -------------------------
# WEBHOOK N8N
# -------------------------
async def notificar_n8n(webhook_url: str, payload: dict):
    if not webhook_url:
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
    except Exception:
        pass


# -------------------------
# CREAR TAREA
# -------------------------
@app.post("/tareas")
async def crear_tarea(tarea: TareaEntrada, background_tasks: BackgroundTasks):

    nueva = guardar_en_db(tarea)

    background_tasks.add_task(
        notificar_n8n,
        os.getenv(
            "N8N_WEBHOOK_TAREAS",
            "http://localhost:5678/webhook-test/evento-tarea"
        ),
        {
            "evento": "tarea_creada",
            "tarea": nueva
        }
    )

    return {
        "ok": True,
        "data": nueva
    }


# -------------------------
# LISTAR TAREAS
# -------------------------
@app.get("/tareas")
def listar_tareas():
    return tareas


# -------------------------
# CHAT
# -------------------------
@app.post("/chat")
async def chat(data: ChatInput):
    return {
        "respuesta": f"Echo: {data.mensaje}",
        "session_id": data.session_id
    }


# -------------------------
# ROOT
# -------------------------
@app.get("/")
def root():
    return {"status": "ok"}