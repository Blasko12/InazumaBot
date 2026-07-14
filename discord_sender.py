import discord

COLOR_INAZUMA = 0x009DFF


def recortar_texto(texto, limite):
    if texto is None:
        return ""

    if len(texto) <= limite:
        return texto

    return texto[:limite - 3] + "..."


def crear_embed(
    texto_original,
    texto_traducido,
    enlace,
    imagenes=None,
):
    imagenes = imagenes or []

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

    embed = discord.Embed(
        title="⚽ INAZUMA ELEVEN CROSS",
        description=descripcion,
        url=enlace,
        color=COLOR_INAZUMA
    )

    embed.set_author(
        name="📰 Nueva noticia oficial"
    )

    embed.set_footer(
        text="⚽ InazumaBot • Noticias oficiales de Inazuma Eleven Cross"
    )

    if imagenes:
        embed.set_image(url=imagenes[0])

    return embed


async def enviar_a_canal(
    canal,
    texto_original,
    texto_traducido,
    enlace,
    imagenes=None,
    videos=None,
):

    videos = videos or []

    embed = crear_embed(
        texto_original,
        texto_traducido,
        enlace,
        imagenes
    )

    contenido = "⚡ **Nueva noticia oficial de Inazuma Eleven Cross**"

    if videos:
        contenido += "\n\n🎥 **Video oficial:**\n"
        contenido += "\n".join(videos)

    await canal.send(
        content=contenido,
        embed=embed
    )