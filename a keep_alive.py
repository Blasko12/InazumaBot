import os
from threading import Thread

from flask import Flask


app = Flask(__name__)


@app.get("/")
def inicio():
    return {
        "bot": "InazumaBot",
        "estado": "activo",
        "mensaje": "Noticias oficiales de Inazuma Eleven Cross",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def ejecutar_servidor():
    puerto = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=puerto,
        debug=False,
        use_reloader=False,
    )


def mantener_activo():
    hilo = Thread(
        target=ejecutar_servidor,
        daemon=True,
    )
    hilo.start()