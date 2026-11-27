# Clasificacion descriptiva y explicaciones offline

Objetivo: preparar comparaciones de escenarios archivados sin activar asistencia competitiva.
Base: parches hasta 3.6 C consolidada, no copia certificada del commit e4be8a9.
Fuente: SQLite local STRATZ y perfiles parciales con procedencia Valve. Sin red, sin datos privados en el parche.
API: `coach.draft.clasificacion_offline.clasificar(**escenario, minimo_partidas=100)` acepta los mismos argumentos que `analisis_offline.comparar`. Devuelve candidatos con explicaciones deterministas, media descriptiva y orden opcional. No es una prediccion ni una recomendacion. El umbral 100 es provisional, no una certificacion estadistica. Los empates se ordenan por ID para reproducibilidad. No mezcla dominio ni synergy con tasas; no penaliza datos ausentes. Los modos se heredan del modulo anterior; estrategico y equilibrado aun comparten candidatos.
Pruebas: `python -m unittest discover -s tests -p 'test_clasificacion_offline.py'` (11) y `python -m unittest discover -s tests -p 'test_analisis_offline.py'` (15). Ambas pasaron localmente. Se verifico ademas que la base real no cambia y que no se produce orden si faltan datos de candidatos.
Aceptacion: CI verde, ausencia de recomendaciones en partida, orden solo con cobertura completa de todos los candidatos y dos o mas candidatos. No se integra con GSI ni Gemini. Pendiente: cobertura de otros heroes, permisos STRATZ, calibracion, explicaciones IA y firma digital.
Reversion: revertir el commit de estos tres archivos nuevos; no altera SQLite ni modulos existentes.
