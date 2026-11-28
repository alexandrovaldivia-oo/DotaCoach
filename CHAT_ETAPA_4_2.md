# Etapa 4.2 — Chat local de estudio (prototipo)

Base: parche 4.1, compilación #39 reportada; reconstrucción local de parches, no checkout certificado de GitHub.

El botón Abrir chat de estudio offline abre una conversación separada del formulario original. Usa los campos SQLite, semana y rango del formulario al abrirse. No hay red, captura, micrófono ni recomendación competitiva. El repertorio de ejemplo corresponde a las preferencias aportadas por el creador; los niveles de dominio no se presuponen. ENIGMA es un nombre provisional. El estado se conserva solo mientras la ventana está abierta. El parser admite frases limitadas, no lenguaje libre general. Los comandos con dos puntos reemplazan una lista; Mi aliado / Mi enemigo / Vetaron a agregan un héroe y retiran ese héroe de candidatos. Los candidatos se indican manualmente para escenarios archivados. No se certifican rango, parche ni posición estadística.

Prueba: con el juego cerrado, abrir el chat, escribir Soy mid; Mi aliado Lion; Mi aliado Axe; Mi Axe juega de 5; Enemigos: Puck, Sven; Compara QoP o Rubick. Con la muestra original, se esperan 4/4 relaciones suficientes para QoP (45.71% media descriptiva) y 0/4 para Rubick. La media no es probabilidad de ganar. No se modifica SQLite.

Pruebas locales: `python -m unittest discover -s tests -p 'test_chat_offline.py' -v` (11), `test_contexto_conversacional.py` (11), `test_draft_interfaz.py` (4), `test_sesion_offline.py` (4), usando el mismo comando con cada patrón. `python draft_offline.py --self-test` también pasó. La GUI de Windows y el workflow independiente aún no se verificaron. No se modificó el workflow; la prueba nueva se espera en el descubrimiento general de tests del proyecto. Si no se ejecuta allí, agregarla en un cambio posterior verificado.

Reversión: revertir el commit de este parche (restaura draft_offline.py y elimina el módulo, tests y documentación nuevos). No borrar la base SQLite. No se requiere instalar Python en el equipo del jugador.
