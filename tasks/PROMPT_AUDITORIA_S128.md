# Prompt de auditoría S128 — evidencia exógena

> Pegar completo al inicio de la sesión. Diseño y justificación:
> `docs/superpowers/specs/2026-08-30-auditoria-s128-design.md`.

```
Auditoría S128 de VRP Chile. Antes de nada, tres cosas que NO son opcionales.

═══════════════════════════════════════════════════════════════════════════
POR QUÉ ESTA AUDITORÍA ES DISTINTA (leer antes de planificar)
═══════════════════════════════════════════════════════════════════════════

Se midió el rendimiento de las once auditorías previas. El resultado es
inequívoco: **el rendimiento viene de estrenar un EJE DE COMPARACIÓN, no de
mirar más hondo el mismo**.

    S105  0 % de eje nuevo  -> ningún hallazgo científico
    S122  ~8 %              -> ninguno
    S116  ~17 %             -> ninguno
    S124  ~70 %             -> grilla UTM
    S127  ~75 %             -> corona anulada aguas abajo, 3 guards

Corolario vinculante: **está PROHIBIDO repetir el barrido general de 6-8 ejes**
(misión / código / reglas / data / git / docs). Rindió cero dos veces.

Y hay dos fugas que explican por qué siempre queda inventario:
  · nueve hallazgos se REDESCUBRIERON porque se cerraron con prosa en vez de
    guard — uno apareció en CUATRO auditorías, y uno refutado en S121 volvió
    como hallazgo nuevo en S125;
  · S121 cerró con 19 hallazgos sin verificar y S125 con 9. Esa es, literal, la
    materia prima que la auditoría siguiente reporta como nueva.

═══════════════════════════════════════════════════════════════════════════
FASE 1 — LA DEUDA. Es la puerta de entrada, no un anexo.
═══════════════════════════════════════════════════════════════════════════

Los 28 hallazgos sin verificar, YA LOCALIZADOS (conteo verificado, no estimado):

  · **19 en `docs/AUDIT_S121_MEJORA_INTEGRAL.md`** — cada uno marcado literal
    con `- **Verificación**: sin verificación individual`. Sacalos con:
        grep -n "sin verificación individual" docs/AUDIT_S121_MEJORA_INTEGRAL.md

  · **9 en `docs/AUDIT_S125_PROFUNDA.md` §3 "SIN RESPALDO"**, y no son menores:
        D5   "calibración lograda, ratio 1,35×" vs la tabla de hoy
        D13  el script que la produce no está en el directorio citado
        D14  el r = −0,23 que sostiene "la máscara no es el driver del gap" — SIN SCRIPT
        D9   residuo "24-83× post-cap", anterior a nadir-fijo
        A54  el 95,4 % de FP físicamente reales — la creencia más load-bearing del catálogo
        A12  ΔT por volcán: NO reproduce
        A84  su probe nunca entró a git
        4 adopciones operacionales cuyo "doc de adopción" es un plan, no un resultado
        R2   ratio suma/máximo

⚠️ Dos de esos nueve —**D14 y A54**— son fundamento de decisiones vivas. D14 ya
está REABIERTA por otra razón (la cita no verificable); que además su correlación
no tenga script es la segunda pata floja de la misma divergencia.

Cada uno termina en UNO de tres destinos, sin punto intermedio:
    CONFIRMADO con script · REFUTADO con script · IMPOSIBLE, y por qué.

Y estas contradicciones internas, que son deuda de la misma clase:
  · `docs/MIROVA_DIVERGENCES.md:562` — tabla roadmap CONGELADA EN S35: lista D8
    como "NUEVO pendiente" (está resuelta) y D5 como cerrada (S125 la rebajó y
    le invirtió el signo: 1,35× -> 0,75×).
  · A82 fue REBAJADA en S124, pero A83 y A84 heredan la versión fuerte sin
    caveat — en el MISMO archivo donde más abajo sí se parchó.
  · Colisión de identificadores: "D2" nombra dos cosas distintas y "D8" también.
    Un grep de "D2 resuelto" arrastra un cierre falso. Es A89.

═══════════════════════════════════════════════════════════════════════════
FASE 2 — EL EJE NUEVO: EVIDENCIA EXÓGENA
═══════════════════════════════════════════════════════════════════════════

Las once auditorías midieron contra MIROVA o contra los papers de MIROVA leídos
a través de NUESTRAS síntesis. Toda la evidencia de calidad del sistema descansa
en una sola fuente que sabemos incompleta.

Dos ventanas al exterior (NHI-v1 queda EXCLUIDO por decisión de Nicolás):

── A. El archivo de TIF/KMZ ────────────────────────────────────────────────
`../mirova-tif-archive` (local). 1.966 TIF, 11 volcanes × 3 sensores.
Una banda float64, EPSG:4326, radiancia espectral MIR. MODIS 51×51 (~1 km),
VIIRS750 67×67, VIIRS375 134×134. Índice en `index.csv`.

⚠️ LÍMITES, decirlos antes de construir nada encima: son **11,6 días**
(2026-05-08 a 05-20). NO hay VRP numérico, NI banda TIR (así que el NTI no se
puede reconstruir), NI la máscara de píxeles que MIROVA alertó, NI ángulos de
vista. Ventana sin actividad fuerte (máx 1,909 ≈ 339 K, cero saturados).

── B. Los papers, verbatim ─────────────────────────────────────────────────
Los PDF de `documentacion/`, no nuestras síntesis. Ya se sabe que hay al menos
un archivo que parece paper y es una página de error de Elsevier
(`laiolo2022_epsl_openvent.md`, 1.335 bytes, "IP blocked").

── Las cinco sondas, en orden de rendimiento esperado ──────────────────────

P1 · LA GRILLA REAL. Los tres sensores comparten el BORDE OESTE idéntico pero
     no el norte: MIROVA fija una esquina, no el centro. Y el `LatLonBox` del
     KMZ —de donde salió nuestro `mirova_center` en S80— NO coincide con los
     bounds del TIF (~1,6 km en Villarrica VIIRS375). Ataca D17 desde la única
     evidencia externa que existe.

P2 · CONTRASTE AL CRÁTER DONDE NO DEBERÍA HABERLO. En esos 11,6 días, Copahue,
     Lastarria y Tupungatito no tienen NINGUNA escena con contraste al cráter
     sobre ~175 cada uno en la imagen de MIROVA. Y nosotros, en la MISMA ventana,
     publicamos **Copahue 91 · Lastarria 79 · Tupungatito 87** detecciones con
     vrp>0 (verificado sobre `data/mirova_equivalent/`). Son 257 detecciones que
     la imagen de la referencia no respalda. **Es la primera vez en 127 sesiones
     que un falso positivo nuestro se podría afirmar con evidencia EXTERNA** y no
     con nuestro propio juicio.
     Cobertura total de la ventana: 1.551 records nuestros, 970 con vrp>0, en los
     11 Tier A. Material de sobra; el cuello es la ventana de 11,6 días, no el n.

P3 · CUÁNTO PIERDE `latest.php`. Su README dice ~80 % de las pasadas. **D2
     ("el CSV cubre ~70 % de VIIRS") NUNCA SE MIDIÓ** y es la creencia más
     load-bearing del catálogo: toda métrica de recall se corrige mentalmente
     con ese número. El archivo tiene 1.966 pasadas con timestamp. Medirlo.

P4 · RADIANCIA CONTRA RADIANCIA. Detecta errores de banda, calibración o
     unidades que son invisibles desde adentro. **Pero tiene dos costos que hay
     que decidir ANTES de empezar, no a mitad:**
     (a) no guardamos L1B crudo, así que comparar radiancia contra radiancia
         exige RE-DESCARGAR los granules del 08-20 de mayo para 11 volcanes, con
         el disco al 98 % (12 GB libres). Verificar espacio primero.
     (b) la alternativa barata es comparar nuestro `bt_k` persistido contra la
         radiancia del TIF vía Planck — pero **la unidad de la banda del TIF NO
         está declarada en ningún tag**; que sea W m⁻² sr⁻¹ µm⁻¹ es una
         inferencia por consistencia con Planck, no un dato. Si se toma ese
         camino, la conclusión hereda esa incertidumbre y hay que escribirlo.
     Recomendación: dejar P4 para el final y sólo si P1-P3 no consumieron la
     sesión. Es la sonda de mayor costo y menor certeza de las cinco.

P5 · VERIFICACIÓN VERBATIM DE LAS CITAS QUE GOBIERNAN DECISIONES.
     Empezar por las dos de D14, que S128 reabrió:
     (a) "Laiolo 2026, textual: no atmospheric correction or cloud-contamination
         automatic filtering" — esa frase NO existe en ningún PDF del repo. Su
         origen es `Vault/10_Bibliografia/laiolo2026switching.md`, con cabecera
         `ai_generated: true, confidence: medium`. DOI 10.1007/s00445-025-01932-y.
     (b) EL CORTE DE 0,1 MW. La misma nota atribuye a MIROVA: "We do not consider
         minor inflections at VRP<0.1 MW because these are likely cloud and/or
         bad geometry". Si es cierto, reencuadra el piso VRP Y la mitad del
         frente de sobre-detección: nuestras detecciones de artefacto están en
         0,04-0,06 MW y las 8 que perdió el brazo corona en S127 estaban en
         0,021-0,042 MW.
     ⚠️ NO ACTUAR sobre (b) hasta tener el PDF. La fuente es la misma nota no
     verificada que originó el problema. Verificarla es la tarea; usarla, no.
     **Cómo conseguir el PDF** (invocar la skill `investigacion` ANTES de buscar
     a mano; agotar lo local primero, que es su regla): el DOI es
     `10.1007/s00445-025-01932-y` (Bull. Volcanol., Springer). Orden: (1) el
     Vault y `documentacion/nuevos/`; (2) Zotero — la nota trae
     `zotero://select/library/items/M7NUCUVL`, así que puede estar ahí; (3)
     Crossref / Semantic Scholar / OpenAlex por DOI; (4) recién entonces web.
     Si no se consigue, D14 queda ABIERTA y se dice así — no se cierra con una
     paráfrasis por segunda vez.
     Extender a TODA cita en itálicas de MISSION.md y MIROVA_DIVERGENCES.md:
     ¿existe el PDF? ¿dice eso?

