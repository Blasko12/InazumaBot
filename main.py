import json
from keep_alive import mantener_activo
from pathlib import Path

import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from discord.ext import tasks

from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_IDS,
    RSS_URL,
)
from discord_sender import enviar_a_canal
from rss import obtener_publicacion_mas_reciente


# Archivos donde se guardan los datos del bot.
CARPETA_DATA = Path(__file__).parent / "data"
ARCHIVO_ESTADO = CARPETA_DATA / "last_posts.json"
ARCHIVO_SERVIDORES = CARPETA_DATA / "servers.json"


# ==========================================================
# PUBLICACIONES GUARDADAS
# ==========================================================

def cargar_ultimo_id() -> str | None:
    """Obtiene el ID de la última publicación enviada."""

    if not ARCHIVO_ESTADO.exists():
        return None

    try:
        with ARCHIVO_ESTADO.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos.get("ultimo_id")

    except (json.JSONDecodeError, OSError):
        return None


def guardar_ultimo_id(publicacion_id: str) -> None:
    """Guarda el ID de la última publicación enviada."""

    CARPETA_DATA.mkdir(parents=True, exist_ok=True)

    with ARCHIVO_ESTADO.open("w", encoding="utf-8") as archivo:
        json.dump(
            {"ultimo_id": publicacion_id},
            archivo,
            ensure_ascii=False,
            indent=2,
        )


# ==========================================================
# SERVIDORES Y CANALES CONFIGURADOS
# ==========================================================

def cargar_servidores() -> dict:
    """Carga los canales configurados por cada servidor."""

    if not ARCHIVO_SERVIDORES.exists():
        return {}

    try:
        with ARCHIVO_SERVIDORES.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

            if isinstance(datos, dict):
                return datos

            return {}

    except (json.JSONDecodeError, OSError):
        return {}


def guardar_servidores(servidores: dict) -> None:
    """Guarda los canales configurados."""

    CARPETA_DATA.mkdir(parents=True, exist_ok=True)

    with ARCHIVO_SERVIDORES.open("w", encoding="utf-8") as archivo:
        json.dump(
            servidores,
            archivo,
            ensure_ascii=False,
            indent=2,
        )


def obtener_ids_canales_configurados() -> list[int]:
    """
    Devuelve todos los canales configurados mediante /configurar.

    También conserva los ID que todavía estén escritos en el archivo .env.
    """

    servidores = cargar_servidores()
    canales: list[int] = []

    for configuracion in servidores.values():
        channel_id = configuracion.get("channel_id")

        try:
            channel_id = int(channel_id)
        except (TypeError, ValueError):
            continue

        if channel_id not in canales:
            canales.append(channel_id)

    # Mantener temporalmente los canales configurados en .env.
    for channel_id in DISCORD_CHANNEL_IDS:
        if channel_id not in canales:
            canales.append(channel_id)

    return canales


# ==========================================================
# TRADUCCIÓN
# ==========================================================

def traducir_al_espanol(texto: str) -> str:
    """Traduce automáticamente la publicación al español."""

    try:
        traduccion = GoogleTranslator(
            source="auto",
            target="es",
        ).translate(texto)

        return traduccion or "No fue posible generar la traducción."

    except Exception as error:
        print(f"No se pudo traducir la publicación: {error}")

        return (
            "La traducción no está disponible en este momento. "
            "Puedes consultar el texto original y el enlace de X."
        )


# ==========================================================
# CLIENTE DE DISCORD
# ==========================================================

class InazumaClient(discord.Client):

    def __init__(self) -> None:
        intents = discord.Intents.default()

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.comandos_sincronizados = False

    async def setup_hook(self) -> None:
        """Se ejecuta durante la preparación del bot."""

        if not revisar_publicaciones.is_running():
            revisar_publicaciones.start()

    async def on_ready(self) -> None:
        """Se ejecuta cuando el bot termina de conectarse."""

        if not self.comandos_sincronizados:
            comandos = await self.tree.sync()
            self.comandos_sincronizados = True

            print(f"Comandos sincronizados: {len(comandos)}")

        canales = obtener_ids_canales_configurados()

        print("=" * 50)
        print(f"InazumaBot conectado como: {self.user}")
        print(f"Servidores conectados: {len(self.guilds)}")
        print(f"Canales configurados: {len(canales)}")
        print("=" * 50)


