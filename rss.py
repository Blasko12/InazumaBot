import feedparser


def obtener_publicacion_mas_reciente(rss_url):
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return None

    entrada = feed.entries[0]

    enlace = entrada.get("link", "").strip()
    imagenes = []
    videos = []

    for medio in entrada.get("media_content", []):
        url = medio.get("url", "").strip()
        tipo = medio.get("type", "").lower()
        medium = medio.get("medium", "").lower()

        if not url:
            continue

        if (
            medium == "video"
            or tipo.startswith("video/")
            or url.lower().endswith((".mp4", ".webm", ".mov"))
        ):
            videos.append(url)

        elif (
            medium == "image"
            or tipo.startswith("image/")
            or url.lower().endswith(
                (".jpg", ".jpeg", ".png", ".gif", ".webp")
            )
        ):
            imagenes.append(url)

    for archivo in entrada.get("enclosures", []):
        url = (
            archivo.get("href")
            or archivo.get("url")
            or ""
        ).strip()

        tipo = archivo.get("type", "").lower()

        if not url:
            continue

        if (
            tipo.startswith("video/")
            or url.lower().endswith((".mp4", ".webm", ".mov"))
        ):
            videos.append(url)

        elif (
            tipo.startswith("image/")
            or url.lower().endswith(
                (".jpg", ".jpeg", ".png", ".gif", ".webp")
            )
        ):
            imagenes.append(url)

    imagenes = list(dict.fromkeys(imagenes))
    videos = list(dict.fromkeys(videos))

    return {
        "id": enlace,
        "titulo": entrada.get(
            "title",
            "Nueva publicación"
        ).strip(),
        "enlace": enlace,
        "fecha": entrada.get("published", ""),
        "imagenes": imagenes,
        "videos": videos,
        "nombre_feed": feed.feed.get(
            "title",
            "Cuenta de X"
        )
    }