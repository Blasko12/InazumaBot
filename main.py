import json
from pathlib import Path

from config import DISCORD_WEBHOOK, RSS_URL
from rss import obtener_publicacion_mas_reciente
from discord_sender import enviar_publicacion


ARCHIVO_ESTADO = Path(__file__).parent / "data" / "last_posts.json"


def cargar_ultimo_id():
    if not ARCHIVO_ESTADO.exists():
        return None

    try:
        with ARCHIVO_ESTADO.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos.get("ultimo_id")
    except (json.JSONDecodeError, OSError):
        return None


def guardar_ultimo_id(publicacion_id):
    ARCHIVO_ESTADO.parent.mkdir(parents=True, exist_ok=True)

    with ARCHIVO_ESTADO.open("w", encoding="utf-8") as archivo:
        json.dump(
            {"ultimo_id": publicacion_id},
            archivo,
            ensure_ascii=False,
            indent=2
        )


def main():
    if not DISCORD_WEBHOOK:
        print("Falta DISCORD_WEBHOOK en el archivo .env")
        return

    if not RSS_URL:
        print("Falta RSS_URL en el archivo .env")
        return

    publicacion = obtener_publicacion_mas_reciente(RSS_URL)

    if not publicacion:
        print("No se encontraron publicaciones.")
        return

    ultimo_id = cargar_ultimo_id()
    publicacion_id = publicacion["enlace"].strip()

    print("ID guardado:", repr(ultimo_id))
    print("ID encontrado:", repr(publicacion_id))

    if ultimo_id == publicacion_id:
        print("No hay publicaciones nuevas.")
        return

    print("Nueva publicación detectada.")

    enviar_publicacion(
        webhook_url=DISCORD_WEBHOOK,
        nombre_cuenta=publicacion["nombre_feed"],
        texto=publicacion["titulo"],
        enlace=publicacion["enlace"],
        imagen_url=publicacion["imagen"]
    )

    guardar_ultimo_id(publicacion_id)

    print("Publicación enviada y registrada correctamente.")


if __name__ == "__main__":
    main()