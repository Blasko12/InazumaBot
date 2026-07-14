import json
from pathlib import Path

from deep_translator import GoogleTranslator

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


def traducir_al_espanol(texto):
    try:
        traduccion = GoogleTranslator(
            source="auto",
            target="es"
        ).translate(texto)

        return traduccion or "No fue posible generar la traducción."
    except Exception as error:
        print("No se pudo traducir:", error)
        return "La traducción no estuvo disponible en este momento."


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
    publicacion_id = publicacion["id"]

    print("ID guardado:", repr(ultimo_id))
    print("ID encontrado:", repr(publicacion_id))

    if ultimo_id == publicacion_id:
        print("No hay publicaciones nuevas.")
        return

    print("Nueva publicación detectada.")
    print("Traduciendo al español...")

    traduccion = traducir_al_espanol(publicacion["titulo"])

    print("Imágenes encontradas:", len(publicacion["imagenes"]))
    print("Videos encontrados:", len(publicacion["videos"]))

    enviar_publicacion(
        webhook_url=DISCORD_WEBHOOK,
        nombre_cuenta=publicacion["nombre_feed"],
        texto_original=publicacion["titulo"],
        texto_traducido=traduccion,
        enlace=publicacion["enlace"],
        imagenes=publicacion["imagenes"],
        videos=publicacion["videos"]
    )

    guardar_ultimo_id(publicacion_id)

    print("Publicación traducida, enviada y registrada correctamente.")


if __name__ == "__main__":
    main()