bot = InazumaClient()


# ==========================================================
# ENVÍO DE NOTICIAS
# ==========================================================

async def obtener_canal(channel_id: int):
    """Busca un canal usando su ID."""

    canal = bot.get_channel(channel_id)

    if canal is not None:
        return canal

    try:
        return await bot.fetch_channel(channel_id)

    except discord.NotFound:
        print(f"No existe el canal con ID {channel_id}")

    except discord.Forbidden:
        print(f"InazumaBot no puede acceder al canal {channel_id}")

    except discord.HTTPException as error:
        print(f"No se pudo obtener el canal {channel_id}: {error}")

    return None


async def publicar_en_canales(publicacion: dict) -> int:
    """Envía una publicación a todos los canales configurados."""

    canales = obtener_ids_canales_configurados()

    if not canales:
        print("No existen canales configurados.")
        return 0

    traduccion = traducir_al_espanol(publicacion["titulo"])
    enviados = 0

    for channel_id in canales:
        canal = await obtener_canal(channel_id)

        if canal is None:
            continue

        try:
            await enviar_a_canal(
                canal=canal,
                texto_original=publicacion["titulo"],
                texto_traducido=traduccion,
                enlace=publicacion["enlace"],
                imagenes=publicacion.get("imagenes", []),
                videos=publicacion.get("videos", []),
            )

            enviados += 1
            print(f"Publicación enviada al canal: {channel_id}")

        except discord.Forbidden:
            print(
                f"InazumaBot no tiene permiso para escribir "
                f"en el canal {channel_id}"
            )

        except discord.HTTPException as error:
            print(
                f"Discord rechazó el mensaje en el canal "
                f"{channel_id}: {error}"
            )

        except Exception as error:
            print(
                f"Error inesperado al publicar en "
                f"el canal {channel_id}: {error}"
            )

    return enviados


# ==========================================================
# REVISIÓN AUTOMÁTICA
# ==========================================================

@tasks.loop(minutes=15)
async def revisar_publicaciones() -> None:
    """Revisa cada 15 minutos si existe una noticia nueva."""

    print("Revisando el RSS...")

    try:
        publicacion = obtener_publicacion_mas_reciente(RSS_URL)

    except Exception as error:
        print(f"Error al leer el RSS: {error}")
        return

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

    enviados = await publicar_en_canales(publicacion)

    if enviados > 0:
        guardar_ultimo_id(publicacion_id)

        print(
            "Publicación registrada correctamente. "
            f"Canales alcanzados: {enviados}"
        )

    else:
        print(
            "No se guardó la publicación porque no pudo "
            "enviarse a ningún canal."
        )


@revisar_publicaciones.before_loop
async def antes_de_revisar() -> None:
    """Espera a que el bot esté conectado antes de revisar el RSS."""

    await bot.wait_until_ready()


@revisar_publicaciones.error
async def error_revisando_publicaciones(error: Exception) -> None:
    print(f"Error en la revisión automática: {error}")


# ==========================================================
# COMANDO /CONFIGURAR
# ==========================================================

@bot.tree.command(
    name="configurar",
    description="Configura este canal para recibir noticias de Inazuma Eleven.",
)
@app_commands.checks.has_permissions(administrator=True)
async def configurar(interaction: discord.Interaction) -> None:
    """Guarda el canal actual como canal de noticias del servidor."""

    if interaction.guild is None:
        await interaction.response.send_message(
            "Este comando solo puede utilizarse dentro de un servidor.",
            ephemeral=True,
        )
        return

    if interaction.channel is None:
        await interaction.response.send_message(
            "No se pudo identificar el canal actual.",
            ephemeral=True,
        )
        return

    servidores = cargar_servidores()

    servidores[str(interaction.guild.id)] = {
        "server_name": interaction.guild.name,
        "channel_id": interaction.channel.id,
        "channel_name": getattr(
            interaction.channel,
            "name",
            "canal desconocido",
        ),
    }

    guardar_servidores(servidores)

    await interaction.response.send_message(
        f"✅ {interaction.channel.mention} fue configurado para recibir "
        "las noticias de **Inazuma Eleven Cross**.",
        ephemeral=True,
    )

    print(
        f"Servidor configurado: {interaction.guild.name} | "
        f"Canal: {getattr(interaction.channel, 'name', 'desconocido')}"
    )


