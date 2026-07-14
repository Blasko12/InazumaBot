import requests


def recortar_texto(texto, limite):
    if texto is None:
        return ""

    if len(texto) <= limite:
        return texto

    return texto[:limite - 3] + "..."


def enviar_publicacion(
    webhook_url,
    nombre_cuenta,
    texto_original,
    texto_traducido,
    enlace,
    imagenes=None,
    videos=None
):
    imagenes = imagenes or []
    videos = videos or []

    descripcion = (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "**📝 Publicación original**\n\n"

        f"{recortar_texto(texto_original,1800)}"

        "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "**🌎 Traducción al español**\n\n"

        f"{recortar_texto(texto_traducido,1800)}"

        "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"🔗 **[Ver publicación original en X]({enlace})**"
    )

    embed = {
        "title": "⚽ INAZUMA ELEVEN CROSS",
        "description": descripcion,

        "url": enlace,

        # Azul Inazuma
        "color": 0x009DFF,

        "author": {
            "name": "📰 Nueva noticia oficial"
        },

        "footer": {
            "text": "⚽ InazumaBot • Noticias oficiales de Inazuma Eleven Cross"
        }
    }

    if imagenes:
        embed["image"] = {
            "url": imagenes[0]
        }

    contenido = "⚡ **Nueva noticia oficial de Inazuma Eleven Cross**"

    if videos:
        contenido += "\n\n🎥 **Video oficial:**\n"
        contenido += "\n".join(videos)

    payload = {
        "username": "InazumaBot",

        "content": contenido,

        "embeds": [embed]
    }

    respuesta = requests.post(
        webhook_url,
        json=payload,
        timeout=30
    )

    respuesta.raise_for_status()