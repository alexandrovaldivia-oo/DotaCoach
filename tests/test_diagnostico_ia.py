import unittest
from unittest.mock import Mock, patch
from coach.ai.proveedor import ProveedorGemini
from coach.ai.contexto import evaluar_respuesta, SolicitudContexto

class TestDiagnosticoIA(unittest.TestCase):
    def respuesta(self, partes, motivo='STOP'):
        r = Mock(status_code=200)
        r.json.return_value = {'candidates':[{'finishReason':motivo,'content':{'parts':partes}}]}
        return r

    def generar(self, r):
        p = ProveedorGemini({'api_key':'secreto_prueba','modelo':'modelo_prueba'})
        with patch('coach.ai.proveedor.requests.post', return_value=r) as post:
            resultado = p.generar('prueba')
            self.assertEqual(post.call_args.kwargs['json']['generationConfig']['maxOutputTokens'],512)
        return resultado

    def test_ignora_razonamiento(self):
        self.assertEqual(self.generar(self.respuesta([{'thought':True,'text':'razonamiento privado'},{'text':'Cuida tu posición.'}])),'Cuida tu posición.')

    def test_une_fragmentos_finales(self):
        self.assertEqual(self.generar(self.respuesta([{'text':'Cuida'},{'text':'tu posición.'}])),'Cuida tu posición.')

    def test_rechaza_truncado(self):
        self.assertIsNone(self.generar(self.respuesta([{'text':'Compra'}],'MAX_TOKENS')))

    def test_solo_razonamiento(self):
        self.assertIsNone(self.generar(self.respuesta([{'thought':True,'text':'privado'}])))

    def test_causas(self):
        s = SolicitudContexto('p',0,('m','h'),max_palabras=3)
        for texto, causa in [(None,'vacia'),('SILENCIO.','silencio_solicitado'),('Compra item_blink','identificador_interno'),('Una frase demasiado extensa','limite_palabras'),('***','vacia_tras_limpieza'),('Cuida tu vida','aceptada')]:
            with self.subTest(causa=causa):
                self.assertEqual(evaluar_respuesta(texto,s)[1],causa)

    def test_error_http_no_filtra_cuerpo(self):
        r = Mock(status_code=403,text='secreto_prueba')
        with self.assertLogs('coach.ai',level='WARNING') as logs:
            self.assertIsNone(self.generar(r))
        self.assertNotIn('secreto_prueba',' '.join(logs.output))
