"""Modo diagnostico: registra lo que Dota 2 envia por GSI. Sin IA ni voz."""
import os

from .gsi.grabador import GrabadorGSI
from .gsi.server import ServidorGSI
from .gsi.setup import avisar_launch_option, crear_cfg


def ejecutar(cfg):
    ruta = crear_cfg(cfg["puerto"], completo=True)
    print("Configuracion GSI:", ruta or "NO se encontro Dota 2 (hay que crear el .cfg a mano)")
    avisar_launch_option()

    grabador = GrabadorGSI()
    try:
        servidor = ServidorGSI(cfg["puerto"], [grabador])
    except OSError as error:
        print("No se pudo abrir el puerto %s: %s" % (cfg["puerto"], error))
        print("Cierra otras copias del coach o del diagnostico y vuelve a intentar.")
        return

    print("Escuchando... abre Dota 2, juega una partida y pulsa Ctrl+C al terminar.")
    print("Registro:", grabador.ruta_log)
    try:
        servidor.servir()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.detener()
        ruta_campos = grabador.cerrar()
        print("")
        print("Mensajes recibidos:", grabador.mensajes)
        print("Campos vistos guardados en:", ruta_campos)
        if grabador.mensajes == 0:
            print("No llego ningun dato. Revisa: opcion de lanzamiento de Steam,")
            print("que Dota 2 se abrio DESPUES de iniciar este programa, y que estabas jugando tu.")
        else:
            try:
                os.startfile(os.path.dirname(ruta_campos))
            except (AttributeError, OSError):
                pass
