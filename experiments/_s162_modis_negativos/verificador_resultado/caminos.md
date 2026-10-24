# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir ningún archivo citado)

Verificador con contexto limpio del resultado del lote MOD-C (run 40120713181). Recibí sólo título,
script:salida y gravedad de R1 a R4. No he leído el pre-registro, el 07_leer_lote.py, su salida ni
INFORME.md. Commit del worktree: 11570ab307c3adcee5d2b7b8b96afb01450c86a9. Hora del servidor al
empezar: Sat, 24 Oct 2026 18:41:37 GMT.

## R1. INDECIDIBLE: x = 2 de n = 390; ΔE punto −18,1, IC 95 % [−43,8; +40,1]

1. **El instrumento mide otra cosa**: «publica» del port podría no ser el predicado del tablero
   corrido con node sobre `record_port`, sino un proxy en Python (por ejemplo `n_px > 0` o
   `vrp > 0`). Si el proxy es más laxo o más estricto que el tablero, x cambia.
2. **n no cuenta lo que la regla dice**: n = 390 debería ser «pasadas neg_resto evaluables». Caminos:
   (a) se incluyeron pasadas donde producción K sí publica (no son neg_resto); (b) se incluyeron
   pasadas que no son negativos limpios (tienen alguna fila de alerta en la referencia); (c) las
   10 no evaluables se quitaron del denominador cuando la regla las contaba, o al revés; (d) hay
   pasadas duplicadas (misma hora, dos gránulos) que cuentan dos veces; (e) la referencia usada para
   «negativo limpio» no es la congelada por el pre-registro (sha256 distinto).
3. **La regla sellada se aplicó con margen**: el §5 puede definir INDECIDIBLE por el IC cruzando cero
   y por la cota; comprobar que la fórmula de ΔE y del IC es la que el pre-registro fija (por ejemplo
   extrapolación a 5.093 con qué estimador, binomial exacta vs normal, bootstrap con qué semilla) y
   que no hubo cambio entre la versión sellada y la que se corrió (adendas 1 y 2 podrían haber
   cambiado la regla después de ver datos).
4. **El 07 lee el artefacto con el record equivocado**: podría leer `record_port` de un trozo pero
   `record_K` de otro, o parear por índice en vez de por clave (volcán + hora), de modo que la pasada
   del port no es la misma que la de K.
5. **El IC no corresponde a x = 2, n = 390**: un IC de [−43,8; +40,1] sobre un punto −18,1 es muy
   asimétrico; comprobar con una binomial exacta (Clopper-Pearson) que la extrapolación de 2/390 a
   5.093 da esas cotas, y que el signo de ΔE es el que la regla define (port menos K, o K menos port).
6. **La ventana no contiene el fenómeno**: las 400 pasadas podrían venir de un tramo donde MODIS casi
   no publica (por ejemplo invierno con máscara de nube, A104) o sin Láscar, y la tasa no
   representaría el estrato. Comprobar la ventana temporal y la mezcla de volcanes contra la del
   estrato completo (5.093).
7. **Selección no aleatoria o no sellada**: la muestra de 400 podría no ser la del
   `objetivos_neg_resto_modis.json` sellado (semilla distinta, o el JSON cambió después del sello).
8. **El port corre con otro perfil o árbol**: el árbol
   `experiments/_s162_modis_verif_cde/arbol/` es «0e18e1053 más 04_analizar.py de s159-pruebas»; si
   el run usó otro commit del port, lo que leo no es lo que corrió. Comprobar que el run declara su
   commit y que coincide.
9. **Zona horaria / día local**: «pasada» en MODIS se parea a ±120 s; si el 07 parea por fecha local
   en vez de UTC, cuenta pasadas distintas.

## R2. Controles en verde: 413/413 con resultado, 10 no evaluables (8 fuera del gránulo, 2 escena inválida); K re-corrido = publicado 403/403; 13/13 iguales a S159; 11/11 protegidas publican; recorte nativo 403/403

1. **413 = 400 + 13**: comprobar que los 13 controles no están dentro de los 400 y que ninguna de
   las 400 se repite. «Con resultado» podría contar un JSON escrito aunque el contenido sea un error
   serializado (`"error": ...`), o sea 413 con archivo pero menos con resultado válido.
2. **«Volcán fuera del gránulo» y «escena inválida» podrían esconder errores de proceso**: una
   excepción atrapada y re-etiquetada como no evaluable es un error disfrazado. Mirar el motivo
   crudo en el JSON y en el log, no la etiqueta.
3. **K re-corrido = publicado 403/403**: si el «publicado» de K se compara contra el record que el
   mismo run produjo (y no contra `data/mirova_equivalent/<vol>.json` del commit declarado), la
   igualdad es trivial. También puede ser que K re-corrido devuelva «no publica» en 403 y el
   publicado también «no publica» en 403 por construcción (es el estrato neg_resto), así que
   el control no puede fallar salvo en las 13 de control: preguntar si el control tiene poder.
