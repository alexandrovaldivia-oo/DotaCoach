# Etapa 3.6 B.8 — prototipo experimental

Agregar los archivos del ZIP en la raíz del repositorio. No reemplaza módulos existentes ni workflows. No se incluye token, datos reales ni base de datos. Fuente: https://stratz.com/ (API GraphQL https://api.stratz.com/graphql). Uso experimental fuera de partida; permisos de almacenamiento y redistribución pendientes.

## Validación
En GitHub Actions se ejecuta el descubrimiento de unittest. Para desarrolladores con Python: `python -m unittest discover -s tests -p test_stratz_experimental.py -v`. Se esperan 15 pruebas nuevas correctas. Se probó además importación local temporal de la muestra del usuario: 252 relaciones, catálogo de 127 héroes, semana 2968. No se probó red real ni Windows en este entorno.

## Diseño y límites
Cliente con acceso de red deshabilitado por defecto y una consulta por llamada; separación mínima de un segundo entre inicios de peticiones reales de una instancia secuencial. No hay bucle de descarga masiva, reintentos automáticos, interfaz ni ejecutable nuevo. No activar red hasta aclarar permisos. El token se recibe en memoria, no se escribe a disco. Se rechazan redirecciones y errores GraphQL. La semana solicitada al orquestador es una restricción de validación local, no un filtro histórico enviado al proveedor: el significado temporal del parámetro week sigue pendiente. El rango devuelto se conserva literalmente; no se certifica el rango solicitado. Synergy se conserva sin interpretación. El catálogo delimita cobertura estricta; si faltan relaciones, se rechaza el lote, no se inventan ceros. SQLite almacena lotes por héroe/rango/semana, con reemplazo transaccional y reanudación de lotes completos; no publica snapshots globales completos todavía. Usar rutas locales fuera del repositorio para SQLite. No publicar datos reales ni tokens.

## Reversión
Eliminar únicamente los cuatro módulos stratz_*.py nuevos, tests/test_stratz_experimental.py y este documento, o revertir el commit de este parche. No modificar archivos previos. No hay cambios en GSI, Gemini, draft competitivo ni compilación de ejecutables.
