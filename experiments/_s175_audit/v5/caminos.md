# Caminos por los que cada afirmación podría estar mal (F5, verificador V5)

Escrito ANTES de abrir ningún archivo citado ni script del auditor. Sólo tenía título, archivo:línea y gravedad.
Hora del servidor al empezar: Sat, 07 Nov 2026 08:47:57 GMT (header Date de la API de GitHub).

## Caminos generales (valen para las 9 afirmaciones)

G1. La copia local está atrasada: el script del auditor lee el worktree (que puede no estar en 752d348bc) y no la copia en
    `C:\Users\nmend\vrp-temporales\s175_audit\main` o `git show 752d348bc:...`. Las líneas citadas (archivo:línea) pueden
    corresponder a otro commit.
G2. La vara es otra: el auditor usa una etiqueta, un predicado o una referencia (consolidado vs snapshot, raíz vs
    `mirova_v1_snapshot`) distinta de la fijada en el preámbulo (sha256 f833bfde... del snapshot; dee76837... de la raíz).
G3. El instrumento mide otra cosa: un conteo sobre un denominador distinto (noches vs pasadas vs filas), una ventana que
    no contiene el fenómeno, o un script que da el mismo número si el fenómeno no existe (pregunta 2 del instrumento).
G4. El script no corre hoy o corre distinto (dependencias, rutas con `cd /d` de cmd.exe, salida de una corrida vieja
    guardada que no corresponde al código actual).
G5. El «control positivo» del auditor no es positivo: algo que se esperaba que cambiara no cambia, o cambia por otra razón.
G6. Cifras heredadas de documentos anteriores (CLAUDE.md, MAPA, handoff) sin recomputar.
G7. Transcripción a mano de un número del script al hallazgo (regla S91): el título dice un número que la salida no dice.
G8. La línea citada existe pero no contiene lo que el hallazgo dice (cita desplazada, función renombrada).

## 301: distancia del OCR no sirve de vara de posición; casi todos los aciertos de otra fuente se apoyan en ella
(scripts/referencia_mirova_unificada.py:134, gravedad 3)
- «casi todos» sin proporción reproducible: ¿cuántos de cuántos, en qué ventana y para qué fuente (TIF, PNG, tabla)?
- La distancia del OCR podría ser una distancia a la celda/pixel y no al cráter: "no sirve" depende de qué se compara
  (posición absoluta vs clase summit/far). El reparo puede ser que la vara se use sólo para clase y no para posición.
- Puede que el OCR sí coincida con la tabla cuando ambos existen en la misma pasada (el OCR ya sea copia de la tabla):
  entonces "se apoyan" es circular, no un defecto del OCR.
- La línea 134 puede ser otra cosa (un fallback, un merge) que el auditor interpretó como el origen de la distancia.
- El «acierto de otra fuente» puede estar definido con una tolerancia que hace trivial el acierto (radio grande).
- La tabla de distancias del OCR puede estar cuantizada (D15) y eso es conocido, no un hallazgo nuevo.

## 303: comparar nuestro radio con el de MIROVA mezcla orígenes (vent vs centro de MIROVA)
(scripts/banco_paridad.py:450, gravedad 2)
- Puede que el banco no compare radios sino un campo ya unificado (`final_hotspot_dist_km`, fallback eruption->vent) y el
  origen sea el mismo en ambos lados: el reparo sería falso.
- Que el origen sea distinto puede ser pequeño frente a la tolerancia (inner_radius 3 a 20 km); la gravedad 2 podría ser 1
  o el efecto, nulo en la clasificación summit/far.
- El caller transforma el argumento antes de la línea 450 (por ejemplo ya resta el desplazamiento vent-centro).
- El volcán donde se mide (¿Puyehue 20 km? ¿Villarrica?) decide si importa; una mediana agrupada puede esconder inversión.

## 304: recall por noche cuenta una pasada distinta en otro lugar (PCC V750 2026-10-10); con misma pasada baja 2 puntos en VIIRS
(scripts/auto_audit_weekly.py:377, gravedad 3)
- «baja 2 puntos» es una diferencia entre dos métricas con denominadores distintos: puede ser ruido (n pequeño) y no
  efecto; sin intervalo, no distingue.
- El caso PCC V750 2026-10-10 es una sola noche: un ejemplo justifica investigar, no priorizar (A94).
- La ventana puede cruzar #535 (2026-08-28 23:00 UTC) y mezclar regímenes (A104), o cruzar el cambio de MODIS a la vía (S172).
- «misma pasada» puede definirse con TOL_S; si la tolerancia de pareo es otra, el número cambia. Vara del pareo.
- El «recall por noche» es el criterio de victoria vinculante (Nicolás, 2026-10-13); cambiarlo a por pasada podría ser
  deseo del auditor y no defecto.
- Línea 377 puede no ser donde se agrega por noche.

## 305: la tabla de MIROVA no lista la mayoría de las pasadas de Suomi NPP; el denominador de negativos se mueve por satélite y mes
(scripts/banco_paridad.py (etiquetar), gravedad 2)
- «la mayoría» depende de qué se cuenta como pasada de Suomi NPP: pasadas orbitales teóricas (TLE) vs pasadas procesadas
  por nosotros. Si se compara contra el catálogo de nuestras pasadas, la tabla puede no estar incompleta sino que MIROVA
  sólo escribe filas cuando hay anomalía (tabla de alertas, no de pasadas): entonces el hallazgo confunde cobertura con diseño.
