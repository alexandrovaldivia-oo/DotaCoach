# Etapa 3.6 B.9 — Importador portable experimental

Objetivo: importar muestras JSON ya obtenidas, fuera de partida y sin red. No descarga datos ni solicita token. Fuente: STRATZ https://stratz.com/. Se requiere permiso de almacenamiento local; el usuario debe confirmar procedencia y rango solicitado. No se certifica el rango de respuesta ni la vigencia estadística.

Agregar los cuatro archivos conservando rutas, incluida .github/workflows/stratz-importador.yml. No reemplaza el workflow principal. Ejecutar ambos workflows y descargar el artefacto DotaStratzImportador-Windows. Extraer completamente y abrir DotaStratzImportador.exe (conservar _internal). Windows puede bloquear ejecutables sin firma: no desactivar protección; si ocurre, reportar el mensaje.

Prueba: seleccionar DotaCoach_STRATZ_cobertura.json, alias alternativa, ID 39, rango CRUSADER_ARCHON. Si se dispone de permiso local, confirmar e importar. Resultado esperado: semana 2968, 252 relaciones, etiqueta UNCALIBRATED, rango no certificado. Base separada: %USERPROFILE%\.dotacoach\experimental\stratz.sqlite3. Repetir importación no duplica filas. No subir la base ni el JSON a GitHub. No hay integración con el coach ni asistencia competitiva.

Pruebas de desarrollador: python -m unittest discover -s tests -p 'test_stratz*.py' -v. El workflow independiente ejecuta las pruebas STRATZ y una comprobación del catálogo empaquetado. La interfaz gráfica y el ejecutable Windows requieren validación real. No se ha probado PyInstaller ni Windows localmente.

Reversión: revertir el commit de esta etapa, o retirar los cuatro archivos añadidos. La base experimental es independiente y puede eliminarse manualmente si ya no se necesita. No tocar la configuración ni los datos de GSI.
