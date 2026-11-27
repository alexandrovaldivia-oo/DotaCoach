"""Cliente experimental de STRATZ. Sin acceso de red por defecto."""
import json
import urllib.request
import time
from urllib.error import URLError

URL = 'https://api.stratz.com/graphql'
RANGOS = ('HERALD_GUARDIAN', 'CRUSADER_ARCHON', 'LEGEND_ANCIENT', 'DIVINE_IMMORTAL', 'ALL')
CONSULTA = '''query ($id: Short!, $rangos: [RankBracketBasicEnum]) {
 heroStats { matchUp(heroId: $id, bracketBasicIds: $rangos, take: 150) {
 heroId with { ...Detalle } vs { ...Detalle } } }
}
fragment Detalle on HeroStatsHeroDryadType {
 heroId1 heroId2 week bracketBasicIds matchCount winCount synergy
 winRateHeroId1 winRateHeroId2 winsAverage
}'''

class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ClienteStratz:
    def __init__(self, token, *, autorizado=False, transporte=None):
        if not autorizado:
            raise PermissionError('Uso de red pendiente de autorizacion')
        if not isinstance(token, str) or not token.strip():
            raise ValueError('Token requerido')
        self._token = token.strip()
        self._transporte = transporte or self._http
        self._ultimo = None

    def _http(self, body):
        if self._ultimo is not None:
            time.sleep(max(0, 1 - (time.monotonic() - self._ultimo)))
        self._ultimo = time.monotonic()
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
            'Authorization': 'Bearer ' + self._token, 'User-Agent': 'STRATZ_API',
            'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.build_opener(_SinRedireccion()).open(req, timeout=60) as respuesta:
                return json.loads(respuesta.read(4_000_001))
        except (URLError, OSError, ValueError):
            raise RuntimeError('Fallo de transporte STRATZ; descarga detenida') from None

    def consultar(self, heroe, rango, semana=None):
        if type(heroe) is not int or heroe <= 0 or rango not in RANGOS:
            raise ValueError('Parametros invalidos')
        if semana is not None and (type(semana) is not int or semana <= 0):
            raise ValueError('Semana invalida')
        resultado = self._transporte({'query': CONSULTA, 'variables': {
            'id': heroe, 'rangos': [rango]}})
        grupo = extraer(resultado)
        # El ID de semana recibido no se presume equivalente a un timestamp Unix.
        return grupo


def extraer(resultado, alias='matchUp'):
    if not isinstance(resultado, dict) or resultado.get('errors'):
        raise ValueError('Respuesta GraphQL invalida o parcial')
    try:
        grupos = resultado['data']['heroStats'][alias]
    except (KeyError, TypeError):
        raise ValueError('Respuesta incompleta') from None
    if not isinstance(grupos, list) or len(grupos) != 1 or not isinstance(grupos[0], dict):
        raise ValueError('Grupo inesperado')
    return grupos[0]
