# Segundo verificador con contexto limpio: sonda S150 de los tres campos

**Objeto.** Commit `5eda5b942` (rama `s150-sonda-tres-campos`, PR draft #776): las correcciones que se aplicaron
sobre el informe del primer verificador (`docs/audit_s150/VERIFICADOR_SONDA_TRES_CAMPOS.md`, escrito sobre
`4ded935a7`). Material leído: `experiments/_s150_sonda_tres_campos/` (DISENO.md entero, §5, §5 bis, §6, §7, §9,
§10 bis; evaluar.py, campos.py, sonda.py, sellar.py, prueba_local.py) y `.github/workflows/probe-s150-tres-campos.yml`.

**Límites que respeté.** No hice checkout, switch, stash, pull, commit ni push en el árbol del repo (sigue en `main`).
Leí con `git show 5eda5b942:<ruta>` y extraje con `git archive 5eda5b942 <rutas>` a
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\ec53cbb6-245a-4ae2-837c-847d5aeff298\scratchpad\verif2\`.
Ahí hice un `git init` propio para probar el sello (repo temporal, nada sale de esa carpeta). Copié al temporal un
solo GeoTIFF que ya estaba en disco (Chaitén 2026-05-19 05:06, 146 kB) para que P4 corriera. Hice un `git fetch`
(sólo refs remotas) para comparar con `origin/main`. Sin workflows, sin sello real, sin NASA, sin credenciales.
Los scripts de ataque quedan en el temporal: `ataques.py`, `ataques2.py`, `ataques3.py` y `ataques_salida.txt`.

## Veredicto

**Sí al piloto, con cuatro cambios chicos antes de sellar.** Las correcciones cierran de verdad los cuatro hallazgos
de gravedad 3 o más del primer informe: lo comprobé con casos que el código viejo (`4ded935a7`) dejaba pasar y el
nuevo no. Pero encontré dos caminos nuevos por los que sale un veredicto que no es el diseñado (un **REFUTA** con un
campo M que no ve nada, y un **CONFIRMA** cuando el nativo no reproduce los grupos negativos), y que el piloto, tal
como está, no mide la falla de instrumento que más probablemente gaste el despacho completo (la σ contra el A/B).
Todo se arregla en `evaluar.py`, el yml y una prueba más en `prueba_local.py`. Ninguno exige tocar `pipeline/`.

Cambios mínimos antes de sellar (detalle en cada hallazgo):
1. `evaluar.py`: REFUTA exige que M publique las conservadas como el nativo (hallazgo V2-1).
2. `evaluar.py`: gate de reproducción también en los grupos negativos, en `nativo|max` y `nativo|min`, y la brecha
   contrastada con la del A/B (V2-2).
3. `evaluar.py` y el yml: sin números de detección cuando falla un gate, y el yml rechaza `piloto = no` con lotes
   parciales (V2-3).
4. `evaluar.py --piloto`: informar el gate de σ contra el A/B y el «mismo gránulo» (V2-4).

Más una prueba en P7 por cada uno, y volver a correr `prueba_local.py`.

## 1. Hallazgos de gravedad 3 o más del primer informe: ¿cerrados?

Todos VERIFICADO con `ataques.py` / `ataques3.py`, que usan las mismas poblaciones sintéticas de `prueba_local.py`
(meta real de `pasadas.json`, 365 pasadas, predicado real del tablero con node) contra el evaluador viejo
(`git show 5eda5b942^:.../evaluar.py`) y el nuevo.

| hallazgo | caso | evaluador viejo (`4ded935a7`) | evaluador nuevo (`5eda5b942`) | ¿cerrado? |
|---|---|---|---|---|
| 1 (grav. 5) reproducción | clones que publican en todo (el nativo no reproduce nada) | `CONFIRMA (con salvedad: el nativo no reproduce el A/B en ['nativo|max', 'nativo|min']...)` | `INDETERMINADO POR INSTRUMENTO: reproduccion: el nativo no reproduce 32 de 32 perdidas confiables (maximo 2)` | **sí** en lo que pedía; queda un hueco (V2-2) |
| 2 (grav. 3) cobertura | sólo el lote 1 con el diseño que confirma | `CONFIRMA` | `INDETERMINADO POR COBERTURA E INSTRUMENTO: faltan 30 de 32 perdidas confiables...` | **sí** el veredicto; los números siguen saliendo (V2-3) |
| 3 (grav. 3) sello | un comentario agregado a `pipeline/process_viirs.py` | sello viejo: 8 de 8 «COINCIDE», `exit=0` | `raiz:pipeline/process_viirs.py: NO COINCIDE ... exit=1` | **sí** (detalle en §4) |
| 4 (grav. 3) TIF | `r_L = 0,5` en las 135 pasadas con TIF (TIF de otra escena) | `CONFIRMA` | `INDETERMINADO POR INSTRUMENTO: validacion: solo 0 de 135 pasadas con TIF pasan r_L >= 0.90` | **sí** el gate (4 b); 4 a escrita en §9; 4 c sin implementar, se dice; 4 d informa |

El borde del gate de registro también se mueve: con `r_L = 0,85` en todas da INDETERMINADO, con `0,95` pasa y
confirma (`ataques2.py`, T9). Los sub-puntos del hallazgo 1: R_L dentro de la corrida (VERIFICADO: el denominador es
`reproducidas`, el mismo conjunto que el gate, `evaluar.py:350-358` y `:467`), guarda de brecha mínima (P7, VERIFICADO),
control positivo de D22 que frena (P7, VERIFICADO), σ contra el A/B como gate (P7, VERIFICADO). Hallazgos 6 y 7
(grav. 2): implementados (`campos.py:410-423`, `:348-350` y `:428-438`), con prueba en P7 (identidad de escena rota
da INDETERMINADO) y P2b (tope); VERIFICADO por lectura y por la salida de `prueba_local.py`.

## 2. Hallazgos nuevos

### V2-1. Sale REFUTA aunque el campo M no publique nada, ni siquiera lo que MIROVA publicó. Gravedad 4

**El fenómeno.** H1 pregunta si la σ medida sobre el campo donde MIROVA detecta recupera las alertas que `max` pierde.
Las conservadas débiles son alertas que **MIROVA publicó** y que nuestro nativo con `max` también publica. Un campo
M que no las ve no es el campo donde MIROVA detecta: está roto o mal construido (centro, radio, geometría del
predicado, un desfase de registro), y su «no recuperar» no dice nada sobre H1.

**Lo que hace el código.** `evaluar.py:484` decide REFUTA con `rl < 0,25 or dfp > 0,50 · brecha`, sin mirar R_K.
La condición `rk_m >= rk_n - 0,10` sólo está en la rama de CONFIRMA (`:486`). Ningún gate previo comprueba que M
publique algo: la identidad compara la réplica con la corrida real (las dos pueden no publicar nada), y la validación
compara texturas de radiancia, no detección.

**Evidencia (VERIFICADO, `ataques.py` T2).** Nativo que reproduce el A/B, campos `tif_*` que no publican en ningún
grupo ni con ninguna conectiva: `REFUTA (R_L 0.00 sobre 32 perdidas reproducidas; dFP -0.027, brecha 0.330)`, con
`conservadas_M_max 0.0` contra `conservadas_nativo_max 1.0`. Un REFUTA cierra el frente de la σ del campo; por A111,
un cierre falso apaga trabajo futuro.

**Corrección.** Antes de la regla de H1, si `R_K(M, max) < R_K(nativo, max) − 0,10`, el veredicto es
«INDETERMINADO POR INSTRUMENTO: M no publica las alertas de MIROVA que el nativo publica» (la misma cota que ya usa
CONFIRMA, sin número nuevo). Una prueba en P7 con el diseño de T2 que exija ese texto.

### V2-2. El gate de reproducción no mira los grupos negativos, y la brecha no tiene contraste: sale CONFIRMA donde debería salir INDETERMINADO. Gravedad 3

**Lo que hace el código.** El gate por grupo (`evaluar.py:350-371`) mira sólo las pérdidas confiables y las
conservadas. En los tres grupos negativos y en la muestra D22 nadie comprueba que `nativo|max` publique como F y
`nativo|min` como B. Pero la tolerancia de CONFIRMA (`dfp <= 0,25 · brecha`) se calcula con esos mismos grupos en
esta corrida, y la guarda sólo es inferior (`brecha >= 0,10`).

**Evidencia (VERIFICADO, `ataques.py` T3).** Con M que recupera 0,81 y reabre el 40 % del residual apagado:
- nativo sano: `INDETERMINADO (R_L 0.81 sobre 32; dFP 0.141, brecha 0.330 ...)` (correcto);
- el mismo M, pero `nativo|min` publica todo `negativo_b_no_publica` (en el A/B B no publicó ninguno; ese estrato pesa
  1.495 de 2.324): `CONFIRMA (... dFP 0.141, brecha 0.973)`, con los dos gates de reproducción en 0 fallas;
- el mismo M, pero `nativo|max` publica el 30 % del residual apagado (F publicó 0 %): `CONFIRMA (... dFP 0.035,
  brecha 0.224)`.

**Cuán probable.** Baja con el gate de σ en pie: mismo gránulo, mismo código y σ igual a 1e-6 dejan poco espacio para
que cambien decisiones en masa. Pero el residual apagado es tan de borde como las pérdidas (B lo publica, F no), que
es exactamente el argumento con que el primer informe pidió el gate por grupo. Cerrarlo cuesta diez líneas.

**Corrección.** Extender el gate a todos los grupos de `F_PUBLICA` / `B_PUBLICA`, en las dos corridas del nativo, con
el mismo 5 % de las conservadas; y calcular la brecha que el A/B da sobre esta misma muestra (con los pesos de
`totales_ventana` y las tablas `F_PUBLICA` / `B_PUBLICA`, 0,330) e informar la diferencia con la de la corrida. Con
el gate extendido la diferencia queda acotada sola. Pruebas en P7 con T3b y T3c.

### V2-3. Los números de detección se calculan e imprimen aunque el veredicto sea INDETERMINADO, y el yml permite un despacho parcial sin bandera de piloto. Gravedad 3

**Lo que hace el código.** Con un gate caído, sólo el texto del veredicto cambia: `out["h3"]["tabla"]` (`evaluar.py:402-414`),
`out["h1"]["mecanismo"]` (`:416-432`) y todas las tasas de D22 (`:511-538`) se calculan igual y van a
`evaluacion.txt` y a `evaluacion.json`. El primer informe rechazó «CONFIRMA con salvedad» porque se leería igual;
una tabla completa bajo INDETERMINADO se lee igual. Además el candado del yml (`:63-74`) sólo exige lotes cuando
`piloto = si`: nada impide `piloto = no` con `lotes = 1`.

**Evidencia (VERIFICADO, `ataques.py` T4 y T4b).** Lote 1 sin `--piloto`: veredicto
`INDETERMINADO POR COBERTURA E INSTRUMENTO`, pero la tabla trae 15 corridas, por ejemplo
`tif_lin|max` perdidas confiables `(1.0, 2)`, y D22 en el nativo con sus variantes y tasas. Lo mismo con los clones de
P6 (INDETERMINADO POR INSTRUMENTO): tabla de 15 corridas y mecanismo presentes.

**Corrección.** (a) En el yml: si `piloto = no`, `lotes` debe venir vacío (error si no). (b) En `evaluar.py`: si
falla un gate de cobertura o de instrumento, no escribir `h3`, `h1.mecanismo` ni las tasas de D22 en la salida; sí
los diagnósticos de los gates (cuáles fallan y en qué claves). Una prueba en P7.

### V2-4. El piloto no mide el gate que más probablemente gaste el despacho: σ contra el A/B y el mismo gránulo. Gravedad 3

**El fenómeno.** El riesgo nombrado en §9 («NASA pudo reprocesar desde septiembre») hace que el L1B que baje la sonda
no sea el del A/B. Si pasa, la σ del nativo no coincide en casi ninguna pasada, el gate de §5.3 cae y las 365 pasadas
(unos 35 lotes de hasta 330 minutos) terminan en INDETERMINADO POR INSTRUMENTO.

**Lo que hace el código.** En `--piloto` el evaluador vuelve en `evaluar.py:288-301`, antes de calcular
`sd_dnti_nativo_vs_record_ab` (`:320-337`) y `mismo_granulo_que_ab` (`:345`). Ninguno de los dos es dato de detección
(son el pozo de fondo y el nombre del archivo).

**Evidencia (VERIFICADO, `ataques.py` T8).** El piloto informa sólo `cobertura_lotes_presentes`, `identidad`,
`operativo`, `validacion_falla` y `validacion_tif`.

**Corrección.** Mover esos dos bloques antes del `if piloto` y escribir en §10 bis que, si el piloto da σ distinta o
gránulo distinto en más del 5 % de sus pasadas, no se despacha el resto.

### V2-5. Pasadas duplicadas cuentan dos veces y pueden fabricar CONFIRMA. Gravedad 2

`_cargar` no deduplica por clave y `usables` las cuenta tantas veces como aparezcan (`evaluar.py:141-152`, `:286`); la
cobertura usa conjuntos y no se entera. VERIFICADO (`ataques.py` T5): zona gris `INDETERMINADO (R_L 0.44 sobre 32)`
pasa a `CONFIRMA (R_L 0.70 sobre 60 perdidas reproducidas)` al repetir las pérdidas recuperadas, sin falla de
cobertura. En el runner no pasa (un archivo por pasada, artefactos de un solo run); sí pasa si alguien re-evalúa en
local con las salidas del piloto y del despacho en la misma carpeta, que es lo natural porque el lote 1 se corre dos
veces. **Corrección:** si una clave aparece más de una vez, abortar con el nombre de los archivos.

### V2-6. D22 decide con menos pérdidas que las que su gate de cobertura promete. Gravedad 2

El gate propio de D22 cuenta pérdidas D22 **usables** (faltan ≤ 1 de 14, `:201-204`), pero la tasa se calcula sobre las
**reproducidas** (`:497`), y el gate general tolera 2 pérdidas no reproducidas que pueden ser todas D22 (el control
positivo de D22 sólo mira `nativo|min`). VERIFICADO (`ataques.py` T7): `SELECTIVO: recupera 1.00 de 11`. §7 dice
«menos de 7 de las 14». **Corrección:** aplicar `MAX_FALTAN_PERDIDAS_D22` a las reproducidas (≥ 13 de 14).

### V2-7. El piloto sí expone detección, por el log y por los json. Gravedad 2

§10 bis dice que el piloto no imprime ningún veredicto de detección. El evaluador no lo hace, pero `sonda.py:332`
imprime en el log de Actions, para cada campo y pasada, `obj_final max ... min ...`, y cada json por pasada trae
`decision[...]["objetivo_final"]` y los records (VERIFICADO por lectura y en la salida sintética, `ataques2.py` T10).
Con 2 pérdidas en el lote 1 no hay veredicto posible, como dice §10 bis. El riesgo real es otro: §10 bis permite
ajustar «la geometría de la validación» después del piloto, y quien la ajuste habrá visto en el log qué campo `tif_*`
detecta el objetivo de Chaitén. **Corrección:** quitar `obj_final` del `print` de `sonda.py` (queda en el json, que
nadie tiene por qué abrir) y escribir en §10 bis que todo ajuste post piloto se justifica sólo con números de
validación, cobertura, tiempo y memoria, citándolos.

### V2-8. El sello no impide re-sellar con otro criterio. Gravedad 2

VERIFICADO en el repo temporal: con el sello commiteado, bajar `H1_RECALL_CONFIRMA` de 0,50 a 0,30, commitear y volver a
sellar da `SELLO COINCIDE`. Está dicho en el DISENO y la procedencia queda en git, pero el piloto obliga a re-sellar
(cambian yml y DISENO), y en ese re-sello no hay control de qué cambió. **Corrección:** `sellar.py --verificar` imprime
también las entradas cuyo hash cambió respecto del sello anterior en la historia de git
(`git log -p -- SELLO_PREREGISTRO.txt`), y §10 bis lista los únicos archivos que pueden cambiar entre el piloto y el
despacho (el yml y §10 bis del DISENO).

### V2-9. El DISENO dice que el piloto comprueba las dependencias del evaluador; no lo hace. Gravedad 2

§9 (hallazgo 11): «el piloto lo comprueba, porque corre el evaluador». Con `--piloto`, `main()` no importa
`banco_paridad` (`evaluar.py:581-587`) y `predicado()` no corre, así que ni las importaciones ni node se ejercitan.
Medí en local qué módulos externos arrastra `import evaluar, banco_paridad`: sólo `yaml` (y numpy), más los locales
`pipeline`, `auto_audit_weekly`, `referencia_mirova_unificada` (VERIFICADO como aproximación; no es un entorno limpio).
Con `numpy pyyaml pandas` debería bastar. Si fallara en el despacho completo, el job de guardado empuja igual las
salidas, así que se pierde la evaluación, no los datos. **Corrección:** corregir la frase, o que el piloto corra
`bp.control_identidad_predicado()` (no mira datos de la sonda).

### V2-10. Una σ del A/B en NaN pasa como idéntica. Gravedad 1

`evaluar.py:324`: `not sd_ab` es falso para NaN, `rel` queda NaN y `rel >= 1e-6` es falso, así que cuenta como idéntica.
VERIFICADO (`ataques.py` T6): con NaN en las 365, `frac_identica 1.0` y CONFIRMA. Hoy `pasadas.json` no trae ninguna σ
nula ni NaN (VERIFICADO sobre las 365) y está sellado. **Corrección:** `math.isfinite(sd_ab) and sd_ab > 0`.

### V2-11. Lo que el sello deja fuera, a sabiendas o no. Gravedad 1

VERIFICADO en el repo temporal: cambios en `scripts/auto_audit_weekly.py` y `scripts/referencia_mirova_unificada.py`
(los importa `banco_paridad`), en `prueba_local.py`, un archivo nuevo sin versionar en `pipeline/` o un cambio sólo de
finales de línea dan `SELLO COINCIDE`. Ninguno entra al predicado ni a la detección, y el runner sólo ve archivos
versionados. Las versiones de numpy y scipy tampoco se fijan; las cubre el gate de σ en el nativo, no en los `tif_*`.
No bloquea.

## 3. Los umbrales de §5 bis

- **¿Con motivo escrito?** Sí, los once, cada uno dice si es elección o dato. VERIFICADO por lectura.
- **¿Fijados sin ver datos de la sonda?** VERIFICADO que no hay datos de la sonda: `gh run list --workflow
  probe-s150-tres-campos.yml` da 404 (el yml no está en `main`, así que nunca se pudo despachar) y
  `git ls-remote --heads origin 's150-tres-campos-*'` no devuelve ramas. Los que dicen ser dato lo son: B y F dan la
  misma σ dNTI en las 365 pasadas (0 diferencias, VERIFICADO sobre `pasadas.json`); la brecha del A/B es
  766 / 2.324 = 0,330 y el error estándar de R_L pasa de 0,088 a 0,091 de 32 a 30 (aritmética VERIFICADO).
- **¿Alguno hace imposible CONFIRMA?** No con las tasas del A/B: el diseño sintético con tasas del A/B en el nativo da
  `CONFIRMA (R_L 0.81 ... dFP 0.035, brecha 0.330)` (T0). La tolerancia de CONFIRMA equivale a reabrir como mucho un
  25 % del residual apagado (0,25 · 0,330 · 2.324 / 766).
- **¿Alguno hace trivial REFUTA?** Sí, uno, y no por su número sino por lo que falta al lado: V2-1.
- **Uno que puede gastar el run sin decir nada:** σ igual a 1e-6 en el 95 %. Es correcto como gate, pero si NASA
  reprocesó los gránulos cae entero; por eso V2-4.

## 4. El sello, probado con archivos modificados

Repo temporal (`git init` sobre la extracción de `5eda5b942`), sello hecho con
`sellar.py --aprobo prueba --informe docs/audit_s150/VERIFICADOR_SONDA_TRES_CAMPOS.md` (226 líneas). Cada fila es un
cambio real en disco seguido de `sellar.py --verificar` y la vuelta atrás. VERIFICADO.

| cambio | resultado |
|---|---|
| ninguno | `SELLO COINCIDE exit=0` |
| comentario en `pipeline/process_viirs.py` (sin commitear) | `NO COINCIDE ... exit=1` |
| piso de `UNSUITABLE_DNTI_FLOOR_DEFAULT` de −0,1 a −0,2 en `pipeline/detection_context.py`, commiteado | `NO COINCIDE ... exit=1` |
| comentario en `frontend/index.html` | `NO COINCIDE ... exit=1` |
| `max-parallel` 6 a 7 en el yml | `NO COINCIDE ... exit=1` |
| línea en `pipeline/profiles/_s147_ab_sin_test1_max.yaml` | `NO COINCIDE ... exit=1` |
| archivo nuevo versionado en `pipeline/` | `NUEVO (no estaba en el sello) ... exit=1` |
| `DISENO.md` | `NO COINCIDE ... exit=1` |
| sello sin la línea `# aprobo` | `cabecera sin aprobo ... exit=1` |
| archivo nuevo sin versionar en `pipeline/`; sólo CRLF; `auto_audit_weekly.py`; `referencia_mirova_unificada.py`; `prueba_local.py` | `COINCIDE` (V2-11, esperado) |
| re-sello tras cambiar una cota de `evaluar.py` | `COINCIDE` (V2-8) |
| el mismo comentario en `process_viirs.py` con el `sellar.py` VIEJO | `exit=0`: el viejo no lo veía |

Observación lateral (VERIFICADO): `sellar.py` se niega a sellar si hay `__pycache__/` sin ignorar dentro de
`pipeline/` o de la carpeta de la sonda, y si el propio `SELLO_PREREGISTRO.txt` quedó sin commitear de un sello
anterior. En el repo real `.gitignore` cubre `__pycache__`; sólo conviene saberlo. Además VERIFICADO hoy que entre
`5eda5b942` y `origin/main` (`b880aa3b1`) no cambió nada de lo sellado; `main` recibe a diario commits del
experimental que tocan `data/`, que no está en el sello.

## 5. Las salvedades sin corregir (4c, 5, 8, 9, 10, 11): ¿bloquean el piloto?

Ninguna bloquea el **piloto**, que existe justamente para medir 4c (r_dL bajo con r_L alto), 8 (volumen) y el tiempo y
memoria de 11. 5 quedó medido por campo (`frac_var_dnti_termino_i04`, `L_i05` en la tabla; VERIFICADO por lectura de
`campos.py:320-335` y `:451`). 9 es informativo. 10 (recuperación de otro píxel de la cumbre) no cambia la unidad de
decisión, que es la pasada publicada, igual que la alerta de MIROVA; conviene informarlo, no bloquea. De 11, la parte
de dependencias está mal descrita (V2-9). Lo que sí debería bloquear el **despacho completo** son V2-1 a V2-4.

## 6. `prueba_local.py`

Corrido por mí sobre la extracción, con `VRP_PROFILE=_s147_ab_sin_test1_max`, en 14,7 s:
`RESULTADO: 106 comprobaciones, TODO OK`, `exit 0`. La salida es **idéntica** línea a línea a
`prueba_local_salida.txt` salvo una línea: el aviso `[VRP profile=_s147_ab_sin_test1_max] anomaly_K=5.0 ...`, que en
mi corrida salió por stderr y en el archivo está mezclado con stdout. VERIFICADO (`diff` con finales normalizados).
Para que P4 corriera copié al temporal el TIF que usa (`experiments/_s144_conteo_tif/_dl_tif/da4fe36e8920/...`,
que no está versionado); sin él, P4 se salta en silencio («se omite») y la prueba sigue saliendo en verde con menos
comprobaciones. Conviene que P4 diga cuántas comprobaciones se saltó en el resumen final.

Nota sobre P8: prueba el sello alterando el **texto** del sello, no los archivos; la tabla de §4 lo prueba con los
archivos. P6 y P7 sí muestran cada veredicto saliendo cuando corresponde, pero no tienen los casos de V2-1, V2-2,
V2-3 y V2-5, que son los que agregaría.
