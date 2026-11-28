# Etapa 4.7 — Whisper residente experimental

Objetivo: evitar cargar el modelo en cada frase, conservando la captura 4.6 y la opción CLI.
Fuente: https://github.com/ggml-org/whisper.cpp/blob/b5907/examples/server/server.cpp (rutas health e inference, parámetros host y request-path).

## Uso
Subir los cuatro archivos del parche a la raíz de main conservando rutas. El workflow existente instala requests y ejecuta test_whisper_enigma.py. Descargar el nuevo artefacto DotaDraftOffline-Windows. No requiere Python local.
En Configurar Whisper elegir whisper-server.exe del paquete b5907 ya descargado y ggml-base.bin. Seleccionar el Fifine que funcionó (ID 1 en la sesión anterior), RMS 80, GPU desactivada. Mantener envío automático y lectura desactivados. Pulsar Escuchar una frase, esperar a Esperando voz, pronunciar la frase. Repetir tres veces sin detener el audio ni cerrar el chat. Medir carga, captura y transcripción. La carga debe ser cero en las consultas siguientes si el proceso sigue activo. Comparar con whisper-cli.exe en la misma configuración. No interpretar captura completa como latencia posterior al habla.

El proceso se inicia bajo demanda, escucha solo en 127.0.0.1, con puerto dinámico y prefijo aleatorio. No usa proxies ni sigue redirecciones. El prefijo no constituye autenticación; otros procesos locales podrían acceder. No abrir puertos ni conceder permisos de red pública. No ejecutar como administrador. No desactivar Smart App Control. Detener audio, cambiar motor o cerrar el chat detiene el servidor; la salida normal también intenta cerrarlo. Un cierre forzado podría dejar el proceso vivo. En caso de fallo seleccionar CLI de nuevo. No se activa asistencia competitiva.

## Pruebas y aceptación
python -m unittest discover -s tests -p 'test_whisper_enigma.py' -v
Las pruebas usan procesos y respuestas simulados. Validar ejecución real en Windows, reutilización del proceso, cancelación y comparación de latencia. GPU y modelos grandes pendientes de pruebas; marcar GPU no garantiza CUDA.

## Reversión
Revertir el commit del parche en GitHub y descargar el artefacto previo. No se altera SQLite ni credenciales. No cambiar workflow.
