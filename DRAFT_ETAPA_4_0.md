# Etapa 4.0: interfaz experimental de estudio offline
Objetivo: consultar escenarios archivados con el motor de etapa 3.9. No captura pantalla, no consulta red, no integra el cliente ni recomienda durante partidas. Las confirmaciones son declaraciones manuales, no verificaciones automáticas.

Fuente: catálogo Valve existente y SQLite local generado por importador STRATZ. No redistribuir base ni token. Rango y vigencia no certificados. La interfaz requiere IDs separados por comas y repertorio de la posición elegida; dominio desconocido. Vetos vacíos significan ninguno confirmado; no usar si se desconocen los vetos.

Pruebas: `python -m unittest discover -s tests -p 'test_draft_interfaz.py' -v` y `python -m unittest discover -s tests -p 'test_sesion_offline.py' -v`. El flujo separado compila con PyInstaller onedir y comprueba carga de catálogo en el ejecutable. No prueba visualmente Tk. En Windows descargar artefacto completo y ejecutar solo si la política de seguridad lo permite. No desactivar Smart App Control.

Caso hipotético: semana 2968, CRUSADER_ARCHON, rol 2, aliados 8,100,2,3; enemigos 13,4,5,6; vetos 7; disponibles 39,86; repertorio 39,86; modo equilibrado. Marcar confirmaciones únicamente para escenario de estudio archivado. Esperado con base previa: 8 relaciones de Queen of Pain y 0 de Rubick; no hay comparación completa. No es predicción de victoria.

Reversión: revertir los commits de esta etapa o eliminar únicamente draft_offline.py, tests/test_draft_interfaz.py, .github/workflows/draft-offline.yml y este documento. No afecta SQLite ni main.py.