4. **13/13 iguales a S159**: iguales en qué (misma decisión publica/no publica, o mismo VRP con
   tolerancia, o mismo píxel). Si sólo es la decisión binaria, un port que cambió de magnitud
   pasaría. Y si S159 corrió en otro runner, los empates de argsort (A/B con dos pipelines, S152)
   pueden mover resultados.
5. **11/11 protegidas publican**: ¿cuáles son las protegidas? Deberían ser alertas de MIROVA de
   1 MW o más dentro de los 13 controles. Si se tomaron protegidas de S159 que ya se sabía que
   publicaban, el control es un control positivo válido para el instrumento (bueno) pero no prueba
   nada del port (nadie dijo que lo probara).
6. **Recorte nativo 403/403**: comprobar que los .npz existen, que tienen dimensiones no vacías y que
   cubren la posición del volcán; un .npz vacío también «existe».
7. **El conteo del control se hace con el mismo lector que el resultado**: si el lector tiene un
   defecto, el control y el resultado lo comparten y el verde no vale. Medir con mi propio lector.

## R3. Los 7 trozos en rojo se deben sólo a pasadas no evaluables previstas

1. **El rojo del job es un exit code**: podría venir de un `sys.exit(1)` deliberado al final cuando
   hay no evaluables (previsto), o de una excepción no atrapada en una pasada que luego no está en el
   JSON (perdida en silencio, A108). Contar las pasadas por trozo contra el objetivo sellado:
   si falta alguna, el rojo es pérdida, no previsión.
2. **7 trozos de 8 en rojo** con 10 no evaluables: eso da al menos 1,4 por trozo; verificar que la
   distribución de las 10 por trozo coincide con qué trozos quedaron rojos (si un trozo rojo tiene 0
   no evaluables, el rojo es otra cosa).
3. **Logs truncados**: GitHub no flushea stdout al matar (A65). Si un trozo murió por timeout, el
   JSON podría estar parcial y el lector lo contaría igual.
4. **Pérdida de gránulos NASA** (`SEARCH_CMR_TIMEOUT`, A64): una pasada sin gránulo que se
   etiqueta «no evaluable» es pérdida de cobertura, y debería contarse aparte de «volcán fuera del
   gránulo».
5. **Trozo de prueba** (`s162-negmodis-prueba`): podría estar contado o no.

## R4. Las dos publicaciones son un píxel cerca de la cumbre; tasa del port ~0,5 % del orden de la de producción en todos los negativos (0,76 %)

1. **«Cerca de la cumbre»**: comprobar la distancia al cráter (`vent_lat/lon` de volcanoes.yaml) con
   haversine propia, y que el píxel está dentro del `inner_radius_km` del volcán (Láscar 5, Llaima 5).
   «Cerca» sin número no es dato.
2. **«Un píxel»**: comprobar el conteo de píxeles alertados en el record_port; si el tablero publica
   por `primary_cluster.vrp_mw > 0` y el cúmulo tiene 1 píxel, bien; si tiene más, la frase cae.
3. **Comparar 0,5 % con 0,76 % mezcla estratos distintos**: 2/390 es la tasa del port en neg_resto
   (donde K no publica por definición); 0,76 % es la tasa de K en TODOS los negativos limpios. Por
   construcción la tasa de K en neg_resto es 0. La tasa comparable del port sería sobre todos los
   negativos limpios, que incluye las pasadas donde K publica (y donde el port también podría
   publicar o no): no se midió en este lote. «Del orden» es una comparación de dos denominadores
   distintos (A90, A93).
4. **El 0,76 % podría venir de otra ventana o referencia** (todos los sensores, o sólo MODIS, o
   antes/después de #535). Comprobar con la referencia congelada.
5. **Las dos pasadas podrían ser el mismo fenómeno físico que MIROVA sí ve en otra pasada de la misma
   noche** (lo que no las haría «falsas» sino señal real sub-umbral, A54), o podrían ser artefacto
   topográfico A69/A80 en Llaima (nevado). El dato de la posición no distingue; anotar sin decidir.
6. **Hora de la pasada**: «Láscar 2026-05-11 07:55» y «Llaima 2026-07-24 01:05» en UTC; Llaima a las
   01:05 UTC es 21:05 local del 23-jul (noche), Láscar 07:55 UTC es 03:55 local (noche). Comprobar que
   ambas son nocturnas según el record (MIR sólo nocturno).

## Transversales

- La copia local del árbol del port podría no coincidir con lo que el run ejecutó (comprobar
  commit declarado en los JSON/logs).
- `python -I` con rutas: el 07 podría depender de imports del repo (`scripts/banco_paridad.py`) y del
  cwd; si no corre con -I, eso es un resultado.
- Disco: C: y D: deben tener más de 3 GB libres; no medido aún (el `df` no imprimió).
- Control positivo mío: inyectar un record_port sintético con VRP > 0 cerca del cráter y comprobar que
  mi lector lo cuenta como publicación; y un record con VRP = 0 que no lo cuente.

---
sha256 (antes de esta línea): 918468c2f4bb39df1c79b89eb03786e7204727b9a099d0e5a9e6bb1666791f95
Hora del servidor (header Date de api.github.com): Sat, 24 Oct 2026 18:43:11 GMT
