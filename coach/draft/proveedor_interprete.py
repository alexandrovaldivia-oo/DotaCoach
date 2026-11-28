"""Adaptador exclusivo para interpretar texto archivado, no altera el coach principal."""
import re
import requests


class ErrorInterpretacion(ValueError):
    pass


class GeminiInterprete:
    def __init__(self, cfg):
        self.cfg = dict(cfg)

    def disponible(self):
        return bool(str(self.cfg.get('api_key') or '').strip())

    def generar(self, prompt):
        if not self.disponible():
            raise ErrorInterpretacion('Clave API no configurada.')
        modelo = self.cfg.get('modelo')
        if not isinstance(modelo, str) or not re.fullmatch(r'[a-zA-Z0-9._-]+', modelo):
            raise ErrorInterpretacion('Modelo no válido.')
        cuerpo = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {
            'temperature': 0.1, 'maxOutputTokens': 2048, 'responseMimeType': 'application/json'}}
        try:
            r = requests.post('https://generativelanguage.googleapis.com/v1beta/models/'+modelo+':generateContent',
                              json=cuerpo, headers={'x-goog-api-key': self.cfg['api_key']}, timeout=(5, 25))
        except requests.Timeout:
            raise ErrorInterpretacion('Tiempo de espera de Gemini agotado.') from None
        except requests.RequestException:
            raise ErrorInterpretacion('Error de conexión con Gemini.') from None
        if r.status_code != 200:
            mensajes = {400:'Solicitud rechazada', 401:'Autenticación rechazada', 403:'Acceso denegado', 404:'Modelo no encontrado', 429:'Cuota o límite de solicitudes'}
            raise ErrorInterpretacion(f'Gemini HTTP {r.status_code}: '+mensajes.get(r.status_code,'Error del servidor'))
        try:
            datos = r.json()
        except ValueError:
            raise ErrorInterpretacion('Respuesta HTTP sin JSON válido.') from None
        try:
            for c in datos.get('candidates', []):
                motivo = c.get('finishReason')
                if motivo == 'MAX_TOKENS':
                    raise ErrorInterpretacion('Gemini agotó los tokens de salida.')
                if motivo != 'STOP':
                    continue
                texto = ''.join(p['text'] for p in c.get('content', {}).get('parts', []) if p.get('thought') is not True and isinstance(p.get('text'), str))
                if texto.strip():
                    return texto
        except (AttributeError, TypeError, KeyError, requests.exceptions.JSONDecodeError):
            raise ErrorInterpretacion('Respuesta HTTP con estructura inválida.') from None
        raise ErrorInterpretacion('Gemini no devolvió texto final completo.')


def crear_interprete(cfg):
    if cfg.get('proveedor', 'gemini') != 'gemini':
        raise ErrorInterpretacion('Proveedor de interpretación no soportado.')
    return GeminiInterprete(cfg)
