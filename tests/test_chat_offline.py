import unittest
from unittest.mock import patch
from draft_offline import catalogo_local
from coach.draft.chat_offline import ChatOffline

class TestChat(unittest.TestCase):
    def setUp(self): self.chat=ChatOffline(catalogo_local(),None,2968,'X')
    def test_rol(self): self.assertIn('Posición 5',self.chat.responder('Juego de 5'))
    def test_repertorio(self): self.assertIn('Rubick',self.chat.responder('Mi repertorio'))
    def test_contexto(self):
        self.chat.responder('Aliados: Lion, Axe'); self.chat.responder('Mi Axe juega de 5'); self.assertIn('Axe: posición 5 declarada',self.chat.responder('Estado'))
    def test_incremental(self):
        self.chat.responder('Mi aliado Lion'); self.chat.responder('Mi aliado Axe'); self.assertIn('Lion, Axe',self.chat.responder('Estado'))
    def test_contradiccion(self):
        self.chat.responder('Mi aliado Axe'); antes=self.chat.contexto
        with self.assertRaises(ValueError): self.chat.responder('Mi enemigo Axe')
        self.assertEqual(antes,self.chat.contexto)
    def test_reinicio(self):
        self.chat.responder('Mi aliado Axe'); self.chat.responder('Reiniciar'); self.assertFalse(self.chat.contexto.aliados)
    def test_primer_pick(self): self.assertIn('Información insuficiente',self.chat.responder('Compara QoP o Rubick'))
    def test_parcial(self):
        self.chat.responder('Mi aliado Axe')
        with patch('coach.draft.contexto_conversacional.estadistica',return_value={'partidas':200,'tasa':.5}):
            self.assertIn('50.00 por ciento',self.chat.responder('¿Qué me conviene más QoP o Rubick?'))
    def test_candidato_ocupado(self):
        self.chat.responder('Candidatos: Axe, QoP'); self.chat.responder('Mi aliado Axe'); self.assertEqual(self.chat.contexto.candidatos,(39,))
    def test_no_inventa(self):
        with self.assertRaises(ValueError): self.chat.responder('Mi aliado héroe inventado')
    def test_sin_candidatos(self): self.assertIn('Indica candidatos',self.chat.responder('Analizar'))
