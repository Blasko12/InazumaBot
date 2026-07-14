import requests


def enviar_publicacion(webhook_url, nombre_cuenta, texto, enlace, imagen_url=None):
    embed = {
        "author": {
            "name": nombre_cuenta
        },
        "description": texto[:4000],
        "url": enlace,
        "footer": {
            "text": "Publicado automáticamente por InazumaBot"
        }
    }

    if imagen_url:
        embed["image"] = {
            "url": imagen_url
        }

    payload = {
        "username": "InazumaBot",
        "content": f"⚡ **Nueva publicación de {nombre_cuenta}**",
        "embeds": [embed]
    }

    respuesta = requests.post(
        webhook_url,
        json=payload,
        timeout=30
    )

    respuesta.raise_for_status()