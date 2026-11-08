# Bloque de arranque S176 (cierre de S175, 2026-11-08 17:30 UTC)

> **Estado fijado con trabajo en curso.** Al escribir esto seguía vivo el verificador limpio del PR #964 (Fable, carpeta
> `C:\Users\nmend\vrp-temporales\s175_verpr\964\`, informe `INFORME.md`, 33 KB, sin cambios desde las 16:37 UTC, esperando
> corridas de mutaciones). Escribe sólo en su carpeta. Leer el informe antes de creerle a esta tabla; si no trae veredicto, relanzar
> el verificador. Nada más corre.
>
> El bloque anterior sigue entero en `tasks/BLOQUE_ARRANQUE_S175.md`: sus decisiones 1 a 6 se resumen abajo donde siguen vivas.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| #956 ficha CPLT v1.19, SINTOMAS, regla de reversión | MERGEADO 15:23:44 UTC | `1b66b7490`; verificador R2 MERGEABLE (`C:\Users\nmend\vrp-temporales\s175_verpr\956\INFORME_R2.md`) |
| #957 recall por pasada, tabla, VRP truncado del OCR | MERGEADO 15:23:37 UTC | `6cf57cb2b`; verificador R2 MERGEABLE (`...\957\INFORME_R2.md`) |
| #959 guardia MODIS por volcán, caídas a K como K | MERGEADO 15:23:32 UTC | `71ecc61b0`; verificador R2 MERGEABLE (`...\959\INFORME_R2.md`) |
| #963 seguimientos chicos | MERGEADO | `1a49293dd`; verificador MERGEABLE (`...\963\INFORME.md`); deja 5 de 6 fallas locales fuera |
| #958 «MIROVA confirmó» por misma pasada y tooltip | MERGEADO 16:06:50 UTC, publicado | `a7a6ae360`; el texto aparece 2 veces en la página en línea; deploy en verde |
| CI de main | VERDE | `a7a6ae360` y `1a49293dd` completed success |
| #955 síntesis de la auditoría S175 | BORRADOR, CI verde | `43b330ef9`; verificador MERGEABLE CON CAMBIOS, atendidos; **falta el anexo del audit del 2026-11-09** |
| #964 lector de V750-A en una sola versión | BORRADOR, CI verde, **verificador en curso** | `dd982437c`; 137 escenarios, 173 mutaciones, 48 de 48 medidas con `--solo` por aserción |
| #965 mapa «Todos los pixels» | BORRADOR, CI verde, falta verificador | `b7a8a177a`; Chillán de 137 a 182 de 182 records; navegador con página parchada en memoria, no sirviendo la rama |
| #966 token rechazado deja el NRT en rojo | BORRADOR, CI verde, falta verificador | `c316e0a24`; 55 pruebas, 15 de 15 mutaciones, 21 de 21 escenarios con token bueno idénticos |
| Auditoría S175: hallazgos sin verificador | 0 quedan | 33 pendientes: 27 confirmados, 6 en parte, 0 refutados (V33A, V33B, §6 de `docs/AUDIT_S175.md` en #955) |
| F5b posición con láminas PNG | HECHO, conclusión central caída | V5B: la lámina VIIRS georreferencia, pero el selector borra la mancha saturada (V5B-01); el «foco a 1 a 2,5 km» del 351 no se sostiene |
| Sombra de V375-E y V750-A | 5 noches (11-03 a 11-07) en los 3 sensores y 11 volcanes | censo de esta sesión; 0 caídas a K; V750 con ROI `sens` en PCC y Tupungatito desde #939 |
| Guardia MODIS | VERDE sin avisos | `data/audit_continuous/guardia_modis_latest.json` 2026-11-08 01:48 UTC |
| NRT | último verde 2026-11-08 12:47 UTC | 4 h 36 min sin corrida al cierre; alarma a 12 h: **mirar primero** |
| `loop/activo` | con main integrado | `git cherry loop/activo origin/main` da 0 tras el merge `3b306b541`; no corrió la suite desde el merge de la mañana |
| Plan semanal | 11 % (Fable 16 %), reinicio 2026-11-15 12:00 UTC | `get_usage` 17:23 UTC |
| Disco | C: 19 GB, D: 4,5 GB | `df -h` 17:23 UTC; 24 worktrees |

## b. Decisiones que espera el dueño

Nicolás respondió «sí a todo lo que recomiendes» el 2026-11-08 15:3x UTC: el arreglo del token, el del mapa, #958 con tooltip, #963, «la
tabla decide» más el conteo en #957, S139 histórica y re-correr F5b. Esas ya no se preguntan; siguen abiertas estas:

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Merge de #966 (token) y #965 (mapa) | frase de Nicolás tras su verificador | Sí a ambos cuando su verificador no deje gravedad 3 |
| 2 | Merge de #955 | tras el anexo del lunes | Sí |
| 3 | Merge de #964 y luego medidor completo (unas 44 h con 4 hilos) | merge antes o después del medidor | Merge después del verificador; el medidor corre sobre main ya con #964 |
| 4 | Sello de V750-A | tras medidor, vara MATLAB en §4.1 y verificador de `equivalencia_v750a.py` | Esperar esas tres cosas |
| 5 | Una caída a K deja la guardia en VIGILANCIA_CIEGA 14 días (`DIAS_AVISO_CAIDA`) | dejar, o bajar la ventana | Dejar; decirlo si hace ruido |
| 6 | Protección de rama de main (decisión 1 del bloque S175) | checks obligatorios o dejar | Checks `pytest` y `bateria-v750a` |
| 7 | Decisiones 2, 3 y 4 del bloque S175 (VPR952-04, pre-registro l. 409, fila 4 por cenit) | ver ese bloque | Las recomendadas ahí |
| 8 | Limpieza de worktrees viejos de S172 a S174 en D: (unos 12 GB) y temporales `s174-*` en C: (A38) | hacerla o dejar | Hacerla: D: está en 4,5 GB y el medidor necesita holgura |

## c. Lo aprendido

- **El disco lo come el archivo de paginación (REGLA GENERAL).** `C:\pagefile.sys` llegó a 35 GB con la memoria comprometida en 61,8 de 65,9 GB (Chrome 17 GB, Claude 14 GB). Destino: memoria `feedback_s175_pagefile_disco.md` (hecho).
- **Antes de medir, ver si lo medido es lo que se sella (proyecto).** El lector de V750-A existía en dos versiones; el medidor corrió horas sobre una que iba a cambiar. Destino: memoria `feedback_s175_lecciones.md`.
- **Un verificador también se equivoca (REGLA GENERAL).** El autor de #956 mostró que la cifra del verificador (662, 15,6 h) estaba contaminada por un reproceso, y el de #957 corrigió la banda y el conteo. El mecanismo es que cada uno compruebe al otro, no que uno mande. Destino: misma memoria.
- **Un nulo o una validación fuera de muestra separa la vara del azar.** VX y V5B tumbaron dos conclusiones de «mismo foco» con permutaciones (93 % y 73 a 77 % de acierto por azar). Destino: misma memoria y A107/A110, ya vigentes.
- **Un medidor que escribe el resumen sólo al final pierde todo si se detiene** y deja 48 MB por mutación. Propuesta: resumen incremental y `--dest` en C:. Destino: S176, al relanzarlo.
- **Heredocs con `\` otra vez** (armar el verificador): usar Write o `chr(92)`. Regla ya escrita en el bloque S175.

## d. Problemas abiertos e hipótesis

| Ítem | Etiqueta |
|---|---|
| El NRT lleva más de 4,5 h sin corrida al cierre | CONFIRMADO; causa SIN VERIFICAR (la cadencia de la tarde es irregular, V33A midió atraso mediano 4,97 h con cron externo) |
| #960 y #962: una corrida con un volcán caído por corte de NASA | CONFIRMADO; las de hoy aún no corrían al cierre |
| VX-04: Planchón-Peteroa Terra 2026-11-02 01:15 sigue NRT, en K, 6 días después | CONFIRMADO el hecho; causa SOSPECHA |
| V33B-02: `alerta_protegida` acepta filas sólo OCR anteriores al hito 2026-06-11 | SOSPECHA, g2 |
| #966: una noche con una sola plataforma y su colección con 403 deja rojo sin culpa del token | CONFIRMADO en el diseño; a evaluar por su verificador |
| `pipeline/store.py:693` repite «3-5 days» (mediana real 13,8 h) | CONFIRMADO; toca `pipeline/` (A45) |
| `scripts/token_edad.py` dice «ok» con un token con salto de línea | CONFIRMADO (autor de #966) |
| El tooltip de #958 corrigió la frase, pero el rótulo «sin publicación de MIROVA» (`frontend/index.html:2352`) sigue absoluto | CONFIRMADO |
| 44 h de medidor con 4 hilos | SOSPECHA: estimación del autor de #964 |

## e. Lo que ya está cerrado y no hay que rehacer

- #956, #957, #958, #959 y #963 en main, cada uno con verificador limpio de otro modelo y frase de Nicolás.
- «Mismo foco o cúmulo» (302) y «foco a 1 a 2,5 km» (351): retirados con evidencia. No volver a citarlos.
- Los 33 hallazgos que faltaban: verificados. No relanzar sus verificadores.
- Issue #961 de disco: cerrado tras el reinicio.
- `loop/activo` con #945, #952, #953 y #954: integrados el 2026-11-08 (suite local 3.254 pasan, 6 fallas, 5 ya resueltas en #963).
- El medidor de V750-A sobre la versión de main sin N-3: descartado a propósito (dos veces), no retomarlo.

## f. Prompt para la próxima sesión

```
Sesión S176 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; HEAD contra git ls-remote origin -h
   refs/heads/loop/activo; df -h /c /d; get_usage. gh pr list --state open. Último run de nrt.yml (al cierre de S175 llevaba 4,5 h sin
   correr), sombra-34.yml, sombra-codigo-mirova.yml y audit-weekly.yml.
