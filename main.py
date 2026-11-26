"""Dota 2 AI Coach.

Uso:
  python main.py                 Abre el coach con overlay
  python main.py --diagnostico   Solo registra lo que Dota 2 envia por GSI (sin IA ni voz)
"""
import logging
import os
import sys

from coach import config
from coach.gsi.server import ServidorGSI
from coach.gsi.setup import avisar_launch_option, crear_cfg


def configurar_logs():
    os.makedirs(config.CARPETA, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(os.path.join(config.CARPETA, "coach.log"), encoding="utf-8"),
                  logging.StreamHandler()])


def principal(cfg):
    from coach.ai.proveedor import crear_proveedor
    from coach.motor import Motor
    from coach.ui.overlay import Overlay
    from coach.voice.tts import ReproductorVoz

    voz = ReproductorVoz(cfg.get("volumen", 0.9))
    motor_ref = {}

    def al_guardar():
        config.guardar(cfg)
        motor_ref["motor"].aplicar_config()

    overlay = Overlay(cfg, al_guardar, lambda: motor_ref["motor"].probar_voz())
    motor = Motor(cfg, crear_proveedor(cfg), voz, overlay)
    motor_ref["motor"] = motor

    ruta = crear_cfg(cfg["puerto"], ruta_cfg=cfg.get("ruta_cfg"))
    if not ruta:
        overlay.mostrar("No encontre Dota 2. Revisa que Steam este instalado.")
    avisar_launch_option()

    servidor = ServidorGSI(cfg["puerto"], [motor.procesar])
    servidor.iniciar_en_hilo()
    try:
        overlay.ejecutar()
    finally:
        servidor.detener()


if __name__ == "__main__":
    configurar_logs()
    configuracion = config.cargar()
    if "--diagnostico" in sys.argv[1:]:
        from coach.diagnostico import ejecutar
        ejecutar(configuracion)
    else:
        principal(configuracion)
