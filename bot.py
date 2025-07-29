import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import pytz

from config import (
    TOKEN,
    CHANNEL_ID,
    UPDATE_INTERVAL,
    UNKNOWN_SERVERS,
    LALO_SERVERS,
    SIR_PLEASE_SERVERS,
    HEIZEMOD_SERVERS,
)

from query import consultar_server

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

mensaje_unknown = None
mensaje_lalo = None
mensaje_sir = None
mensaje_heize = None
mensaje_hora = None  # ✅ mensaje con la hora

# URL de imágenes por tipo de servidor
IMAGES = {
    "Unknown Servers": "https://imgur.com/a/VTa9jmO",
    "LALO HLZ": "https://imgur.com/a/BrJjvWE",
    "Sir Please": "https://imgur.com/a/XuuMGT2",
    "Heizemod": "https://imgur.com/a/8Ymw2Py",
}

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    canal = bot.get_channel(CHANNEL_ID)

    global mensaje_unknown, mensaje_lalo, mensaje_sir, mensaje_heize, mensaje_hora
    if mensaje_unknown is None:
        mensaje_unknown = await canal.send(embed=discord.Embed(title="⏳ Cargando Unknown Servers..."))
    if mensaje_lalo is None:
        mensaje_lalo = await canal.send(embed=discord.Embed(title="⏳ Cargando LALO HLZ..."))
    if mensaje_sir is None:
        mensaje_sir = await canal.send(embed=discord.Embed(title="⏳ Cargando Sir Please..."))
    if mensaje_heize is None:
        mensaje_heize = await canal.send(embed=discord.Embed(title="⏳ Cargando Heizemod..."))
    if mensaje_hora is None:
        mensaje_hora = await canal.send("🕒 Última actualización: ...")

    actualizar_status.start()

async def construir_embed(nombre, servidores):
    descripcion = ""
    for ip, port in servidores:
        estado = await consultar_server(ip, port)
        if estado:
            descripcion += f"{estado}\n"

    embed = discord.Embed(
        title=f"🔹 {nombre}",
        description=descripcion or "❌ No se pudieron consultar servidores.",
        color=discord.Color.blurple()
    )
    embed.set_image(url=IMAGES.get(nombre, ""))  # Imagen correspondiente
    return embed

@tasks.loop(seconds=UPDATE_INTERVAL)
async def actualizar_status():
    global mensaje_hora

    embed_unknown = await construir_embed("Unknown Servers", UNKNOWN_SERVERS)
    embed_lalo = await construir_embed("LALO HLZ", LALO_SERVERS)
    embed_sir = await construir_embed("Sir Please", SIR_PLEASE_SERVERS)
    embed_heize = await construir_embed("Heizemod", HEIZEMOD_SERVERS)

    await mensaje_unknown.edit(embed=embed_unknown)
    await mensaje_lalo.edit(embed=embed_lalo)
    await mensaje_sir.edit(embed=embed_sir)
    await mensaje_heize.edit(embed=embed_heize)

    # ✅ Hora en zona horaria peruana
    hora_peru = datetime.datetime.now(pytz.timezone("America/Lima")).strftime("%H:%M:%S")
    await mensaje_hora.edit(content=f"🕒 Última actualización: {hora_peru} (hora Perú)")

bot.run(TOKEN)