2. Lee: CLAUDE.md; tasks/BLOQUE_ARRANQUE_S176.md entero; las entradas del 2026-11-08 de la bitácora §6 de tasks/LOOP_OBJETIVOS.md;
   C:\Users\nmend\vrp-temporales\s175_verpr\964\INFORME.md (si no tiene veredicto, relanza el verificador de #964).
3. Trabajo, en paralelo donde se pueda (máximo 5 agentes, sólo con holgura de memoria comprometida):
   a. Primero contesta a Nicolás, midiendo, sus dos preguntas: «porque no se estan mostrando datos para el resto de los volcanes? entendi
      que estaba corriendo el nrt para los 43» y «como va nuestra paridad de magnitudes y el resto de los datos» (por sensor).
   b. Trae main a loop/activo. Lunes 2026-11-09: lee el audit semanal, el primero con la vía MODIS (ver #915 y #936); escribe el anexo de
      #955 y pide su merge.
   c. Verificador limpio de otro modelo para #966 (token, autor Opus) y #965 (mapa; sirve la rama de verdad en navegador); merge con frase.
      El token se rota antes del 2026-11-27.
   d. #964: con verificador limpio, merge con frase; luego medidor completo con --dest en C:, resumen incremental, y la vara MATLAB
      (experiments/_s162_v750a/vara_matlab_v750a.py) en el §4.1 antes del sello.
   e. Aprobado por Nicolás, sin preguntar otra vez: conteo de filas OCR que descarta la tabla (decisión 1 de #957), sacar S139 de la suite
      como histórica, re-correr F5b con la máscara corregida.
   f. Pedidos nuevos de Nicolás:
      - Plan para que GPT Codex pueda revisar, entender y auditar nuestro código.
      - Auditar el visualizador y mirovaweb.it, y cómo se relacionan: vista de las últimas pasadas por volcán y sensor, descarga de GeoTIFF
        para ubicar los píxeles, tarjetas con menos información, agrupar por sensor y no por satélite. Con navegador real y antes de proponer.
4. Reglas duras: pipeline/ congelado durante la sombra (excepciones: ROI de V750, emergencias del NRT, el token autorizado);
   nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); merge a main sólo con frase de Nicolás y gh pr merge
   --match-head-commit; sólo EARTHDATA_TOKEN (A71); verificador limpio de otro modelo antes de aceptar un resultado y también el autor
   comprueba al verificador; effort high explícito y carpeta temporal propia; máximo 2 procesos pesados locales y parada bajo 3 GB
   libres en C: o D:; mira pagefile.sys ante una caída de disco; git add por archivo; nunca git stash; date -u antes de cada encabezado de
   bitácora; un PR sin checks no es verde; heredocs sin \v ni \t.
5. Si la sesión no alcanza (contexto sobre 50 % o cambio de día): commitea, anota en la bitácora, escribe el bloque S177 con /cierre.
```
