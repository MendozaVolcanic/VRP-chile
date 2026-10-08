# Plan de auditoría S150 (2026-10-08): ojos nuevos, con un volcán en erupción

## Por qué existe

Dos cosas pasaron a la vez y ninguna la vio el sistema por sí mismo:

1. **El NRT estuvo caído cinco días** (2026-10-03 07:36 UTC al 2026-10-08) porque venció el token de
   Earthdata, y lo detectó una persona mirando, no una alerta.
2. **Nevados de Chillán entró en actividad fuerte desde el 2026-09-28**, con alertas de MIROVA de 2 a 10 MW
   en los tres sensores. Es la primera vez que el sistema, calibrado casi entero sobre volcanes en reposo
   (señales de 0,05 a 0,5 MW), recibe una señal de erupción en un volcán que no es Láscar. En el cruce de
   producción (26-sep a 2-oct) ya apareció un caso grave: la pasada MODIS del 2026-10-01 08:35, con 5,18 MW
   en MIROVA y el cúmulo nuestro a 0,9 km del cráter, **quedó oculta en el tablero** porque la etiqueta
   `far` se deriva del píxel más caliente de la escena (32,8 km). Es el defecto A46/A81; existe el flag
   `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` (S132) y está apagado.

Además es la primera auditoría hecha con Claude Opus 5.5 sobre este proyecto: el valor está en mirar con
ojos nuevos lo que las 149 sesiones anteriores dejaron de mirar.

## Definiciones del dueño que se dan por dadas

- Objetivo: máxima fidelidad a MIROVA en el perfil réplica (`mirova_equivalent`), con paridad en los dos
  sentidos (publicar lo que MIROVA publica y callar donde calla). Más detecciones, con posibles falsos
  positivos, en el `experimental`.
- VIIRS debe capturar todo lo que MIROVA publica, también lo débil; sólo MODIS puede perder sub-píxel.
- La referencia de MIROVA no sirve igual todo el año (regla A119 en `CLAUDE.md`).

## Frentes (uno por auditor, disjuntos)

| frente | qué mira | pregunta central |
|---|---|---|
| **A. Operación de punta a punta** | workflows (`nrt.yml`, healthcheck, monitor de fallas, retry, sync de MIROVA, Pages), credenciales, cron, frescura de datos | ¿Por qué un apagón de cinco días no disparó ninguna alerta que alguien leyera? ¿Qué otro apagón silencioso es posible hoy? ¿El sistema se recuperó entero tras rotar el token (hueco del 3 al 8 de octubre rellenado en los 11 Tier A)? |
| **B. Por uso: lo que ve el operador durante la erupción** | `frontend/index.html`, `diario.html`, `mosaico.html` y los datos de Nevados de Chillán del 2026-09-20 a hoy | Cadena promesa, supuesto, control: para cada cosa que el tablero muestra o esconde de Chillán, ¿la etiqueta dice la verdad? Toda compuerta que oculta una pasada (far, inner, topes, supresiones) evaluada contra lo que MIROVA publicó esas mismas pasadas |
| **C. Magnitudes y constantes del pipeline en régimen de erupción** | `pipeline/` (constantes que deciden detección, cúmulo, etiqueta, magnitud, topes y pisos) | Cada constante calibrada en reposo: ¿qué hace con una señal de 2 a 50 MW, muchos píxeles y un cúmulo extendido? ¿Hay topes que recorten magnitud real (por ejemplo el tope de 5 MW de D9), radios que partan el cúmulo, o compuertas que una erupción dispare al revés? |
| **D. Instrumentos de decisión** | evaluadores y bancos (`experiments/_s149_prereg_invierno/`, `experiments/_s146_ab_sin_test1/evaluar.py`, `banco_paridad`, `scripts/libro_de_cuentas.py`, `scripts/calidad_referencia_mirova.py`, la auditoría automática semanal) | ¿Cada instrumento mide lo que dice medir? S150 encontró uno que comparaba el gemelo contra el brazo equivocado y daba un falso 90 %. Buscar esa clase de defecto: etiqueta, denominador, ventana, zona horaria, pareo, nulo |

Lo que **no** se audita: la fidelidad al paper (S138, S146 y S149 la cubrieron), la conectiva y la banda 22
(las mide la prueba A de Chillán en paralelo, en `experiments/_s150_ndc/`; no tocar esa carpeta).

## Entrega

Informes en `docs/audit_s150/AUDITOR_<frente>.md`; scripts en `experiments/_s150_audit/<frente>/`. Un
verificador con contexto limpio revisa después los hallazgos de gravedad 4 y 5. La síntesis va a
`docs/AUDIT_S150.md`, con la lista de pruebas de campo (qué mirar en el tablero, qué decide).
