# Etapa 4.6 — Captura adaptativa y diagnóstico de latencia

Solo estudio offline. Sin lectura de memoria, automatización del juego ni nuevas consultas a STRATZ. Basado en el ZIP de etapa 4.5; no se verificó el commit remoto completo.

## Cambios
- Selección de dispositivo PortAudio y medidor RMS (escala visual relativa, no dB).
- Umbral configurable, espera inicial de 8 s, dos bloques de 100 ms por encima del umbral para activar, prerroll de 400 ms, fin por 500 ms de silencio, límite de 15 s. Es una heurística de energía, no un VAD neuronal; ruido y pausas largas pueden afectar el resultado.
- Medición separada de captura y transcripción (incluye inicio del proceso y carga del modelo, no incluye IA ni síntesis).
- GPU opcional: elimina -ng; no garantiza CUDA ni verifica que se haya usado GPU. Conservar CPU para el binario actual.
- No modifica las dependencias, configuración, GSI o SQLite. No cambia la síntesis de voz.

## Pruebas
python -m unittest discover -s tests -p 'test_whisper_enigma.py' -v
python -m unittest discover -s tests -p 'test_voz_enigma.py' -v

## Validación Windows
Abrir el artefacto nuevo, configurar el mismo whisper-cli y modelo base, listar micrófonos, seleccionar el micrófono real, dejar GPU y envío automático desactivados. Pulsar Escuchar una frase y decir «Hola Enigma, soy mid y mis aliados son Lion y Axe». Observar nivel RMS y tiempos. Si no detecta voz, probar umbral 30 o 50 con el micrófono correcto. Probar también silencio. La calidad de transcripción y latencia reales siguen pendientes. No desactivar Smart App Control.

## Reversión
Revertir el commit de este parche para recuperar los tres archivos anteriores; eliminar este documento. No hay migración de datos.