═══════════════════════════════════════════════════════════════════════════
LO QUE YA SE SABE Y NO HAY QUE REDESCUBRIR
═══════════════════════════════════════════════════════════════════════════

De los siete barridos que prepararon esta auditoría (todos con datos):

  · **Ground truth**: MODIS existe SÓLO en Láscar (50 alertas; los otros diez
    suman 0 en el canal nocturno). Cualquier veredicto MODIS fuera de Láscar es
    INDEFINIDO, no débil. NdC n=10 en 8 meses: el n=3 de S127 es su régimen
    normal, no mala suerte.
  · El filtro nocturno `3 <= hora_UTC <= 9` descarta 3 noches REALES en la
    ventana del veredicto de S127 (Láscar MODIS, local 21:00) — chico, pero
    Láscar es el único con GT MODIS. Nuestro lado usa elevación solar; la
    referencia usa una ventana de horas. **Filtros asimétricos entre las dos
    series que se comparan.**
  · 76 % de los registros OCR pierden la distancia por mojibake (`distâ‰ˆ`), y
    donde la columna `Distancia_km` existe contradice a la nota de la misma fila
    por un orden de magnitud.
  · **93 % de los pares volcán×sensor conviven con más de un esquema** (hasta
    12). Hay huecos de cobertura en 2025-11/12 que nadie registró. Y NINGÚN
    record guarda con qué versión del pipeline se produjo: un número publicado
    puede cambiar sin dejar rastro.
  · **11 flags están ON sin A/B con reproceso real**, entre ellos
    `enable_vrp_tir_consistency_gate`, que S81 ya demostró insuficiente. De los
    que SÍ tuvieron A/B pareado no se revirtió ninguno.

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA AUDITORÍA
═══════════════════════════════════════════════════════════════════════════

  1. **Cierre por GUARD, no por corrección.** Ningún hallazgo pasa a CONFIRMADO
     / FALSO / OBSOLETO sin un test que lo mida, o la razón escrita de por qué
     no se puede. Es el cambio que separa a S127 (0 reincidencias) del resto.
  2. **Estrenar eje, no repetir barrido.**
  3. **Los pendientes se publican** y son la puerta de entrada de S129.
  4. **A89 vale para el auditor**: "no aparece en ningún lado" casi nunca
     significa que no esté. Un grep que no encuentra devuelve CERO, y el cero se
     lee como ausencia. En S127 pasó cinco veces y las cinco fue de quien
     auditaba. Antes de escribir "esto no se usa", trazá cómo lo LEE el código.
     Para flags: leer `pipeline.profile`, nunca el YAML.
  5. **Estratificar por volcán**, no sólo por sensor.
  6. **Un par por noche**, máximo de ambos lados.
  7. Todo número sale de un script que lo persiste (S91). Ninguno a mano.
  8. Read-only. Tocar `pipeline/` exige ciclo A45 completo.
