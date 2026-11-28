# Etapa 4.4 — Voz local y personalidad experimental

Uso exclusivo para escenarios archivados, fuera de partidas. No cambia GSI, SQLite, proveedor de consejos ni configuración. La interfaz conserva el consentimiento de IA remota; el audio no se envía al proveedor, solo texto si el usuario lo envía y autoriza.

Windows PowerShell 5.1 y System.Speech (.NET Framework) se utilizan como backend local opcional. Requiere reconocedor de dictado y voz española disponibles para System.Speech, micrófono predeterminado y permisos. No instala paquetes ni cambia políticas. Si falta un componente, el chat escrito sigue disponible. No usar para sortear un bloqueo de Smart App Control.

Prueba: descargar el artefacto de draft offline, abrir el chat, activar Leer respuestas, seleccionar personalidad, pulsar Escuchar una frase, decir «Soy mid», revisar transcripción y pulsar Enviar. Probar Detener audio durante una respuesta. Probar una comparación archivada con datos insuficientes y Humor activado/desactivado. Verificar que no se escucha sin pulsar el botón. El micrófono no se activa continuamente; no hay palabra clave ni envío automático. Si el audio está ocupado, otra solicitud de audio detiene la anterior; repetir cuando termine. No hay clonación de voces, solo estilo textual y primera voz española local disponible. Humor usa una regla limitada, no sarcasmo generativo. El nombre de héroes ingleses puede requerir corrección manual.

Pruebas locales: `python -m unittest discover -s tests` en reconstrucción de parches; backend de audio simulado y lógica comprobada. Falta probar Windows real y sus dispositivos; no se afirma latencia medida. El flujo principal descubre pruebas; no se modifica el workflow independiente existente.

Reversión: revertir el commit de esta etapa; elimina voz_enigma.py, test_voz_enigma.py y este documento y restaura draft_offline.py. No eliminar la base SQLite ni configuración.

Referencia: https://learn.microsoft.com/en-us/dotnet/api/system.speech.recognition.speechrecognitionengine.recognize?view=netframework-4.8
