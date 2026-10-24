# Verificador con contexto limpio del pre-registro V750-B (S162)

**Hora del servidor** (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera Date): Sat, 24 Oct 2026 16:16:36 GMT.
**Commit del worktree** (`git rev-parse HEAD`): `970a6aa0171e62419a8bd4bda7cd7b692380a37d`, rama `claude/s162-viirs750-f63ef4`, arbol limpio al inicio; `origin/main` = `80b819828f16e19ceacbd21dc7c4e474d46122b4`; tag `s161-d25-lectura` = `a7418e01de7fc182b86c2f70d925292343fd0be6`.
**Modelo y esfuerzo**: Claude Fable 5.1, esfuerzo medio, sin acceso al razonamiento del autor del pre-registro.
**Worktree** (solo lectura salvo esta carpeta): `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4`.
**Carpeta propia** (scripts y salidas de este informe): `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4\experiments\_s162_v750b\verificador\`.
**Arbol temporal para correr** (origin/main + `_s162_v750b` + `evaluar_d25.py` del tag; `git archive` con rutas): `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs750-f63ef4\b455f415-8036-418a-afd4-61523e9603ae\scratchpad\arbol\`. Insumos de V750-C extraidos de `origin/s159-pruebas` (`812624cc6baf97872e8c9fc09558e809123d92dd`) a `...\scratchpad\insumos\`. Grillas de N leidas en su lugar en `D:\vrp-trabajo\temporales\s159_n\` (D: con 9,7 GB libres; C: con 43 GB).

**Que NO mire**: no despache ni mire ningun run de GitHub Actions; no corri el brazo nativo (N0/N1) ni el brazo K sobre un granulo real (no hay red ni granulos en esta sesion); no corri el control «B0 y B1 = censo S159» (los artefactos del censo viven en `resultados_crudos.tar.gz` de `origin/s159-oraculo-censo` y en `C:\vrp-trabajo\s159-m\`, fuera del alcance); no re-verifique la regla GEO de la grilla (esquina `X0 - 25.000 m`, `02_seleccion.py:48`) contra los TIF; no verifique que `data/mirova_equivalent` de hoy este escrito con K en toda la ventana (de eso depende el control «K = produccion»).

## 0. sha256 de lo verificado (tomados a las 16:16 UTC, antes de leer nada)

| archivo (en `experiments/_s162_v750b/`) | sha256 |
|---|---|
| PREREGISTRO_V750B.md | bc3f47cec6d7dd5cac9deb40ab11f52227395915d23facf02b0ed95e77242474 |
| analizar_v750b.py | d8097fc15a0575dcc3ef610740b2e98e747f34a5557b1030accfa476ccd86a74 |
| ensayo_analizador.py | 1f3e531cf1b70872c5f60a8d30526de83b028d31877e04fa91de706b4791ebc0 |
| objetivos_v750b.py | d99a290fa17d9a30a4dc1b532069c8bb60d3bbbe27e7d927711d9982454a1d0b |
| probe_v750b.py | d574a8a4a1f5bf11165c4c3149ff367447bbce7cabe3c2534d626c3df5e4f448 |
| prueba_local_510.py | 07f8c4f6fa87f189600f7e57b64cc8e4395e456cbc809a3fe94d2648d882cdc7 |
| probe-s162-v750b.yml | 670ce8de71742dff27b24c98d82116a41887b129ebba43c64a3af09ef4741b34 |
| ensayo_analizador_salida.txt | 61019d673d7e876626aefa76d7ccf3e74cb2afb1db571d03abc49c142100debc |
| prueba_local_510_salida.txt | 395ae77ec895c0070c86882213c82775423960975b5c54cae28e69850e8146de |
| evaluar_d25.py en el tag `s161-d25-lectura` (`git show s161-d25-lectura:experiments/_s157_prereg_d25/evaluar_d25.py`) | 2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747 (el de `origin/main` es otro: `04cc8f1b...`; el pre-registro hace bien en fijar el tag) |

Scripts propios (en `verificador/`): `mutaciones_regla_s6.py` 3911d5279188c9ac03300b65d918883310026f1be2a68f4a664ecdf3aa1cd52d, `ancla_centro_vs_crater_510.py` c3122527115785f774e555ecc333a9b129207a7672d8ae06bea28d7415f230e7, `celda_crater_independiente.py` (copia del scratchpad), con sus `_salida.txt`.

## 1. Caminos por los que esto podria estar mal (escritos ANTES de leer el contenido)

Lista a priori, para no heredar supuestos del autor. Cada camino se cierra en §2 (hallazgo), §3 (SIN DATO) o §4 (limpio).

- C1. Sistema de filas y columnas: la celda del crater en otro orden u origen que la grilla de `probe_n.grillar`. **Limpio** (§4.1).
- C2. La caja del `.m` en pixeles nativos aplicada a celdas de 1 km sin convertir; o caja centrada en el centro de la grilla cuando el crater no es el centro. **VB-10** (nativo) y **VB-07** (ancla).
- C3. Los brazos B0 a B3 no son los de la tabla; un brazo identico a otro por construccion. **Limpio** (§4.2), salvo lo que dice VB-09 sobre que lectura del `.m` falta.
- C4. El brazo nativo no corre sobre la geometria nativa o la celda del pixel de K esta en otro marco. **Limpio** en el marco (§4.5); **VB-10** en la comparabilidad.
- C5. Etiquetas que no coinciden con el programa (OCR en T, regla SN, negativo limpio). **VB-03**.
- C6. La regla §6 puede elegir o descartar por una razon ajena (elegibilidad, desempate, direccion, canal). **VB-01, VB-03, VB-08**.
- C7. Controles que no pueden fallar o que no frenan. **VB-06**.
- C8. Cobertura dispareja entre brazos; pasada faltante contada como «no detecto». **VB-04, VB-05, VB-11**.
- C9. Workflow que escribe, usa usuario y clave vencidos, o no falla sin token. **Limpio** (§4.6) salvo **VB-14**.
- C10. El analizador arrastra el evaluador de D25 o copia la prueba de signos con un detalle cambiado. **Limpio** (§4.3).
- C11. Las salidas `_salida.txt` no se reproducen. **Limpio** (§4.4), con la nota de VB-13 sobre el parrafo a mano.
- C12. Las grillas de N no son las que el probe espera. **Limpio** (§4.4).
- C13. Zona 0 y zona 1 del `.m` no comparten umbrales (faltaria B0e). **Limpio** (§4.2).
- C14. Numeros sin denominador ni ventana, o transcritos a mano. **VB-13** (uno).
- C15. Falta lo que un sello necesita (tag, hashes, abandono, run a medias). **§5**.
- C16 (agregado al leer): el analizador se cae con un record raro. **VB-02**.
- C17 (agregado al leer): el comentario del `.m` y su matriz de ejemplo no describen la misma geometria. **VB-09**.

## 2. Hallazgos (VB-01 en adelante, por gravedad, lo peor primero)

### VB-01. La regla §6.3 elige por «cercania al .m» tambien a un brazo que PIERDE contra B1 con p = 1/256
- ARCHIVO:LINEA: `experiments/_s162_v750b/analizar_v750b.py:346-354` (si `ganan` queda vacio, `cand = [b for b in PREF if b in elegibles]` sin excluir a los que dieron PIERDE); `PREF` en la l. 45; texto en `PREREGISTRO_V750B.md:117-119` («Si ninguno gana contra B1 (empates o BLOQUEA)»: no dice que pasa con PIERDE). SCRIPT:SALIDA: `verificador/mutaciones_regla_s6.py`, escenario E1, en `verificador/mutaciones_regla_s6_salida.txt`.
- QUE PASA: el fenomeno que decide esta ROI es el ruido de cumbre en noches tranquilas (negativos limpios publicados) contra las alertas debiles que se pierden. En E1, B0, B2 y B4 publican 8 negativos limpios mas que B1 en 8 noches distintas (P2 contra B1 = PIERDE, p = 1/256) y ningun brazo pierde protegidas; el codigo imprime `ROI elegida: B4 (ninguno gana contra B1; orden de cercania al .m (§6.3))`. El texto del §6.3 dice que a «igual desempeno» manda la fidelidad; un brazo que pierde con p = 1/256 no es igual desempeno, y el pre-registro no cubre ese caso. El codigo lo resuelve a favor del brazo mas parecido al `.m`, que es exactamente el que publica mas falsas alarmas en ese escenario.
- COMO SE VE EN EL DASHBOARD: si esa ROI pasa a V750-A, el operador veria mas puntos de cumbre en noches sin actividad que con B1, y el pre-registro lo habria sellado como «fidelidad».
- COMO REPRODUCIRLO: `cd <arbol>` y `python experiments/_s162_v750b/verificador/mutaciones_regla_s6.py --arbol <arbol> --dest <tmp>`; leer el bloque `== E1`. Control positivo del instrumento: E0 (un brazo que pierde una protegida sale de los elegibles) y E5 (dos que ganan: elige el de menor E, B3), los dos en la salida.
- CONFIANZA: CONFIRMADO (corrido).
- GRAVEDAD: 4.

### VB-02. Un solo record de K en `None` tumba el analizador entero antes de imprimir ningun control
- ARCHIVO:LINEA: `analizar_v750b.py:124-127` (`slim` hace `rec.get`), llamado en la l. 195 con `r["brazos"]["K"]["record"]`; el record queda `None` cuando `calculate_vrp` devuelve `None` (`pipeline/process_viirs_mod.py:541-542`, ROI vacia) o cuando el store no escribe (`experiments/_s159/n/probe_n.py:202-223`, `guardar_como_store` devuelve `None`); `ok()` en la l. 177-181 lo deja pasar porque solo exige que exista la clave `record`. SCRIPT:SALIDA: `mutaciones_regla_s6.py`, escenario E7: `rc=1`, `AttributeError: 'NoneType' object has no attribute 'get'`.
- QUE PASA: en N fue 0 de 510 (`K con clave record: 510 | record None: 0`, medido en esta sesion sobre los insumos), pero el run tiene unas 6.900 pasadas y basta una. El ensayo del §11 no lo cubre porque usa los records de K de N, que no tienen ninguno.
- COMO SE VE EN EL DASHBOARD: invisible; se ve como un run de 2 h sin lectura hasta que alguien parche el analizador despues del sello.
- COMO REPRODUCIRLO: bloque `== E7` de la bateria.
- CONFIANZA: CONFIRMADO (corrido).
- GRAVEDAD: 3.

### VB-03. En la ventana T una alerta que es «protegida» solo por el OCR veta la elegibilidad, contra el programa (§2: «T, tabla sola, decide») y A119
- ARCHIVO:LINEA: `analizar_v750b.py:343-344` (elegible exige P1 = 0 en T con el canal `todo`), `analizar_v750b.py:261-270` (`etiqueta(o, "todo")` usa `o["protegida"]`), `experiments/_s159/n/01_poblacion.py:111` (`prot = any(alerta_protegida(f) for f in ref)` sobre TODAS las filas pareadas, CONS y OCR), `scripts/clase_mirova.py:65-75` (`alerta_protegida` no mira `source`). El propio `PREREGISTRO_V750B.md:113-114` lo pide asi («P1 = 0 en T y en O, con la tabla sola y con tabla mas OCR»). SCRIPT:SALIDA: escenario E2: una alerta del 2026-05-03 con CONS 0,6 MW y OCR 1,3 MW que B2 no publica deja `elegibles=['B0','B1','B3','B4']`.
- QUE PASA: antes del 2026-06-11 el OCR tenia la geometria mal calibrada y sin distancia medida (A119, `docs/audit_s139/MAPA_BASES_MIROVA_V1.md` §2, no re-verificado aqui); una lectura de VRP del OCR en esa epoca puede inflar una alerta de la tabla de 0,6 a 1,3 MW. El veto de P1 es absoluto («no entra al paquete aunque gane en P2»), asi que una sola fila OCR de T puede sacar del paquete a la ROI que mejor replica a MIROVA. El programa manda que en T decida la tabla sola; el pre-registro y el codigo exigen las dos cosas en T.
- COMO SE VE EN EL DASHBOARD: invisible en el tablero; se ve como una ROI descartada por una fila que MIROVA no publico en su tabla.
- COMO REPRODUCIRLO: bloque `== E2`.
- CONFIANZA: CONFIRMADO (corrido). Que haya filas OCR de 1 MW o mas pegadas a filas CONS menores en T, en la poblacion real: SIN DATO (no conte).
- GRAVEDAD: 3.

### VB-04. Una pasada con error en el brazo K, o con grilla incompleta, sale del denominador como «no observada», sin nombre, y el job sale 0
- ARCHIVO:LINEA: `analizar_v750b.py:177-189`: `ok()` falla por `"error" in k` o por faltar las cajas; la l. 184-186 cuenta esas pasadas en `no_obs` con `partida(r)` («observada» si la cobertura estaba bien, «sin_cobertura» si el probe no grillo); la lista nominal de protegidas (l. 188-189) solo recorre `sin`, que exige `estado` distinto de «ok». En el probe, `probe_v750b.py:155-160` deja `estado = "ok"` aunque K haya fallado (l. 158-159) o la grilla no exista (l. 135-137), y `main` solo cuenta como faltantes los estados distintos de «ok» y «fuera» (l. 234-236, `return 2 if faltan`). SCRIPT:SALIDA: escenario E3: dos protegidas de 2,0 MW, una con K en error y otra con grilla incompleta, dan `no observadas: {'observada': 1, 'sin_cobertura': 1}`, `SIN DATO: 0`, `protegidas SIN DATO: ninguna`.
- QUE PASA: el pre-registro (§4 y §7) promete que toda protegida sin medir se lista como falla de cobertura y que el run «sale 2 si falta una pasada» (§9). Un error de K (por ejemplo `calculate_vrp` que levanta una excepcion por un granulo raro) o una grilla incompleta no cumplen ninguna de las dos: la protegida desaparece del denominador de P1 sin aviso, y el job queda verde (A108: un run verde no prueba cobertura pareja).
- COMO SE VE EN EL DASHBOARD: invisible; se ve como «0 protegidas perdidas» con menos protegidas de las que hay.
- COMO REPRODUCIRLO: bloque `== E3`.
- CONFIANZA: CONFIRMADO (corrido).
- GRAVEDAD: 3.

### VB-05. Una pasada sin granulo en la lista de objetivos mata los 32 trozos antes de bajar nada (`sorted` con `None`)
- ARCHIVO:LINEA: `probe_v750b.py:218-221` (`grupos.setdefault(o["granule"], [])` y `claves = sorted(grupos)`); `probe_n.py:460` de `origin/main` tiene el respaldo `o.get("granule") or f"diurna|..."` que aqui no se copio; `objetivos_v750b.py:102-103` imprime cuantas pasadas quedan sin granulo pero no las filtra. Medido: `python -c "print(sorted({None:1,'a':2}))"` da `TypeError`; en la poblacion de hoy (`experiments/_s159/n/poblacion_completa.json`, 5.819 pasadas) hay 0 sin granulo, y el censo tambien dio 0 (`01_objetivos_salida.txt` de `origin/s159-pruebas`).
- QUE PASA: con la ventana extendida al 2026-11-02 y los dias del rescate del 12-oct, basta una pasada cuyo record de produccion no traiga `granule` para que cada trozo levante `TypeError` en la primera linea util. El run completo falla en verde-rojo sin un solo granulo bajado, y la regla del §9 («sale 2 si falta una pasada») ni se alcanza.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: agregar a `objetivos_v750b.json` una pasada con `"granule": null` y correr `probe_v750b.py --sin-red`... no basta: `--sin-red` sale antes; hay que llegar a `main` con token. Alternativa sin red: `python -c "import json;print(sorted({None:1,'a':2}))"`.
- CONFIANZA: CONFIRMADO por lectura y por la prueba del `sorted`; hoy latente (0 casos).
- GRAVEDAD: 3 (latente).

### VB-06. Tres controles del §7 no frenan nada: el positivo y el negativo se imprimen despues de la compuerta, y «B0 y B1 = censo» pasa como «no pedido»
- ARCHIVO:LINEA: `analizar_v750b.py:254` (`ctrl_ok` solo incluye el nulo del contador, K = produccion y el censo cuando se pidio), `analizar_v750b.py:315-317` (unica salida temprana), `analizar_v750b.py:320` (control negativo) y `analizar_v750b.py:322-324` (control positivo) ya pasada la compuerta; `analizar_v750b.py:237` (`c_censo = "no pedido"`) y la l. 254 lo trata como verde. `PREREGISTRO_V750B.md:131-132` dice que si el positivo falla «el instrumento no ve la ROI» y que el negativo tiene que dar «E identico». SCRIPT:SALIDA: escenario E4 (ningun brazo pierde protegidas de Cordon Caulle): `control positivo = 0` y aun asi `ROI elegida: B4`.
- QUE PASA: el control positivo es el unico que prueba que el instrumento ve la ROI (pregunta 1 del instrumento). Con el control en 0 se imprime veredicto igual. El control contra el censo, que es el que detectaria que el oraculo cambio entre S159 y hoy, se puede omitir sin que la compuerta lo note (A116: un control que no puede fallar no es control). Y el pre-registro no dice de donde salen los artefactos del censo para `--censo-art` (viven en `resultados_crudos.tar.gz` de `origin/s159-oraculo-censo`, no en `origin/main`).
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: bloque `== E4`; y `python analizar_v750b.py ... --solo-controles` sin `--censo-art`, que imprime `EN VERDE` con el censo «no pedido» (asi salio tambien el ensayo del autor y mi re-corrida, `verificador/ensayo_rerun_salida_controles.txt`).
- CONFIANZA: CONFIRMADO (leido y corrido).
- GRAVEDAD: 2.

### VB-07. El predicado «publica» de los brazos del oraculo clasifica summit/far desde el centro de la grilla; produccion lo hace desde el crater del yaml
- ARCHIVO:LINEA: `analizar_v750b.py:115` (`dcen = hypot(fr - C, fc - C) * 0.75`, con `C = 33`) y l. 120 (`"summit" if dcen <= inner`); produccion: `pipeline/process_viirs_mod.py:1238-1239` sobre `final_hotspot_dist_km`, medido desde `get_detection_anchor` (`pipeline/geo_utils.py:53-78`: gana `vent_lat/vent_lon`). `PREREGISTRO_V750B.md:92-94` describe el record sin decir desde que punto mide la distancia. SCRIPT:SALIDA: `verificador/ancla_centro_vs_crater_510.py` sobre las 510 grillas de N (ventana 2026-04-01 a 2026-10-21): 3 cumulos cambian de clase segun el ancla: Planchon-Peteroa 2026-08-15 05:06 (alerta de MIROVA; B0, B1 y B3: summit a 2,25 km del centro, far a 3,75 km del crater, inner 3), Tupungatito 2026-07-31 06:24 (negativo limpio; B1: far a 7,42 km del centro, summit a 6,08 km del crater, inner 7). Control positivo del script: un cumulo construido en (24, 27) de Tupungatito da far desde el centro y summit desde el crater.
- QUE PASA: fisicamente el crater de Tupungatito esta a 4,86 km al NW del centro del TIF y el de Planchon-Peteroa a 2,00 km al S (medido, `verificador/celda_crater_independiente_salida.txt`); un cumulo real en el crater y su halo cae a distancias distintas segun el punto de referencia. Hoy el efecto es chico (3 de 510), pero toca justo a los dos volcanes que motivan el pre-registro y, para el brazo K, el tablero usa el otro ancla: K y los B no se publican con el mismo predicado geometrico. Lo que no decide V750-B (K es informativo) si contamina la comparacion K contra B del §5 y la lectura del §8.
- COMO SE VE EN EL DASHBOARD: en el tablero real la distancia se mide desde el crater; una ROI elegida con el ancla del centro puede publicar algo distinto de lo que el run midio.
- COMO REPRODUCIRLO: `python experiments/_s162_v750b/verificador/ancla_centro_vs_crater_510.py --arbol <arbol> --insumos <insumos> --grillas D:/vrp-trabajo/temporales/s159_n`.
- CONFIANZA: CONFIRMADO (leido y medido); el tamano del efecto en el run completo, SIN DATO.
- GRAVEDAD: 2.

### VB-08. El §6.2 no dice que ventana ni que canal deciden el GANA; el codigo decide con T union O y canal `todo`, y exige ademas que el canal tabla no de PIERDE ni BLOQUEA
- ARCHIVO:LINEA: `analizar_v750b.py:346-349` (`veredicto[(b, "TO", "todo")][1] == "GANA" and veredicto[(b, "TO", "tabla")][1] in ("GANA", "EMPATE", "SIN SUSTRATO")`; el desempate por menor E tambien en `TO`/`todo`); `PREREGISTRO_V750B.md:115-116` solo dice «cada uno contra B1 por P2». SCRIPT:SALIDA: escenario E6: B2 apaga 6 negativos que B1 publica y pierde 6 bajas que solo trae el OCR: con `todo` da EMPATE (neto 0) y con la tabla sola daria GANA; el codigo no lo elige y cae al §6.3 (B4).
- QUE PASA: la regla escrita permite dos lecturas que dan ROI distintas. La del codigo es defendible (O decide con tabla mas OCR, programa §2), pero mezcla T (donde el OCR no decide) con O dentro de un solo `TO`, y la condicion sobre el canal tabla no esta escrita en ninguna parte. Un sello sobre el texto de hoy no fija la regla que de verdad corre.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: bloque `== E6`.
- CONFIANZA: CONFIRMADO (leido y corrido).
- GRAVEDAD: 2.

### VB-09. El comentario del `.m` describe BOX == 1 como la ROI central conservadora y BOX == 2 como la extendida sensible; la matriz de ejemplo es al reves, y ningun brazo prueba la lectura del comentario
- ARCHIVO:LINEA: `experiments/_s159/o1/o2_paquete/MIROVA_VIIRS750_hotspot_detection.m:111-119` de `origin/main` («BOX == 1: central volcanic ROI, generally centred on the summit area... Conservative thresholds»; «BOX == 2: extended volcanic ROI surrounding the central region... tested with more sensitive minimum thresholds») y l. 389-399 (ROI2 con los umbrales sensibles); la matriz de ejemplo, segun `experiments/_s158_audit_r2/granulos/probe_granulos.py:45-47` y `experiments/_s160_espacial/INFORME.md` E-09 (Etna, 21 x 19), tiene BOX == 2 en el 7 x 7 central. `PREREGISTRO_V750B.md:11-12` llama a BOX = 2 «zona de cumbre».
- QUE PASA: el `.m` trae dos descripciones de su propia geometria que no coinciden. Bajo la del comentario, la configuracion literal seria un centro de 7 x 7 CONSERVADOR con una corona de 21 x 21 SENSIBLE, que es justo la que cubriria el lacolito de Cordon Caulle (4,6 a 10,5 km) y el crater de Tupungatito (4,9 km) sin bajar el umbral en la cumbre. Esa lectura no esta entre B0 a B4. Como el §6.3 desempata por «cercania al .m», hay que decir cual de las dos lecturas del `.m` es la vara, o el desempate queda sin referencia.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: `git show origin/main:experiments/_s159/o1/o2_paquete/MIROVA_VIIRS750_hotspot_detection.m | sed -n '105,125p'`.
- CONFIANZA: CONFIRMADO lo del comentario (leido); lo de la matriz de ejemplo lo tomo de dos documentos del repo, no la lei yo: SOSPECHA en eso.
- GRAVEDAD: 2 (decision de diseno antes del sello, no un bug).

### VB-10. N0 y N1: la caja en pixeles nativos no mide los mismos kilometros que la de la grilla fuera del nadir, y la prediccion del §8 lo lee al reves en Tupungatito
- ARCHIVO:LINEA: `probe_v750b.py:81-91` (`ventana_nativa`: 67 x 67 pixeles del barrido) y l. 147-151 (cajas de 7 x 7 y 21 x 21 en pixeles); `PREREGISTRO_V750B.md:57-58` y 145-150. Tamano del pixel: `pipeline/scan_geometry.py:206-210` cita el ATBD de geolocalizacion VIIRS (423-ATBD-002, Tabla 2.2-1): I-band 0,371 x 0,388 km en el nadir y 0,80 x 0,789 km al fin del barrido (factor ~2,1 por eje); M-band proporcional (0,75 km a ~1,6 km, SOSPECHA en el numero exacto, no lo lei del ATBD).
- QUE PASA: a 55° de cenit un pixel M-band mide cerca del doble en el eje del barrido; el 7 x 7 nativo cubre ~11 km de ancho en vez de 5,25, y el 21 x 21 ~33 km en vez de 15,75. El crater de Tupungatito (4,86 km del centro) cae DENTRO del 7 x 7 nativo en las pasadas de borde, asi que N0 puede detectar ahi por tamano de caja, no por «sin remuestreo». El §8 predice «casi ninguna de Tupungatito (zona conservadora)» y leeria una deteccion de N0 como evidencia de que el remuestreo calla la cumbre. Es diagnostico (no decide V750-B), pero es la confirmacion de V750-C que el pre-registro dice heredar.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: no corri el nativo. Mitigacion barata: estratificar N0/N1 por tramo de cenit (ya se guarda `geometria_centro`) y expresar la caja nativa en km con `lat`/`lon` de la ventana guardada.
- CONFIANZA: SOSPECHA (razonado sobre el ATBD citado, no medido).
- GRAVEDAD: 2.

### VB-11. La regla del 12-oct (§3: rescate de LAADS o exclusion en todos los brazos) no esta implementada en ningun script
- ARCHIVO:LINEA: `objetivos_v750b.py:32` (`EXCLUIDOS` trae 10-13 y 10-17 a 10-20, no el 10-12), `probe_v750b.py` (no usa el patron de `probe_rescate.py`), `analizar_v750b.py` (no excluye el 10-12 cuando una pasada falta). `PREREGISTRO_V750B.md:77-79`. El ensayo del autor y mi re-corrida ya muestran `NevadosDeChillan 2026-10-12 05:18` como protegida SIN DATO (aparece dos veces porque `objetivos_n.json` y `objetivos_censo.json` la traen las dos; eso es solo del ensayo).
- QUE PASA: una protegida del 12-oct que no baje queda SIN DATO en todos los brazos (bien) pero la del mismo dia que si baje cuenta, contra lo que el §3 promete («se excluye en todos los brazos»). Como el 12-oct es el dia del cese de CMR que motivo el rescate, es el dia con mas probabilidad de cobertura dispareja.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: `grep -n EXCLUIDOS experiments/_s162_v750b/objetivos_v750b.py`; `grep -c rescate experiments/_s162_v750b/probe_v750b.py` da 0.
- CONFIANZA: CONFIRMADO (leido).
- GRAVEDAD: 2.

### VB-12. «K = produccion» es binario: una sola pasada distinta detiene toda la lectura, y depende de que `data/` este en K en toda la ventana
- ARCHIVO:LINEA: `analizar_v750b.py:234-236` y 254 (`not dpub and not dvrp`); `PREREGISTRO_V750B.md:129` («se detiene la lectura»). En el ensayo: 0 de 508 distintos (bien).
- QUE PASA: el control compara el K re-corrido en el runner contra `pub_prod` y `pc_vrp` leidos de `data/mirova_equivalent` al generar los objetivos. Una pasada que produccion escribio como NRT y el runner baja como Standard (A: `product_version`, delta BT < 0,1 K pero `pc.vrp_mw` a 0,001 MW no esta garantizado), o cualquier pasada de T que no se haya reprocesado con K, hace fallar el control y con el toda la lectura de un run de 2 h. No hay tolerancia declarada ni la opcion de dejar esas pasadas como SIN DATO.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: no reproducido (haria falta un granulo real). Verificacion previa barata: contar en `data/mirova_equivalent/*.json` los records VIIRS 750 de la ventana con `product_version == "nrt"` y la marca de regimen de K.
- CONFIANZA: SOSPECHA (riesgo de diseno, no fallo observado).
- GRAVEDAD: 2.

### VB-13. Citas que no apuntan a donde esta la cosa, y un numero sin script
- ARCHIVO:LINEA: `PREREGISTRO_V750B.md:17, 31, 78, 81` citan `experiments/_s159/oraculo_censo/` (INFORME C-1, `probe_rescate.py`, `01_objetivos.py`): esa carpeta no existe en `origin/main` ni en `HEAD` (`git cat-file -e` falla); vive en `origin/s159-pruebas` (`812624cc6`) y `origin/s159-oraculo-censo`. `PREREGISTRO_V750B.md:81` dice que la lista de objetivos sale de `01_objetivos.py` del censo; `objetivos_v750b.py:81-85` usa `experiments/_s159/n/01_poblacion.py` (equivalente en poblacion, pero no es lo que dice el texto). `probe_v750b.py:11` y `PREREGISTRO_V750B.md:172` dicen que el probe reusa `probe_censo.py`; solo importa `probe_n` (l. 36). `PREREGISTRO_V750B.md:66` y `probe_v750b.py:59-61`: «medido: 0 de 510 grillas» para B0e sin ningun script en el repo que lo mida (la version que lo midio se borro; la salida lo cuenta en un parrafo escrito a mano al final de `prueba_local_510_salida.txt`, por eso su sha256 no es el de la salida del script: la mia es `f4751401...`). Lo re-medi: `ancla_centro_vs_crater_510.py` da **B0e distinto de B0: 0 de 510**, asi que el numero es cierto, pero ahora tiene script.
- QUE PASA: quien selle o audite con `origin/main` no encuentra el censo ni el patron de rescate; y un numero que no sale de un script viola la regla S91.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: `git cat-file -e origin/main:experiments/_s159/oraculo_censo || echo NO`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VB-14. El workflow sube el artefacto aunque la carpeta `out/` este vacia, y sin `retention-days`
- ARCHIVO:LINEA: `experiments/_s162_v750b/probe-s162-v750b.yml:62-70` (sin `if-no-files-found: error` ni `retention-days`); el del censo, `origin/s159-pruebas:experiments/_s159/oraculo_censo/probe-s159-oraculo-censo.yml`, lleva los dos.
- QUE PASA: un trozo que muera antes de escribir `resultados_NN.json` (por ejemplo por VB-05) sube un artefacto vacio con aviso, no con error; el analizador despues lo lee como «sin resultado» para todas sus pasadas. Con `if: always()` el paso de subida enmascara la causa.
- COMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO (leido).
- GRAVEDAD: 1.

### VB-15. El programa §2 declara el placebo K x 1,2 «obligatorio» y el pre-registro no lo trae ni explica por que no aplica
- ARCHIVO:LINEA: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md:63`; `PREREGISTRO_V750B.md` §5 y §7 (ausente).
- QUE PASA: el placebo es del comparador de magnitud M (D-44); V750-B no mide M (solo razones descriptivas), asi que probablemente no aplica, pero el sello deberia decirlo para que la coordinadora no lo exija despues.
- CONFIANZA: CONFIRMADO lo ausente; que no aplique es mi lectura.
- GRAVEDAD: 1.

### VB-16. «Cumbre sin dato» se mide en el 7 x 7 del CENTRO de la grilla, no en la celda del crater
- ARCHIVO:LINEA: `analizar_v750b.py:139-142` (`nan_7`, `nan_centro`), `probe_v750b.py:94-97`.
- QUE PASA: para Cordon Caulle (crater en la celda (23, 30)) y Tupungatito ((27, 30)) el estado «no observada» mira una cumbre que no es la del volcan; una pasada con el crater en NaN y el centro limpio cuenta como observada (conservador para P1), y la inversa sale del denominador. Impacto esperado chico; falta decirlo en §4.
- CONFIANZA: CONFIRMADO (leido).
- GRAVEDAD: 1.

## 3. SIN DATO (lo que no pude medir, dicho como tal)

- Control «B0 y B1 = censo S159» del §7: no corrido (artefactos fuera de `origin/main`, ver VB-06 y VB-13).
- Brazo K y brazos nativos N0/N1 sobre granulos reales: no corridos (sin red). El marco de coordenadas de `en_pixel_k` si esta verificado (§4.5).
- Tamano del efecto de VB-07 y de VB-03 en la poblacion completa de ~6.900: no contado.
- Que `data/mirova_equivalent` este escrito con K en toda la ventana T union O (premisa de «K = produccion»): no verificado.
- Las cifras del §9 (unas 6.900 pasadas, ~600 en S_C, 2 h): el propio pre-registro las marca SOSPECHA; `objetivos_v750b.py` no se puede correr aqui sin `--data` y `--ref-dest` frescos.
- La regla GEO de la grilla (esquina `X0 - 25.000 m`, paso 750): tomada de `02_seleccion.py:48` sin cotejar contra un TIF.

## 4. VERIFICADO LIMPIO (que no hay que volver a mirar, y con que comando)

4.1 **Celda del crater en el mismo sistema que la grilla.** `probe_n.grillar` (`origin/main:experiments/_s159/n/probe_n.py:76-78`) pone `ys = ul_y - 750 * (i + 0,5)` (fila 0 al norte) y `xs = ul_x + 750 * (i + 0,5)`; `objetivos_v750b.celda_crater` (l. 46-51) usa `(ul_y - y) // 750` y `(x - ul_x) // 750` en el mismo EPSG de la grilla. Recalculado por mi cuenta con pyproj y la celda mas cercana a los centros de celda: PCC (23, 30), Tupungatito (27, 30), Planchon-Peteroa (35, 33), Lascar (32, 33), Villarrica (33, 32), Chillan (33, 33), identicos a los del autor; el centro del TIF cae en (33, 33) en los seis. Distancias vent a centro: PCC 7,63 km (dN +7,30, dE -2,17), Tupungatito 4,86 km (dN +4,03, dE -2,70: NW), Planchon-Peteroa 2,00 km, que son los 7,6 / 4,9 / 2,0 del §1. Comando: `python experiments/_s162_v750b/verificador/celda_crater_independiente.py <arbol>`.

4.2 **Los brazos son los de la tabla, y B0e sobra.** `probe_v750b.cajas` (l. 44-62): B0 = `caja_mirova()` (7 x 7 = 2 dentro de 21 x 21 = 1, simetrizado, `probe_granulos.py:44-54`); B1 = B0 con 1 -> 2; B2 = B0 con el 7 x 7 movido a la celda del crater (y el anillo 21 x 21 de 1 en el centro); B3 = circulo `dk <= inner_km` en 2 sobre el 21 x 21 (para PCC, inner 20, cubre la grilla entera salvo el borde: la tabla del §2 dice «el resto del 21 x 21», que ahi no existe, cosmetico). B4 se arma en el analizador (`caja_de`, l. 130-133) con B1 en PCC y Tupungatito. En el `.m` (l. 303-304 y 373-374) la media y el sigma del contraste son de TODA la escena, y zona 0 y zona 1 usan el mismo umbral (l. 389-395; port `mirova_v750_r2.py:113-115`): el tamano del anillo no puede cambiar una mascara. Medido: B0e (21 x 19) distinto de B0 en **0 de 510** grillas. B2 y B3 actuan donde deben: mascaras distintas de B0 en PCC (27 y 30 de 510), Tupungatito (10 y 11), Planchon-Peteroa (1 con B2). Comando: `python experiments/_s162_v750b/prueba_local_510.py --insumos <insumos> --grillas D:/vrp-trabajo/temporales/s159_n` (1 min 39 s) y `ancla_centro_vs_crater_510.py`.

4.3 **La prueba de signos es la de D-45 sin copiar a mano.** `analizar_v750b.cargar_signos` (l. 55-80) extrae con `ast` las definiciones literales de `prueba_signos_p2`, `regla_signos_p2` y sus constantes de `evaluar_d25.py` del tag (`s161-d25-lectura:experiments/_s157_prereg_d25/evaluar_d25.py:83, 146-150, 509-566`, leidas) y comprueba `SEMILLA_P2_SIGNOS == 162`, `MAX_B_EXACTO_P2 == 20`, `TOPE_P2_DEN == 20`. La direccion es correcta: `c = e(brazo) - e(B1)` (l. 305-306), neto negativo = menos errores = GANA (`regla_signos_p2`, l. 560-561). Los bloques son (noche UTC, volcan) con alguna discordante, incluidas las de suma 0 (l. 307-309), como pide D-45 §2.3. Verificado en la bateria: E1 da `PIERDE (neto 8, bloques 8, p pierde [1, 256])`, E5 da GANA con 6 bloques, B3 = B1 da SIN SUSTRATO con 0 bloques.

4.4 **Las salidas del autor se reproducen.** `prueba_local_510_salida.txt`: mismos numeros (celdas, 510/510 en B0 y B1 contra N, mismo conteo de mascaras) salvo el parrafo final a mano (VB-13). `ensayo_analizador_salida.txt`: identica (517 objetivos, 509 resultados, 508 ok, 1 sin_crater, 8 SIN DATO, 1.584 perturbaciones con 0 que no cambian, K = produccion 0 y 0). Las grillas de N estan donde el pre-registro dice (`run_39682867040` 391 npz, `run_39693661527` 119, `run_39680724047` 8). Comandos: los del docstring de cada script, corridos en el arbol temporal; salida de mi re-corrida en `verificador/ensayo_rerun_salida_controles.txt`.

4.5 **El marco de `pc_pix` y el de la ventana nativa coinciden.** `calculate_vrp` no recorta el granulo: `roi_mask_bbox` devuelve una mascara del tamano del arreglo (`process_viirs_mod.py:538`) y los indices salen de `np.unravel_index(..., roi_bt_full.shape)` (l. 633); `PG.leer_geo` lee `latitude[:]` entero (`probe_granulos.py:117-118`), y `probe_v750b.ventana_nativa` resta la esquina `i0 - 33` en ese mismo marco (l. 86-91). En los 357 records de N con `pc_pix`, las filas llegan a 3.140 y las columnas a 3.134, consistente con un granulo M-band de 3.232 x 3.200 (y no con un recorte). No hay `concatenate`/`vstack` en `process_viirs_mod.py` ni en `fetch.py`.

4.6 **El workflow es de solo lectura y autentica solo por token.** `probe-s162-v750b.yml`: `"on":` entre comillas (l. 11), `push` a `s162-v750b-disparo` (l. 12-13), `permissions: contents: read` (l. 28-29), paso «Token presente» que sale 1 si `EARTHDATA_TOKEN` esta vacio (l. 37-41), sin `EARTHDATA_USERNAME/PASSWORD`, sin `git push`/`commit`, `set -o pipefail` antes del `tee` (l. 58-61) y `return 2 if faltan` en el probe (l. 245). Identico en pasos al del censo S159 salvo el timeout (120) y lo de VB-14. `python experiments/_s162_v750b/probe_v750b.py --sin-red` corre en 3 s y pasa las tres pruebas (`PRUEBA SIN RED OK`, `PRUEBA SINTETICA OK`, `prueba_sin_red_v750b: ok`).

4.7 **Etiquetas que si coinciden con el programa.** `neg_limpio` = fila RUTINA de CONS con VRP 0 y noche sin alerta ni FP (`scripts/banco_paridad.py:322-325`); `decide` = negativo, o alerta de la tabla, o noche desde 2026-06-13 (`01_poblacion.py:118`), asi que en T las alertas solo OCR no entran (lo que falla es la marca `protegida`, VB-03); frontera T/O en `analizar_v750b.py:47, 272-274` (cadena `"2026-06-13"`, comparacion de cadenas correcta con `"YYYY-MM-DD HH:MM"`); protegida = lectura A, 1 MW o mas (`clase_mirova.py:46, 65-75`); dias D-29 excluidos (`objetivos_v750b.py:32`) y corte de Suomi NPP (l. 33, 87). El pre-registro cita bien los numeros del censo que usa como control (C-1: 6 protegidas y 33 bajas perdidas con la caja por defecto; C-2: 15 negativos de 5.353 y delta E -90 con la sensible) y los de V750-C (78 de 78 con 21 x 21 y con el circulo; 12 contra 8 negativos), leidos en `origin/s159-pruebas:experiments/_s159/oraculo_censo/INFORME.md:89-116` y `experiments/_s162_v750c/INFORME.md:24, 48, 157-160`.

4.8 **El control nulo del contador y el de K = produccion si pueden fallar.** El nulo perturba records publicados (VRP a 0 y clase a far) y 50 negativos no publicados (los vuelve summit de 0,3 MW) y exige que todos cambien de publicacion (l. 211-233); el predicado es el del tablero ejecutado con node (`banco_paridad.correr_node`, l. 141-153, con `isSummitDetection`, `isValidDetection`, `isThermalArtifact`, `mirovaEqVrpDisplay` de `frontend/index.html:1162-1617`, leidos). En la bateria, un record sintetico con `primary_cluster.vrp_mw = 0` o `distance_class = "far"` deja de publicarse y uno de 0,3 MW summit se publica: 1.584 de 1.584 en el ensayo.

## 5. Que falta en el pre-registro para que Nicolas lo pueda sellar

1. Decidir y escribir en §6 (VB-01, VB-08): que hace un brazo que PIERDE contra B1 (propongo: no se elige por §6.3; solo entran al desempate por cercania los EMPATE, BLOQUEA y SIN SUSTRATO), que ventana y canal deciden el GANA y el desempate por E, y que pasa si el canal tabla y el canal todo se contradicen.
2. Decidir §6.1 contra el programa §2 (VB-03): en T, P1 con la tabla sola; el OCR de T se informa aparte.
3. Decir cual lectura del `.m` es la vara del §6.3 (VB-09), y si se agrega el brazo «centro conservador, corona sensible» o por que no.
4. Escribir desde que punto mide la distancia el record del oraculo y por que (VB-07), y como se compara con K.
5. Arreglos de codigo antes del despacho (no del sello, pero el §11 los promete): `slim(None)` (VB-02); K en error y grilla incompleta como SIN DATO nominal y con salida 2 (VB-04); respaldo para `granule` nulo o filtro con conteo impreso (VB-05); controles positivo, negativo y censo dentro de la compuerta, y ruta declarada de los artefactos del censo (VB-06); regla del 12-oct (VB-11); `if-no-files-found: error` (VB-14).
6. Fijar en el texto: sha256 de `evaluar_d25.py` del tag (2e5576...), sha256 de los cuatro scripts al momento del sello, tag del codigo desde el que se despacha, criterio de abandono (que porcentaje de pasadas SIN DATO invalida el run) y que pasa si el run muere a medias (A108: contar pasadas por brazo antes del veredicto).
7. Una linea sobre el placebo (VB-15) y sobre la cumbre que mide «no observada» (VB-16).

**Veredicto: listo para sello con cambios** (los puntos 1 a 4 son del texto y los decide Nicolas; el 5 es codigo que la sesion del instrumento puede cerrar antes del despacho; el 6 y 7 son una tarde). No esta listo tal como esta: con el texto de hoy, la regla puede elegir una ROI que pierde contra B1 por «cercania al .m», y una fila OCR de T puede vetar la mejor.