```

## Nota sobre cómo se construyó este prompt

Salió de siete barridos paralelos —archivo de TIF, clasificación de creencias por tipo de
evidencia, historial de adopciones revertidas, repos hermanos, ground truth end-to-end,
idempotencia y estabilidad, y meta-análisis de las once auditorías— más verificación propia
de los hallazgos que tocaban decisiones vivas.

La decisión de alcance (eje exógeno **sin** NHI, deuda primero, D14 reabierta) es de
Nicolás.

## Verificación de que esto se puede ejecutar (hecha en S127, no asumida)

| requisito | estado |
|---|---|
| los 28 pendientes son localizables | **sí** — 19 por `grep` literal en S121, 9 enumerados en §3 de S125 |
| `rasterio` instalado | **sí** (también numpy, scipy, pyproj; falta `osgeo`, no hace falta) |
| el archivo de TIF está local | **sí**, `../mirova-tif-archive`, 1.966 TIF (133 MB de dato útil) |
| nuestros records cubren la ventana del archivo | **sí** — 1.551 records, 970 con vrp>0, en los 11 Tier A |
| espacio en disco | ⚠️ **12 GB libres, 98 % usado**. Alcanza para P1-P3 y P5; P4 exige re-descargar granules |
| el PDF de Laiolo 2026 | **NO lo tenemos**. P5(b) depende de conseguirlo |

**Lo único que puede trabar la sesión es P4** (re-descarga de granules con el disco al 98 %)
y **P5(b)** (sin el PDF no se puede verificar el corte de 0,1 MW). Las dos están marcadas
arriba con su alternativa. P1, P2, P3 y P5(a) corren con lo que ya hay en disco.
