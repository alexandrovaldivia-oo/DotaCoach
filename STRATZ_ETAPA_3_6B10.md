# Etapa 3.6 B.10 — lector experimental

Objetivo: auditar y consultar SQLite local fuera de partida, sin red y sin modificar datos.
Requisitos: parches B8 y B9, catálogo existente. Fuente: tablas relaciones_v1 y lotes_v1.

Archivos: nuevo coach/draft/stratz_lector.py y tests/test_stratz_lector.py; se reemplaza actualizador_stratz.py de B9 únicamente para agregar el botón de verificación y ampliar la ventana. No se cambia el workflow.

Pruebas: python -m unittest discover -s tests -p 'test_stratz*.py' -v
Resultado local: 30 pruebas, 8 nuevas. Importación y auditoría de muestra real: 252 relaciones, 126 por tipo, integrity_check ok. QoP vs Puck: 458/1018. No se incluye la muestra ni la base en el parche.

Windows: subir los archivos a main, verificar Actions principal e importador, descargar el nuevo artefacto DotaStratzImportador-Windows, extraerlo y abrir el exe. Pulsar Verificar base existente sin reimportar. Esperado: ok, 252 relaciones, un lote, semana 2968, 126 aliados y 126 enemigos, QoP vs Puck 458/1018. Si existen más lotes, los totales variarán.

El lector abre SQLite en modo ro, no crea una base faltante. La prueba QoP/Puck de la interfaz es un diagnóstico fijo para la muestra existente; la función consultar admite otros IDs y semanas. El intervalo Wilson supone observaciones binomiales y no corrige sesgos. Vigencia desconocida salvo referencia explícita; rango siempre no certificado. No se interpreta synergy como probabilidad. No se habilitan red masiva ni asistencia competitiva. Permisos STRATZ pendientes.

Reversión: revertir el commit del parche B10 o restaurar actualizador_stratz.py de B9 y eliminar los tres archivos nuevos. No borrar SQLite. El esquema permanece intacto.
