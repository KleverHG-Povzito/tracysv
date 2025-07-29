import socket
import time
import asyncio

# =========================
# Funciones auxiliares
# =========================

def read_string(data, offset):
    end = data.find(b'\x00', offset)
    return data[offset:end].decode('utf-8'), end + 1

# =========================
# Cache
# =========================

cache = {}
CACHE_TTL = 30  # segundos

# =========================
# Consulta síncrona bloqueante
# =========================

def query_server_sync(ip, port):
    request_info = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.sendto(request_info, (ip, port))
    data, _ = s.recvfrom(4096)

    # Challenge
    if data[4] == 0x41:
        challenge = data[5:]
        s.sendto(request_info + challenge, (ip, port))
        data, _ = s.recvfrom(4096)

    return data

# =========================
# Consulta async segura
# =========================

async def query_server(ip, port):
    key = f"{ip}:{port}"
    now = time.time()

    if key in cache and now - cache[key]["time"] < CACHE_TTL:
        return cache[key]["data"]

    loop = asyncio.get_event_loop()
    for intento in range(2):  # Máximo 2 intentos
        try:
            data = await loop.run_in_executor(None, query_server_sync, ip, port)
            cache[key] = {"data": data, "time": now}
            return data
        except:
            await asyncio.sleep(0.1)  # Pequeña pausa entre intentos

    return None

# =========================
# Parseo A2S_INFO
# =========================

def parse_server_info(data):
    if not data or len(data) < 6:
        return None
    try:
        offset = 6
        name, offset = read_string(data, offset)
        map_name, offset = read_string(data, offset)
        folder, offset = read_string(data, offset)
        game, offset = read_string(data, offset)
        offset += 2
        players = data[offset]
        max_players = data[offset + 1]
        return {
            "name": name,
            "map": map_name,
            "folder": folder,
            "game": game,
            "players": players,
            "max_players": max_players
        }
    except:
        return None

# =========================
# Resumen final para el bot
# =========================

async def consultar_server(ip, port):
    raw_data = await query_server(ip, port)
    info = parse_server_info(raw_data)

    if not info:
        return None  # No se mostrará nada si no responde

    nombre = info['name'][:35] + "..." if len(info['name']) > 38 else info['name']
    return (
        f"🟢 `{ip}:{port}` "
        f"- {nombre or 'Sin nombre'}\n"
        f" 🧍 {info['players']}/{info['max_players']} | 🗺️ {info['map']}"
    )
