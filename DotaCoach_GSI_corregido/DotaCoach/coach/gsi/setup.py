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


def contenido_cfg(puerto, completo=False, validado=False):
    componentes = COMPONENTES_BASE[:6] if validado else (COMPONENTES_COMPLETOS if completo else COMPONENTES_BASE)
    lineas = ['"Dota 2 AI Coach"', "{",
              '    "uri"           "http://%s:%d/"' % (HOST, puerto),
              '    "timeout"       "5.0"',
              '    "buffer"        "0.1"',
              '    "throttle"      "0.5"',
              '    "heartbeat"     "%s"' % ("10.0" if validado else "30.0"),
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


def encontrar_carpeta_cfg(ruta_cfg=None):
    """Solo acepta instalaciones con ejecutable; no elige entre varias a ciegas."""
    candidatos = [ruta_cfg] if ruta_cfg else [
        os.path.join(base, SUBRUTA_DOTA) for base in _bibliotecas_steam()]
    encontrados = {}
    for ruta in candidatos:
        ruta = os.path.abspath(ruta)
        game = os.path.dirname(os.path.dirname(ruta))
        exe = os.path.join(game, "bin", "win64", "dota2.exe")
        if os.path.isdir(ruta) and os.path.isfile(exe):
            encontrados[os.path.normcase(os.path.realpath(ruta))] = ruta
    if len(encontrados) > 1:
        raise OSError("Varias instalaciones de Dota 2: configura ruta_cfg en config.json: "
                      + " | ".join(encontrados.values()))
    if ruta_cfg and not encontrados:
        raise OSError("ruta_cfg no corresponde a una instalacion de Dota 2: " + ruta_cfg)
    return next(iter(encontrados.values()), None)


def crear_cfg(puerto, completo=False, ruta_cfg=None):
    """Usa los seis componentes validados; completo es una prueba optativa."""
    cfg = encontrar_carpeta_cfg(ruta_cfg)
    if not cfg:
        return None
    carpeta = os.path.join(cfg, "gamestate_integration")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, NOMBRE_CFG)
    contenido = contenido_cfg(puerto, completo, validado=not completo)
    # Conserva configuraciones anteriores para permitir una reversion.
    if os.path.isfile(destino):
        with open(destino, "rb") as f:
            anterior = f.read()
        if anterior.replace(b"\r\n", b"\n") == contenido.encode("ascii"):
            return destino
        import shutil
        import time
        shutil.copy2(destino, destino + ".%d.bak" % time.time_ns())
    import tempfile
    fd, temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="ascii") as f:
            f.write(contenido)
        os.replace(temporal, destino)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
    log.info("Configuracion GSI escrita en %s", destino)
    return destino


def avisar_launch_option():
    print("")
    print("Si no llegan datos, agrega esta opcion de lanzamiento en Steam")
    print("(Dota 2 > Propiedades > Opciones de lanzamiento):  -gamestateintegration")
    print("")
