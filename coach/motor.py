"""Motor integrado. Consejos solo en una partida de práctica habilitada a mano."""
import logging
import threading
import time

from .ai.contexto import construir_contexto, evaluar_respuesta, respuesta_vigente
from .eventos_avanzados import detectar_avanzados
from .prioridades import ControlAvisos
from .persona import persona
from .state import EstadoPartida, parsear
from .texto import limpiar_texto

log = logging.getLogger('coach.motor')


class _VigenciaVoz:
    """Dos controles: admisión de audio y continuidad tras comenzar."""
    def __init__(self, antes, durante):
        self.antes = antes
        self.durante = durante

    def __call__(self):
        return self.antes()


class Motor:
    def __init__(self, cfg, proveedor, voz, ui, *, reloj=time.monotonic):
        self.cfg, self.proveedor, self.voz, self.ui = cfg, proveedor, voz, ui
        self.estado = EstadoPartida()
        self._reloj = reloj
        self._lock = threading.RLock()
        self._control = ControlAvisos()
        self._sesion = None
        self._generacion = 0
        self._generacion_audio = 0
        self._ultimo_gsi = None
        self._ia_ocupada = False
        self._cerrado = False
        self.aplicar_config()

    def aplicar_config(self):
        with self._lock:
            voz, tono, velocidad = persona(self.cfg.get('persona'))['voz']
            self.voz.configurar(voz, tono, velocidad, self.cfg.get('volumen', 0.9))
            self._generacion += 1
            self._generacion_audio += 1
            if self.cfg.get('modo_competitivo'):
                self._sesion = None

    def _actual(self, e, ahora):
        return (not self._cerrado and not self.cfg.get('modo_competitivo')
                and bool(e.match_id) and bool(e.heroe) and e.en_partida
                and e.fase_activa and e.pausa is False and 'hero.alive' in e.conocidos
                and self._ultimo_gsi is not None and 0 <= ahora-self._ultimo_gsi <= 3)

    def _practica(self, ahora):
        return self._actual(self.estado, ahora) and self._sesion == (self.estado.match_id, self.estado.heroe)

    def habilitar_practica(self):
        """Confirmación humana, solo para la partida actual. GSI no certifica su modalidad."""
        with self._lock:
            if not self._actual(self.estado, self._reloj()):
                return False
            self._sesion = (self.estado.match_id, self.estado.heroe)
            self._generacion += 1
            self._generacion_audio += 1
            log.info('Practica habilitada manualmente')
            return True

    def deshabilitar_practica(self):
        with self._lock:
            self._sesion = None
            self._generacion += 1
            self._generacion_audio += 1

    def cerrar(self):
        with self._lock:
            self._cerrado = True
            self.deshabilitar_practica()

    def procesar(self, payload):
        with self._lock:
            if self._cerrado:
                return
            ahora = self._reloj()
            prev, act = self.estado, parsear(payload)
            if self._ultimo_gsi is not None and ahora-self._ultimo_gsi > 3:
                self.deshabilitar_practica()
            self.estado, self._ultimo_gsi = act, ahora
            if self._sesion is not None and (self._sesion != (act.match_id, act.heroe)
                    or not act.fase_activa or not act.en_partida or self.cfg.get('modo_competitivo')):
                self.deshabilitar_practica()
            if (prev.pausa != act.pausa or prev.vivo != act.vivo
                    or prev.heroe != act.heroe or prev.match_id != act.match_id
                    or prev.fase != act.fase or 'hero.alive' not in act.conocidos
                    or ('map.clock_time' in prev.conocidos and 'map.clock_time' in act.conocidos and act.reloj < prev.reloj)):
                self._generacion += 1
                self._generacion_audio += 1
            practica = self._practica(ahora)
            self.ui.estado('Practica activa' if practica else 'Consejos desactivados')
            try:
                disponible = bool(self.proveedor.disponible()) if practica else False
            except Exception:
                disponible = False
            eventos = detectar_avanzados(prev, act)
            aviso = self._control.seleccionar(eventos, act, ahora, practica=practica,
                        ia_disponible=disponible, ia_ocupada=self._ia_ocupada)
            if not aviso:
                return
            # Una nueva intervención invalida cualquier entrega anterior aún pendiente.
            self._generacion += 1
            generacion = self._generacion
            # Una alerta crítica nueva puede interrumpir un consejo en curso.
            if aviso.tipo == 'vida_baja':
                self._generacion_audio += 1
            log.info('Intervencion seleccionada: %s', aviso.tipo)
            if aviso.usa_ia:
                limite = self.cfg.get('max_palabras', 22)
                if type(limite) is not int or not 1 <= limite <= 40:
                    limite = 22
                solicitud = construir_contexto(act, aviso, ahora, practica=True,
                            personalidad=self.cfg.get('persona', 'profesional'), max_palabras=limite)
                if solicitud:
                    self._ia_ocupada = True
                    threading.Thread(target=self._pedir_ia, args=(solicitud, generacion), daemon=True).start()
            else:
                textos = {'vida_baja': 'Tu vida está baja. Evalúa si debes retirarte.',
                          'mana_baja': 'Tu maná está bajo. Administra tus recursos.',
                          'definitiva_disponible': 'Tu habilidad definitiva está disponible.'}
                texto = textos.get(aviso.tipo)
                if texto:
                    self._entregar(texto, self._guardia(generacion, ahora, aviso.tipo, act.vivo))

    def _guardia(self, generacion, creada, tipo, vivo, solicitud=None):
        def vigente():
            with self._lock:
                ahora = self._reloj()
                e = self.estado
                if (generacion != self._generacion or not self._practica(ahora)
                        or not 0 <= ahora-creada <= 8 or e.vivo != vivo):
                    return False
                if solicitud is not None:
                    return respuesta_vigente(solicitud, e, ahora, practica=True,
                            edad_estado=ahora-self._ultimo_gsi)
                if tipo == 'vida_baja':
                    return e.vida_porcentaje is not None and 0 < e.vida_porcentaje <= 25
                if tipo == 'mana_baja':
                    return e.mana_porcentaje is not None and e.mana_porcentaje <= 20
                if tipo == 'definitiva_disponible':
                    return any(a.definitiva is True and a.pasiva is False and a.nivel
                               and a.recarga == 0 and a.disponible is True for a in e.detalle_habilidades)
                return False
        return vigente

    def _entregar(self, texto, vigente):
        texto = limpiar_texto(texto)
        with self._lock:
            if texto and vigente():
                self.ui.mostrar(texto, vigente=vigente)
                if self.cfg.get('voz', True):
                    generacion_audio = self._generacion_audio
                    vivo = self.estado.vivo

                    def continuar():
                        with self._lock:
                            return (generacion_audio == self._generacion_audio
                                    and bool(self.cfg.get('voz', True))
                                    and self._practica(self._reloj())
                                    and self.estado.vivo == vivo)

                    self.voz.hablar(texto, vigente=_VigenciaVoz(
                        lambda: continuar() and vigente(), continuar))

    def _pedir_ia(self, solicitud, generacion):
        try:
            vigente = self._guardia(generacion, solicitud.creada, solicitud.tipo, solicitud.vivo, solicitud)
            if not vigente():
                return
            texto, causa = evaluar_respuesta(self.proveedor.generar(solicitud.prompt), solicitud)
            if not texto:
                log.info('Respuesta IA descartada: %s', causa)
            elif not vigente():
                log.info('Respuesta IA descartada: contexto_no_vigente')
            else:
                log.info('Respuesta IA aceptada para entrega')
                self._entregar(texto, vigente)
        except Exception:
            log.warning('Fallo al generar consejo de IA')
        finally:
            with self._lock:
                self._ia_ocupada = False

    def probar_voz(self):
        texto = 'Voz de prueba. Listo para entrenar.'
        self.ui.mostrar(texto)
        with self._lock:
            if self.cfg.get('voz', True) and not self._cerrado:
                generacion_audio = self._generacion_audio

                def vigente():
                    with self._lock:
                        return (not self._cerrado and bool(self.cfg.get('voz', True))
                                and generacion_audio == self._generacion_audio)

                self.voz.hablar(texto, vigente=vigente)
