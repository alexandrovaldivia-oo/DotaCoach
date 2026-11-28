# Etapa 4.8 — Perfil rápido experimental
Base: parche 4.7, commit de referencia f2e1867 según captura del usuario.
Objetivo: comparar latencia y precisión con parámetros de decodificación reducidos, sin cambiar modelo ni micrófono.
Fuente: https://github.com/ggml-org/whisper.cpp/blob/master/examples/server/README.md (la documentación del tag b5907 no se pudo abrir).
Implementación: modo opcional, desactivado por defecto, para whisper-server únicamente. Reinicia el servidor al cambiar modo; no cambia el CLI. Usa best-of=1, beam-size=1, no-fallback y no-context. Puede reducir precisión. No modifica texto reconocido ni garantiza uso GPU.
Pruebas: python -m unittest discover -s tests -p test_whisper_enigma.py -v (18/18 en Linux con simulaciones); python -m py_compile draft_offline.py. No se probó Windows ni el servidor real.
Validación: con Turbo, GPU solicitada, Fifine 1, RMS 80 y autoenvío desactivado, comparar las mismas tres frases con modo normal y rápido, descartando primera consulta de cada modo. Registrar texto y tiempo. Objetivo experimental <800 ms y sin perder términos estratégicos; tres frases no certifican 95% de precisión.
Reversión: desmarcar modo rápido, o revertir commit completo. Si el servidor no admite parámetros, desmarcar modo rápido. No desactivar protecciones de Windows. No ejecutar como administrador. Solo uso offline de estudio; no exponer servidor local.
Archivos: draft_offline.py, coach/draft/whisper_residente.py, tests/test_whisper_enigma.py, este documento. Subir conservando rutas; no modificar workflows.