- Que "el denominador se mueve por satélite y mes" puede ser el resultado esperado de la regla D-9 / de la ventana A119
  (OCR mal calibrado hasta 2026-06-11, VIIRS por pasada desde abril), no un defecto de etiquetar.
- Depende de la copia de la referencia (snapshot vs raíz vs remota viva).
- Ventana: el fenómeno puede estar sólo en meses con cobertura mala (enero, TIF congelados desde 2026-09-22).

## 306: snapshot del consolidado semanal y del OCR horario: entre audits el banco con --snapshot ve alertas OCR sin RUTINA
(.github/workflows/audit-weekly.yml:55, gravedad 2)
- El workflow citado puede no ser el que fija la antigüedad del snapshot: otro workflow (sync-mirova-csv) puede
  refrescar el snapshot a otra cadencia, y el hallazgo describiría una cadencia que ya no existe.
- "sin RUTINA": depende de qué es RUTINA (etiqueta del scraper) y de si el banco la lee del consolidado o del OCR.
- El flag `--snapshot` puede no estar en uso en producción (sólo laboratorio); entonces gravedad 2 sobra.
- La línea 55 del yml puede ser otra cosa (cron, permisos).
- Las alertas "vistas" en el OCR horario sin RUTINA podrían ser el comportamiento deseado (A11: OCR complemento).

## 307: nueve alertas OCR escritas 1,0 MW con nota de truncado deciden la lista de protegidas (Chillán MODIS 2026-10-30 07:15)
(scripts/clase_mirova.py:65, gravedad 2)
- «nueve»: ¿de cuántas en total, en qué ventana y con qué definición de "nota de truncado"? Un conteo que depende de una
  subcadena en un campo de texto puede dar falso verde/rojo (A92).
- "deciden" no es lo mismo que "están en": hay que ver si la alerta sigue siendo protegida sin esas nueve (con tabla
  presente, o con otra pasada cercana). Si hay otra fila de la tabla de ≥1 MW para esa pasada, no deciden.
- 1,0 MW exacto puede ser un valor verdadero (≥1 MW cuenta, lectura A) y no un truncado; la nota puede ser otra cosa.
- La regla D-9 (VIIRS 375 ≤0,05 MW) no aplica a MODIS: confundir sensores.
- La línea 65 puede no ser el lugar donde se aplica el umbral.

## 309: 42 protegidas diurnas fuera del criterio; las 36 de Chillán tienen protegida nocturna a menos de 12 h
(scripts/auto_audit_weekly.py:296, gravedad 2)
- «diurnas» depende de la hora local/UTC y del criterio de día (cenit solar, no hora fija); en invierno/verano o por
  volcán la clasificación cambia (Chillán a ~-36° de latitud).
- «fuera del criterio» requiere saber cuál criterio de MIROVA/MIR sólo-nocturno se aplica (MIR sólo nocturno); si la
  protegida diurna es por VRP TIR y no MIR, no está fuera.
- La ventana: Chillán está en erupción desde un cierto mes; 36 de 42 son de un solo volcán en un solo episodio (cluster
  temporal, no 36 hechos independientes).
- «a menos de 12 h» es un umbral del auditor, no del código: arbitrario.
- La línea 296 puede ser otra función.

## 311: las tres copias de mirovaEqVrp difieren y el guard de tres vistas sólo compara isValidDetection
(frontend/diario.html:255, gravedad 1)
- «difieren» puede ser sólo en espacios, comentarios o nombre de variable: diferencia textual ≠ diferencia de comportamiento.
- CLAUDE.md dice que `comparacion.html` es PREVIEW sin `mirovaEqVrp` a propósito; podría contarse como diferencia siendo diseño.
- El guard puede comparar más que isValidDetection (otro test en `tests/`), o ese test puede ser el que se refiere.
- Las 3 vistas son index, diario, mosaico; el auditor podría contar otra tripleta.
- La línea 255 de diario.html puede haber cambiado en la copia vs 752d348bc.
- `i3_vistas_y_pages.sh` es bash: puede correr distinto bajo Git Bash vs WSL.

## 312: n_misma_pasada del audit compara máximo contra máximo, no noches con acierto en la misma pasada
(scripts/auto_audit_weekly.py:821, gravedad 1)
- Es posible que "n_misma_pasada" esté definido como diseño (max vs max) y documentado así; el reparo sería semántico.
- La línea 821 puede estar en un bloque distinto del que calcula la variable.
- El script `linea_base_1102.py` recibe un argumento (carpeta temporal `root_1102`) y la línea 123 del encargo corta la ruta
  ("f5\root_1102" partida por un salto de línea): puede no correr tal cual.
- La diferencia numérica entre las dos definiciones podría ser 0 en la ventana medida (sin efecto observable).

## Lo que haré para medir por otro camino (plan, no resultado)
- Releer cada línea citada en el commit 752d348bc (git show) además del worktree, y compararlas.
- Recontar con mi propio script, sin importar el del auditor, al menos: 301 (proporción), 307 (sensibilidad: protegidas con y
  sin las nueve), 309 (criterio diurno por altura solar calculada, no por hora fija), 311 (diff normalizado de las tres copias),
  304 (misma pasada vs noche con TOL_S).
- Control positivo en cada medición; declarar denominador y ventana.

---
SELLO (sha256 del contenido anterior a esta línea de sello): 4924f4fedc37beebe46ebedb924105e77830d8d0a90582ceafe492699f5b5e9c
Hora del servidor: Date: Sat, 07 Nov 2026 08:48:36 GMT
