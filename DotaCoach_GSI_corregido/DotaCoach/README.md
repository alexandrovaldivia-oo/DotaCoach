# Dota 2 AI Coach

Entrenador de Dota 2 en tiempo real: overlay, voz y consejos con IA.
Version 0.1 (etapa 3: arquitectura base, sin validar todavia contra una partida real).

## Como probarlo

1. Python 3.10 o superior (solo para desarrollo; el producto final sera un .exe portable).
2. `pip install -r requirements.txt`
3. Dota 2 > Propiedades > Opciones de lanzamiento: `-gamestateintegration`
4. **Primero el diagnostico** (sin IA ni voz): `python main.py --diagnostico`
   Juega una partida, pulsa Ctrl+C y revisa la carpeta `gsi_logs` de tu usuario:
   `campos_vistos_....txt` dice que datos recibes de verdad.
5. Coach completo: `python main.py` (pega tu API key de Gemini en el overlay).
6. Pruebas: `python -m unittest discover -s tests -v`

Registros de errores: carpeta `.dotacoach` de tu usuario, archivo `coach.log`.

## Estructura

| Modulo | Responsabilidad |
|---|---|
| `coach/gsi/` | Crear el .cfg, recibir GSI, grabar JSON crudo (diagnostico) |
| `coach/state.py` | Convierte el JSON de GSI en un estado tolerante a datos faltantes |
| `coach/eventos.py` | Detecta cambios: nivel, objeto nuevo, muerte, racha, partida nueva |
| `coach/reglas.py` | Reglas deterministas (temporizadores, definitiva). La logica pura NO va a la IA |
| `coach/datos/` | Constantes y nombres que cambian con los parches |
| `coach/ai/` | Proveedor de IA intercambiable (hoy Gemini con tu key) |
| `coach/persona.py` | Personalidades y reglas globales del texto hablado |
| `coach/voice/` | Voz (hoy edge-tts, en la nube, sin instalar modelos) |
| `coach/ui/` | Overlay minimo; reemplazable en la etapa 4 |
| `coach/motor.py` | Une todo y decide que se dice y cuando |

## Reglas de diseno

1. Ninguna funcion entra sin una fuente de datos comprobada.
2. Cada pieza en su modulo: quitar o cambiar algo no obliga a reescribir.
3. La IA solo redacta y explica; las decisiones salen de reglas y datos.
4. Nada esencial depende de tu GPU. Lo local (voces clonadas) sera opcional.
5. La voz del Peon es un estilo de texto opcional, no parte del nucleo
   (la voz original de Warcraft III pertenece a Blizzard: riesgo si el producto se vende).
6. Sin ventajas injustas: solo GSI y lo que el jugador ve en pantalla. El modo competitivo apaga los consejos.

## Pendiente y por validar

- [ ] Confirmar con `--diagnostico` que campos entrega GSI como jugador (enemigos, edificios, draft).
- [ ] Verificar las constantes de `coach/datos/constantes.py` con el parche actual.
- [ ] Probar el overlay y la voz en Windows con una partida real (no se pudo probar aqui).
- [ ] Opcion de lanzamiento de Steam: confirmar si sigue siendo necesaria.
- [ ] Objetos: ampliar `coach/datos/nombres.py`.

## Hoja de ruta (tus etapas)

1. Viabilidad (hecha, falta validar GSI) - 2. Alcance - 3. Arquitectura (esta base) -
4. Interfaz - 5. Conexion con Dota - 6. Analisis en tiempo real - 7. Motor de recomendaciones -
8. Voz y personalizacion - 9. Analisis post-partida - 10. Pruebas y lanzamiento.

## Correccion GSI (26/11/2026)

La conexion real fue validada con un CFG de seis componentes: provider, map,
player, hero, abilities, items. El diagnostico y el coach usan esta configuracion
por defecto. Los componentes experimentales no se solicitan automaticamente.
El descubrimiento exige game/bin/win64/dota2.exe y no elige a ciegas entre dos
instalaciones completas. En ese caso, agregar la clave ruta_cfg al JSON existente
~/.dotacoach/config.json, apuntando a game/dota/cfg de la instalacion correcta.
No compartir ese JSON: puede contener la clave API.
Los CFG anteriores se conservan como .bak si es necesario cambiar su contenido.
El catalogo de campos se guarda al primer mensaje, aproximadamente cada diez
segundos mientras llegan datos y al cerrar normalmente con Ctrl+C.
Validacion pendiente: ejecutar el artefacto Windows de GitHub Actions con Dota
cerrado, comprobar la ruta impresa, abrir Dota y recibir datos en una practica.
No utilizar el coach en ranked hasta verificar las condiciones de Valve.