@configurar.error
async def configurar_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:

    if isinstance(error, app_commands.MissingPermissions):
        mensaje = "Solo un administrador puede utilizar `/configurar`."

    else:
        mensaje = f"No se pudo guardar la configuración: `{error}`"

    if interaction.response.is_done():
        await interaction.followup.send(
            mensaje,
            ephemeral=True,
        )

    else:
        await interaction.response.send_message(
            mensaje,
            ephemeral=True,
        )


# ==========================================================
# COMANDO /ESTADO
# ==========================================================

@bot.tree.command(
    name="estado",
    description="Muestra el estado actual de InazumaBot.",
)
async def estado(interaction: discord.Interaction) -> None:

    canales = obtener_ids_canales_configurados()

    canal_servidor = "No configurado"

    if interaction.guild is not None:
        servidores = cargar_servidores()
        configuracion = servidores.get(str(interaction.guild.id))

        if configuracion:
            channel_id = configuracion.get("channel_id")
            canal_servidor = f"<#{channel_id}>"

    await interaction.response.send_message(
        "⚽ **Estado de InazumaBot**\n\n"
        "Conexión con Discord: ✅\n"
        "RSS de Inazuma Eleven Cross: ✅\n"
        "Traducción al español: ✅\n"
        "Revisión automática: cada 15 minutos\n\n"
        f"Canal de este servidor: {canal_servidor}\n"
        f"Servidores conectados: `{len(bot.guilds)}`\n"
        f"Canales totales configurados: `{len(canales)}`",
        ephemeral=True,
    )


# ==========================================================
# COMANDO /PROBAR
# ==========================================================

@bot.tree.command(
    name="probar",
    description="Publica la noticia más reciente como prueba.",
)
@app_commands.checks.has_permissions(administrator=True)
async def probar(interaction: discord.Interaction) -> None:

    await interaction.response.defer(ephemeral=True)

    try:
        publicacion = obtener_publicacion_mas_reciente(RSS_URL)

    except Exception as error:
        await interaction.followup.send(
            f"No se pudo consultar el RSS: `{error}`",
            ephemeral=True,
        )
        return

    if not publicacion:
        await interaction.followup.send(
            "No se pudo obtener ninguna publicación.",
            ephemeral=True,
        )
        return

    if interaction.channel is None:
        await interaction.followup.send(
            "No se pudo identificar este canal.",
            ephemeral=True,
        )
        return

    traduccion = traducir_al_espanol(publicacion["titulo"])

    try:
        await enviar_a_canal(
            canal=interaction.channel,
            texto_original=publicacion["titulo"],
            texto_traducido=traduccion,
            enlace=publicacion["enlace"],
            imagenes=publicacion.get("imagenes", []),
            videos=publicacion.get("videos", []),
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "InazumaBot no tiene permiso para publicar en este canal.",
            ephemeral=True,
        )
        return

    except discord.HTTPException as error:
        await interaction.followup.send(
            f"Discord rechazó la publicación: `{error}`",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        "✅ Publicación de prueba enviada correctamente.",
        ephemeral=True,
    )


@probar.error
async def probar_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:

    if isinstance(error, app_commands.MissingPermissions):
        mensaje = "Solo un administrador puede utilizar `/probar`."

    else:
        mensaje = f"No se pudo ejecutar la prueba: `{error}`"

    if interaction.response.is_done():
        await interaction.followup.send(
            mensaje,
            ephemeral=True,
        )

    else:
        await interaction.response.send_message(
            mensaje,
            ephemeral=True,
        )


# ==========================================================
# INICIAR EL BOT
# ==========================================================

if not DISCORD_BOT_TOKEN:
    raise RuntimeError(
        "Falta DISCORD_BOT_TOKEN en el archivo .env"
    )

if not RSS_URL:
    raise RuntimeError(
        "Falta RSS_URL en el archivo .env"
    )

mantener_activo()
bot.run(DISCORD_BOT_TOKEN)
