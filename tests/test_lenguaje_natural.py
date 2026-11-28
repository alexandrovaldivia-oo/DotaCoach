import unittest
from draft_offline import catalogo_local
from coach.draft.chat_offline import ChatOffline
from coach.draft.lenguaje_natural import proponer, aplicar

class Fake:
    def __init__(self,s): self.s=s
    def disponible(self): return True
    def generar(self,prompt): return self.s

class TestLenguaje(unittest.TestCase):
    def setUp(self): self.chat=ChatOffline(catalogo_local(),None,2968,'X')
    def test_propuesta(self):
        c=self.chat.contexto; p=proponer(self.chat,Fake('{"rol":2,"aliados":["Lion","Axe"],"roles":[{"heroe":"Axe","rol":5}]}'),'Voy mid'); self.assertEqual(c,self.chat.contexto); self.assertIn('posición 5 declarada',aplicar(self.chat,c,p))
    def test_invalidos(self):
        for s in ('no json','{}','{"rol":true}','{"aliados":["inventado"]}','{"modo":"ranked"}','{"analizar":1}','{"aliados":["Axe"],"enemigos":["Axe"]}'):
            with self.subTest(s=s),self.assertRaises(ValueError): proponer(self.chat,Fake(s),'prueba')
    def test_contexto_cambio(self):
        c=self.chat.contexto;p=proponer(self.chat,Fake('{"rol":3}'),'off');self.chat.responder('Soy 5');self.assertRaises(ValueError,aplicar,self.chat,c,p)
    def test_incremental(self):
        self.chat.responder('Mi aliado Lion'); c=self.chat.contexto;p=proponer(self.chat,Fake('{"aliados":["Axe"]}'),'también Axe');self.assertIn('Lion, Axe',aplicar(self.chat,c,p))
    def test_analisis(self):
        c=self.chat.contexto;p=proponer(self.chat,Fake('{"candidatos":["QoP","Rubick"],"analizar":true}'),'compara');self.assertIn('Información insuficiente',aplicar(self.chat,c,p))

from unittest.mock import patch, Mock
import requests
from coach.draft.proveedor_interprete import GeminiInterprete, ErrorInterpretacion

class TestInterpreteGemini(unittest.TestCase):
    def setUp(self):
        self.p = GeminiInterprete({'modelo':'gemini-test','api_key':'clave-ficticia'})
        self.chat = ChatOffline(catalogo_local(),None,2968,'X')

    @patch('coach.draft.proveedor_interprete.requests.post')
    def test_json_y_fase(self, post):
        post.return_value.status_code=200
        post.return_value.json.return_value={'candidates':[{'finishReason':'STOP','content':{'parts':[{'thought':True,'text':'ignorar'},{'text':'{"rol":2,"fase":2,"aliados":["Lion","Axe"],'},{'text':'"enemigos":["Puck","Sven"],"roles":[{"heroe":"Lion","rol":5},{"heroe":"Axe","rol":3}]}'}]}}]}
        previo=self.chat.contexto
        propuesta=proponer(self.chat,self.p,'Escenario de segunda fase')
        self.assertEqual(self.chat.contexto,previo)
        aplicar(self.chat,previo,propuesta)
        self.assertEqual(self.chat.contexto.fase,2)
        self.assertEqual(len(self.chat.contexto.roles_declarados),2)
        self.assertEqual(len(self.chat.contexto.enemigos),2)
        gen=post.call_args.kwargs['json']['generationConfig']
        self.assertEqual(gen['maxOutputTokens'],2048)
        self.assertEqual(gen['responseMimeType'],'application/json')

    @patch('coach.draft.proveedor_interprete.requests.post')
    def test_http_y_secreto(self, post):
        for code in (400,401,403,404,429,503):
            post.return_value.status_code=code
            post.return_value.text='clave-ficticia'
            with self.assertRaisesRegex(ErrorInterpretacion,f'HTTP {code}') as e: self.p.generar('prueba')
            self.assertNotIn('clave-ficticia',str(e.exception))

    @patch('coach.draft.proveedor_interprete.requests.post')
    def test_timeout(self, post):
        post.side_effect=requests.Timeout('clave-ficticia')
        with self.assertRaisesRegex(ErrorInterpretacion,'espera'): self.p.generar('prueba')

    @patch('coach.draft.proveedor_interprete.requests.post')
    def test_tokens(self, post):
        post.return_value.status_code=200
        post.return_value.json.return_value={'candidates':[{'finishReason':'MAX_TOKENS'}]}
        with self.assertRaisesRegex(ErrorInterpretacion,'tokens'): self.p.generar('prueba')

    def test_fase_invalida(self):
        for v in ('true','0','4','"segunda"'):
            with self.assertRaises(ValueError): proponer(self.chat,Fake('{"fase":'+v+'}'),'prueba')

    def test_fase_y_nulos(self):
        previo=self.chat.contexto
        p=proponer(self.chat,Fake('```JSON\r\n{"fase":2,"aliados":null,"roles":null}\r\n```'),'segunda fase')
        aplicar(self.chat,previo,p)
        self.assertIn('Fase declarada: 2',self.chat.estado())
        self.chat.responder('reiniciar')
        self.assertIsNone(self.chat.contexto.fase)
