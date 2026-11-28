# Etapa 4.5 — Whisper experimental offline

## Objetivo
Separar captura PCM de reconocimiento y conservar el chat y el sintetizador existentes. No habilita asistencia competitiva. No transmite audio a la red; el texto solo se envía a Gemini si se autoriza mediante los controles existentes.

## Preparación
1. Subir draft_offline.py, coach/draft/whisper_enigma.py, tests/test_whisper_enigma.py y este documento a la raíz, conservando rutas. Reemplazar .github/workflows/draft-offline.yml en un segundo commit. No modificar el workflow principal.
2. Comprobar ambos workflows. Descargar DotaDraftOffline-Windows y extraerlo completo.
3. Obtener el binario Windows x64 CPU de https://github.com/ggml-org/whisper.cpp/releases y extraer todos sus archivos, incluidas DLL. Obtener ggml-base.bin multilingüe desde https://huggingface.co/ggerganov/whisper.cpp/blob/main/ggml-base.bin (no usar base.en). No instalar Python. No desactivar Smart App Control si bloquea algún binario.
4. Abrir ENIGMA, pulsar Configurar Whisper, elegir whisper-cli.exe y ggml-base.bin. La configuración es por sesión. Pulsar Escuchar una frase y hablar durante los seis segundos de captura. Revisar la transcripción y enviar. El envío automático es opcional y está desactivado inicialmente. No sustituye las confirmaciones de IA remota.
5. Probar «Hola Enigma, soy mid», «Mis aliados son Lion y Axe», «Compara Queen of Pain con Rubick». Comprobar palabras, latencia y que Detener audio cancela el resultado. Usar Windows permite volver al reconocedor anterior.

## Decisiones y límites
CPU primero (-ng); GPU pendiente de prueba. Captura mono PCM 16 kHz, seis segundos, umbral de silencio provisional. Si el dispositivo no admite el formato se informa el error. El modelo se carga por consulta; no es streaming. Se usan archivos temporales que se eliminan al terminar normalmente. El sintetizador sigue siendo Windows; la voz neuronal y voces personalizadas están pendientes. No se incluyen ejecutables ni modelos externos. Solo seleccionar binarios de fuentes oficiales. Seis pruebas nuevas más diez previas de audio ejecutadas localmente con subprocess simulado; no se probó PortAudio ni Whisper real ni el empaquetado Windows. No es una validación de latencia o calidad.

## Reversión
Revertir ambos commits mediante GitHub; no se cambia SQLite, GSI, configuración de credenciales ni sistema operativo.
