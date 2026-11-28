# Corrección 4.3 — intérprete ENIGMA

Objetivo: separar la generación JSON del proveedor de consejos, conservar fase declarada y evitar controles cortados. No habilita asistencia competitiva.

Archivos: draft_offline.py, coach/draft/{proveedor_interprete,lenguaje_natural,contexto_conversacional,chat_offline}.py y tests/test_lenguaje_natural.py. El flujo existente ya ejecuta estas pruebas y empaqueta las dependencias. No requiere cambios de workflow.

Pruebas locales: 334 pruebas de la reconstrucción por ZIP, todas satisfactorias; seis nuevas. `python -m unittest discover -s tests` y `python draft_offline.py --self-test`. HTTP simulado, no se usaron claves reales. La interfaz gráfica Windows y la llamada real quedan pendientes.

Validación: abrir el artefacto nuevo, activar IA remota, introducir el escenario ficticio de mid, Lion 5, Axe 3, Puck y Sven enemigos, segunda fase. Enviar y confirmar únicamente si el resumen es correcto. Si hay fallo, capturar el diagnóstico; no compartir claves. No se modifica SQLite ni la configuración. La fase es declarada, no inferida por posición. La interfaz numérica anterior conserva sus restricciones.

Reversión: revertir el commit del parche en GitHub; no borrar datos locales. El adaptador nuevo no altera el proveedor del coach principal. La causa exacta del error previo no fue reproducida.
