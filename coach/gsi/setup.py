"""Crea el archivo de configuracion de GSI dentro de la carpeta de Dota 2."""
import os
import re
import string
import logging

log = logging.getLogger("coach.gsi.setup")

HOST = "127.0.0" + ".1"
NOMBRE_CFG = "gamestate_integration_dotacoach.cfg"
SUBRUTA_DOTA = os.path.join("steamapps", "common", "dota 2 beta", "game", "dota", "cfg")

COMPONENTES_BASE = ("provider", "map", "player", "hero", "abilities", "items", "events")
COMPONENTES_COMPLETOS = COMPONENTES_BASE + ("buildings", "draft", "league", "wearables")


def contenido_cfg(puerto, completo=False):
    componentes = COMPONENTES_COMPLETOS if completo else COMPONENTES_BASE
    lineas = ['"Dota 2 AI Coach"', "{",
              '    "uri"           "http://%s:%d/"' % (HOST, puerto),
              '    "timeout"       "5.0"',
              '    "buffer"        "0.1"',
              '    "throttle"      "0.5"',
              '    "heartbeat"     "30.0"',
              '    "data"', "    {"]
    for nombre in componentes:
        lineas.append('        "%s"%s"1"' % (nombre, " " * max(2, 16 - len(nombre))))
    lineas += ["    }", "}", ""]
    return "\n".join(lineas)


def _bibliotecas_steam():
    """Devuelve carpetas de biblioteca de Steam (registro de Windows + libraryfolders.vdf)."""
    carpetas = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as clave:
            ruta, _ = winreg.QueryValueEx(clave, "SteamPath")
            carpetas.append(os.path.normpath(ruta))
    except (ImportError, OSError):
        pass

    for base in list(carpetas):
        vdf = os.path.join(base, "steamapps", "libraryfolders.vdf")
        try:
            with open(vdf, "r", encoding="utf-8", errors="ignore") as f:
                for ruta in re.findall(r'"path"\s+"([^"]+)"', f.read()):
                    carpetas.append(os.path.normpath(ruta.replace("\\\\", "\\")))
        except OSError:
            pass

    # Respaldo: rutas tipicas en todos los discos.
    for letra in string.ascii_uppercase:
        raiz = letra + ":\\"
        if os.path.exists(raiz):
            for sub in ("Program Files (x86)\\Steam", "Program Files\\Steam", "SteamLibrary", "Steam"):
                carpetas.append(os.path.join(raiz, sub))
    return carpetas


def encontrar_carpeta_cfg():
    vistos = set()
    for base in _bibliotecas_steam():
        if base in vistos:
            continue
        vistos.add(base)
        ruta = os.path.join(base, SUBRUTA_DOTA)
        if os.path.isdir(ruta):
            return ruta
    return None


def crear_cfg(puerto, completo=False):
    """Escribe el .cfg. Devuelve la ruta creada o None si no encontro Dota 2."""
    cfg = encontrar_carpeta_cfg()
    if not cfg:
        return None
    carpeta = os.path.join(cfg, "gamestate_integration")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, NOMBRE_CFG)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(contenido_cfg(puerto, completo))
    log.info("Configuracion GSI escrita en %s", destino)
    return destino


def avisar_launch_option():
    print("")
    print("Si no llegan datos, agrega esta opcion de lanzamiento en Steam")
    print("(Dota 2 > Propiedades > Opciones de lanzamiento):  -gamestateintegration")
    print("")
