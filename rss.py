import feedparser


def obtener_publicacion_mas_reciente(rss_url):
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return None

    entrada = feed.entries[0]

    enlace = entrada.get("link", "").strip()

    imagen_url = None
    media = entrada.get("media_content", [])

    if media:
        imagen_url = media[0].get("url")

    return {
        # Usamos el enlace como ID estable.
        "id": enlace,
        "titulo": entrada.get("title", "Nueva publicación"),
        "enlace": enlace,
        "fecha": entrada.get("published", ""),
        "imagen": imagen_url,
        "nombre_feed": feed.feed.get("title", "Cuenta de X")
    }