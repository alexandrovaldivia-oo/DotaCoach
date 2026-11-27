# Etapa 3.6 C consolidada — comparación offline experimental

Objetivo: unir perfiles parciales, repertorio, disponibilidad confirmada y lector SQLite para comparar escenarios archivados. No se conecta al juego ni habilita asistencia competitiva. No consulta internet. No genera recomendaciones definitivas ni puntuaciones. Los modos estratégico y equilibrado comparten candidatos por ahora; ambos exponen pertenencia al repertorio y el modo personal filtra por posición declarada. No infiere aptitud de rol. Orden alfabético.

## Fuentes y límites
Se reutiliza PILOTO de capacidades.py. Se agregan evidencias parciales de https://www.dota2.com/hero/disruptor, https://www.dota2.com/hero/tusk y https://www.dota2.com/hero/juggernaut (extractos indexados consultados el 2026-11-27; parche no certificado). La protección por curación es una inferencia. Los perfiles no documentados se mantienen desconocidos. STRATZ https://stratz.com/ es fuente de estadísticas locales, con rango no certificado y vigencia desconocida. No se distribuyen datos ni tokens. No se calcula ni interpreta synergy como causalidad o probabilidad de victoria.

## Pruebas y uso
Desde la raíz del repositorio: `python -m unittest discover -s tests -p test_analisis_offline.py -v` (15 pruebas; en GitHub Actions, no instalar Python localmente). Se utiliza un escenario de ejemplo y SQLite temporal. Adicionalmente se comprobó la base real de usuario en modo lectura: Queen of Pain 8/8 relaciones disponibles, Rubick y Disruptor 0/8. Escenario hipotético, no partida observada. El hash del archivo no cambió. Las pruebas locales se ejecutaron con una reconstrucción de dependencias a partir de parches disponibles, no un checkout confirmado del commit da9c0bc.

## Aceptación y reversión
Subir los tres archivos conservando las rutas. Confirmar el flujo principal y que las 15 pruebas nuevas se ejecutaron. Si falla, revertir el commit o eliminar únicamente los tres archivos nuevos. No requiere actualizar la base ni el importador. No modificar los flujos de compilación. La futura interfaz, la clasificación de candidatos, la certificación de rangos, el catálogo estratégico completo, los permisos STRATZ y la firma de ejecutables quedan pendientes.
