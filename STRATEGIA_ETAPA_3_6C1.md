# Etapa 3.6 C.1 — Perfiles estratégicos parciales

Objetivo: representar capacidades con evidencia y conservar lo desconocido. Uso exclusivamente offline, sin recomendaciones competitivas.

Fuentes: catálogo Valve existente y extractos indexados de https://www.dota2.com/hero/queenofpain/?l=spanish , https://www.dota2.com/hero/puck y https://www.dota2.com/hero/rubick revisados el 27/11/2026. Las páginas completas no fueron legibles; no se certifica parche. El escape de Queen of Pain es una inferencia; no se afirma que esté siempre disponible. Los perfiles son parciales, no califican fuerza ni ausencia de capacidades. El enlace de fuente se valida sintácticamente, no garantiza autenticidad ni vigencia.

Archivos nuevos: coach/draft/capacidades.py y tests/test_capacidades_estrategicas.py. No cambia SQLite, GSI, Gemini, workflows ni ejecutables. No incluye datos STRATZ.

Prueba en CI: python -m unittest discover -s tests. Prueba focal: python -m unittest discover -s tests -p test_capacidades_estrategicas.py -v. No requiere Python en PC del usuario. Se ejecutaron 12 pruebas nuevas y 10 de catálogo sobre los parches locales. Falta suite completa en GitHub.

Aceptación: identidades válidas, evidencia trazable, distinción de estados, desconocidos explícitos, rechazo de duplicados. Reversión: revertir el commit o eliminar exclusivamente los tres archivos de este parche. No activa ninguna función en partida.
