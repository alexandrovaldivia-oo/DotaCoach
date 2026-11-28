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
