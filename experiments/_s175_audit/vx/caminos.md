# caminos.md: por dónde podría estar mal cada afirmación (escrito ANTES de abrir ningún archivo citado)

Verificador VX, auditoría S175, base 752d348bc67190e53b610989877e2405d238a1bc.
Hasta este momento sólo listé directorios (experiments/_s175_audit/*, vrp-temporales/s175_audit/*),
leí los insumos chicos (hora_servidor.txt, rate_limit.json, secretos_nombres_fechas.txt), el HEAD del
worktree (d1367c6f0) y el disco. No abrí ningún script, documento ni archivo de memoria citado.

## 302 (F5): «con la distancia de la tabla los aciertos por misma pasada son el mismo foco o cúmulo; una protegida al borde (Chillán V375 2026-10-18 06:48)»

1. El instrumento mide otra cosa: la «distancia de la tabla» de MIROVA puede medirse desde otro punto
   (cumbre del KML vs. nuestro `final_hotspot_*`, regla A3), o estar cuantizada a la celda de grilla
   (D15, A13), de modo que «misma distancia» no implica «mismo foco».
2. El pareo «misma pasada» usa una tolerancia (TOL_S l. 78) que puede juntar pasadas de distintos
   satélites o de distintas órbitas; si TOL_S es grande, «mismo foco» se infla por selección (A109).
3. La ventana no contiene el fenómeno: si la ventana de i2 es corta o sólo cubre un régimen (post K, pre
   vía MODIS), el «todos coinciden» puede ser un cero de instrumento (pregunta 2: ¿hay control positivo
   donde un par NO coincida?).
4. El umbral de «mismo foco» (km) puede ser arbitrario y el caso Chillán «al borde» depende de ese
   umbral: con otro umbral cambia el veredicto. Hay que mirar qué umbral y por qué.
5. La protegida «al borde» puede ser artefacto de la referencia: la fila de MIROVA puede venir del OCR
   (distancia de otra pasada, reference_ocr_imagen_de_otra_pasada) y no de la tabla; o la fila de la
   tabla puede ser de un satélite distinto (NOAA-20 vs. SNPP) y la nuestra de otro.
6. El script del auditor puede depender de descargas (i2_tif.py con carpeta `if_descargas`) que no
   existan o estén congeladas (TIF de MIROVA congelados desde 2026-09-22): el TIF que confirma la
   posición puede ser de otra fecha (md5 repetido).
7. La «protegida» (≥1 MW) depende de qué campo de VRP se lea (tabla vs. OCR) y de la regla D-9; si el
   auditor etiqueta distinto a `etiquetar` l. 317, la vara es otra.
8. La copia local está atrasada: los CSV de referencia que lee el script pueden no ser los del sha256
   declarado en el preámbulo (f833bf..., 577a33...).
9. El script puede no correr desde cero (depende de f5_medir_out.json previo, JSON con rutas absolutas
   de otra máquina/temporal), con lo cual «re-correr» sólo relee un cache.
10. La conclusión «sostiene la conclusión central» puede ir más allá de lo medido: aciertos por misma
    pasada es un subconjunto (sólo pares pareados en tiempo), no «la paridad» entera.

## 108 (F0): «la cola de campo no se mantuvo desde S160: los 10 casos siguen abierto, también C-06, que ya tiene respuesta»

1. La copia local está atrasada: el documento puede haberse actualizado en otra rama (`loop/activo`,
   395af8034) o en PRs posteriores a la base (#952 fuera de main), y en la base sí seguir «abierto».
2. «Último commit b941c8052 (S160)» puede ser el último commit del archivo pero el estado de cada caso
   puede vivir en otro lugar (issues de GitHub, `docs/SINTOMAS.md`, bloque de arranque) y la cola ser
   un índice que no pretende estar al día.
3. «C-06 ya tiene respuesta»: la respuesta puede ser el issue #943 (Suomi NPP dejó de producir); hay
   que verificar que C-06 trate de eso y no de otra cosa, y que el issue siga abierto (está «abierto»
   el 2026-11-04; podría haberse cerrado después).
4. El conteo «10 casos» y «filas C-02 a C-10» no cuadran (C-02 a C-10 son 9): puede faltar C-01 o el
   script contar distinto; ver qué cuenta el clasificador.
5. El clasificador del auditor puede detectar «abierto» por subcadena (A92) y dar falso positivo si el
   formato del estado es otro («abierto, con respuesta en #943»).
6. La gravedad 2 puede estar inflada: una cola de campo desactualizada no cambia ninguna detección;
   su efecto en el dashboard es nulo. Verificar si el proyecto tiene regla que exija mantenerla.

## 111 (F0): «243 abierto: nadie mide la fracción de records MODIS que llegan como NRT; la fecha de decomiso de la colección 6.1 ya pasó»

1. «Nadie mide» puede ser falso por otro camino: `auto_audit_weekly.py`, `nrt-healthcheck.yml`,
   `store.py` (auto-upgrade NRT→Standard) o el dashboard pueden exponer el campo o un conteo bajo otro
   nombre (`collection`, `is_nrt`, `source`, `granule_name` con `_NRT`), y el grep por
   `product_version` sería un guard por subcadena mal elegido (A89: «no aparece» casi nunca es que no
   esté).
2. `fetch.py:212-218` puede no ser el único lugar donde se eligen colecciones: la vía
   `mirova_v750_codigo.py` o `scan_geometry.py` pueden pedir MxD03 con otra versión; y el rango de
   líneas puede haber drifteado respecto de la base.
3. «La fecha de decomiso de la colección 6.1 ya pasó»: es una afirmación externa (NASA LAADS/LANCE). Hay
   que verificar en qué fuente se apoya; si la 6.1 sigue sirviendo datos en la base (records recientes
   con 6.1), el «decomiso» no ocurrió o no afecta a lo que usamos. Riesgo de cita de memoria.
4. El script `f0_proporcion_nrt_modis.py` puede medir la proporción NRT sobre un campo que no distingue
   (si `product_version` no se persiste, el script sólo puede medir cero o nada: pregunta 2).
5. La ventana del script puede estar antes del cambio de vía (2026-11-02) o mezclar regímenes (A104).
6. «243 abierto» es un ID de otro frente (o del backlog); verificar que exista y qué dice; no heredar.
7. Gravedad: si el auto-upgrade NRT→Standard funciona, la fracción NRT es transitoria y su efecto en
   detección es menor (LANCE NRT difiere de Standard en geolocalización y calibración); medir si hay
   records que quedaron NRT para siempre.

## 256 (F3): «la memoria del agente dice que el MxD03 se baja y se ignora; la vía de producción lo usa desde 2026-11-02»

1. La memoria puede decir «se ignora» en un contexto acotado (la interpolación `_interp_geo` del camino
   K), no en absoluto; el título del hallazgo puede exagerar. Hay que leer la frase y su alcance.
2. «La vía lo usa» (`mirova_v750_codigo.py:842`): puede usarlo sólo bajo un flag o sólo cuando existe,
   y caer a `_interp_geo` si no (`sin_mxd03` como fuente de caída a K según A100). Entonces «lo usa» es
   condicional y la memoria sigue siendo cierta para los records que caen a K.
3. La línea 842 puede haber drifteado entre la base y el worktree; verificar en 752d348bc con `git show`.
4. «Desde 2026-11-02»: la fecha puede ser la del merge del PR B (#934) o la del primer record con
   `via_codigo_mirova: true`; en los datos puede ser otra (regla S155: anclar a los datos).
5. El archivo de memoria citado puede ya tener una marca de rebaja (⚠️ S172) que el grep por «se ignora»
   no ve: el hallazgo sería «memoria sin marca» y en realidad hay marca en otra línea o en MEMORY.md.
6. Gravedad 2 para un documento de memoria: no toca detección; sólo induce a error al agente. Verificar
   si hay guard/test que vigile la memoria (no debería: la memoria está fuera del repo).
7. La memoria está fuera del repo (`~/.claude/projects/.../memory/`): la «base 752d348bc» no la
   contiene, así que el hallazgo no es verificable contra un commit; sólo contra el archivo de hoy.

## Reglas que me doy
- No abro INFORME.md ni hallazgos.csv de ningún frente (columnas de razonamiento).
- Scripts del auditor: los leo y los re-corro con `python -I` desde una copia o con cwd fuera de su
  carpeta, salida a mi temporal, y comparo contra sus `*.out.txt`/`*_salida.txt`.
- Control positivo por medición y denominador + ventana en cada número.
- Máximo 5 llamadas a la API de GitHub; 0,5 GB de temporal; un proceso pesado a la vez.

---
sha256 (antes de esta línea): f729df02b3656b21d4dcfddd1c836b719116b32ae99fb14a1dbd7c0a5e4acbb1
Hora del servidor (gh api -i, header Date): Date: Sun, 08 Nov 2026 04:04:38 GMT
