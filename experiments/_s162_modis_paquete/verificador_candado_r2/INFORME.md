# Verificacion con contexto limpio del candado MOD-D, segunda vuelta (adenda 4)

Hora del servidor de GitHub al empezar: Mon, 26 Oct 2026 05:49:54 GMT (al cerrar: Mon, 26 Oct 2026 11:49:10 GMT; la sesion duro 6 h porque las tandas de mutaciones del autor corrieron con la maquina compartida con otra sesion). Material: worktree
`C:\vrp-trabajo\s162-modd`, rama `s162-modd-candado`, HEAD `ff2ced5319e1e40e665e3acda60ca0a4ab041cc5` = `origin/s162-modd-candado`
(medido con `git rev-parse` y `git ls-remote`); el arbol solo tenia sin seguimiento los seis archivos de las tandas de mutaciones
en curso. Modelo: Claude Fable 5.1; esfuerzo: el que fijo quien lanzo la sesion (no lo veo desde adentro). Caminos de ruptura
escritos ANTES de abrir el codigo en `CAMINOS.md` de esta carpeta (hora del servidor 05:52:34 GMT, sha256 al pie). No vi la
primera vuelta mas que como lista de lo que se dijo que estaba mal (su `INFORME.md`), ni el razonamiento del autor.

**Que no mire**: el arnes real con red (`probe_paquete.py` sobre HDF; pyhdf no corre en Windows) ni `recorrer_en_sha.py`; el
punto 5 de la adenda 4 (M con la regla de `fillmissing2`), que vive en otra rama y no esta en este arbol; el contenido del
`.m` de MIROVA; la correccion de la vuelta anterior a VCM-05 (procedimiento, no codigo). Las 31 mutaciones del candado no las
lance yo: lei las salidas de las tres tandas que ya corrian (`mutar_evaluar_paquete_salida_v3_g0/1/2.txt`), y lance aparte
cuatro mutaciones propias y la bateria completa. Discos: al empezar C: 25 GB y D: 9,6 GB libres; al cerrar C: 17 GB y D: 8,5 GB (siempre sobre 3 GB).

Todo lo que afirmo sale de un archivo que lei o de un comando que corri en esta sesion; lo que no, va como SOSPECHA.

## En una pantalla

1. **Los seis VCM estan arreglados en el codigo y ninguna otra regla sellada cambio**: el diff `b423316c2..ff2ced531` del evaluador
   toca solo `evaluable`, `armar_tabla` (K33), `control_cobertura`, `veredicto` (fila 5), `externos_de_entrada` (manifiesto y
   `--commit`) y `main`; P1, P1b, P2, M, Chillan y el orden del §6 quedan intactos; `PREREGISTRO.md` solo agrega la adenda 4
   (39 lineas, 0 borradas).
2. **La regla nueva (b) hace lo aprobado y en la fila correcta**: una protegida que K publica y sale por «volcan fuera del granulo»
   o «escena invalida» lleva a DECIDE NICOLAS, pero NO pisa a NO CANDIDATO (P1 veto, P2 PIERDE) ni a INDECIDIBLE (control rojo,
   SIN SUSTRATO): lo medi con `veredicto()` directo y con escenarios completos con node (`pruebas_extra_r2.py`, 13 de 13). La
   bateria la ejercita por los dos motivos con K publicando (t12 y t33) y con K callado (t22), y las 33 fallan contra el vacio.
3. **La bateria del candado tiene dos huecos nuevos alrededor del arreglo**: no hay prueba con P1 veto Y protegida fuera a la vez
   (una mutacion que evalue la fila 5 antes de la 2 queda VIVA) ni con un negativo o bajo 1 MW fuera del denominador con K
   publicando (la lista de «protegidas» podria ampliarse a toda etiqueta sin que nada falle); y `externos_de_entrada`
   (manifiesto, procedencia con `--commit`) no la toca ninguna prueba: solo el ensayo en seco y mis pruebas extra.
4. **El manifiesto cubre lo que importan el arnes y el evaluador** (39 archivos, todos iguales a los blobs del commit HEAD; un byte
   cambiado en `probe_paquete.py` o en `probe_mxd03_ab.py` se ve; un archivo faltante se ve), lo comprueban los dos jobs y el
   evaluador, y la procedencia exige `--commit`; pero el chequeo del evaluador es contra su PROPIO arbol y su PROPIO manifiesto
   (no contra el del tag) y `--commit` acepta un prefijo de una letra. El tag del candado todavia no existe.
5. **Veredicto: se puede despachar el humo con cambios chicos** (lista en §7; ninguno toca `pipeline/` ni re-sella una regla).
   Mutaciones: las 31 del candado ATRAPADAS por asercion (0 caen, 0 vivas, identidad 33 de 33 en las tres tandas); faltan cuatro
   evidentes (precedencia de la regla (b), etiqueta de la lista, `--commit` ignorado, manifiesto ignorado), que corri sobre copia y
   quedan VIVAS contra la bateria.

## 1. Que corri y que dio

| que | comando (desde `experiments/_s162_modis_paquete/`, `python -I -B`, `VRP_PROFILE=mirova_equivalent`) | resultado | salida |
|---|---|---|---|
| manifiesto | `python -I manifiesto_candado.py --comprobar` | `estado OK, n 39, faltan [], distintos []`, prueba del manifiesto True, rc 0 | en este informe |
| manifiesto contra el commit | `git ls-tree HEAD <ruta>` para las 39 entradas | 39 de 39 iguales al blob del commit (independiente de CRLF) | idem |
| bateria contra el vacio | `probar_evaluar_paquete.py --modulo evaluar_vacio.py` | `pasan 0, fallan 33, caen 0 (de 33)`, 1,3 s | `salida_bateria_vacio_r2.txt` |
| bateria contra el real | `probar_evaluar_paquete.py` | `pasan 33, fallan 0, caen 0 (de 33)`, rc 0 (unos 8 min con la maquina cargada por las tandas) | `salida_bateria_real_r2.txt` |
| ensayo en seco | `ensayo_en_seco.py --ref D:/vrp-trabajo/temporales/s162_mxd03/ref` | rc 0; 7 de 7 exigencias SI; numeros identicos a la salida guardada salvo lo esperado por la adenda 4 (`manifiesto OK` nuevo, `procedencia INDECIDIBLE` en vez de OK) | `salida_ensayo_en_seco_r2.txt` |
| pruebas extra propias | `verificador_candado_r2/pruebas_extra_r2.py` | `pasan 13, fallan 0, caen 0 (de 13)` contra el real; contra el vacio 8 fallan, 3 caen (prueban funciones que el vacio no tiene), 2 pasan (r04 es prueba en negativo; r11 prueba `manifiesto_candado` directo, no el evaluador) | `salida_pruebas_extra_r2_real.txt`, `_vacio.txt` |
| mutaciones propias (4, sobre copia) | `verificador_candado_r2/mutaciones_r2.py` | las 4 quedan **VIVAS contra la bateria del candado** y las 4 caen contra mis pruebas extra (m1 por r01, r02, r08; m2 por r03, r04; m4 por r10; m5 por r13) | `salida_mutaciones_r2.txt` |
| las 31 mutaciones del candado | lei las tres tandas que ya corrian (PID 19288, 9992, 25732, arrancadas 02:48 local) | g0 `11 de 31`, g1 `10 de 31`, g2 `10 de 31` atrapadas por asercion = **31 de 31; caen 0; vivas 0**; identidad `pasan 33 de 33` en las tres; 0 `SUSTITUCION INVALIDA`; terminaron entre las 08:34 y las 08:48 local (casi 6 h, no 1 h) | `../mutar_evaluar_paquete_salida_v3_g0/1/2.txt` |
| diagnostico S-1 y prueba sin red del arnes | `diagnostico_s1.py`; `probar_probe_paquete.py` | `PRUEBA DIAGNOSTICO S-1 OK` (rc 0; el borde ruidoso sube la sigma de 0,00041 a 0,00109 y la cumbre pierde su pixel con la ROI1 intacta); arnes `SIN MUTAR: OK`, `RESULTADO: OK, atrapadas 6 de 6, caen 0, vivas 0` (rc 0) | `salida_diagnostico_s1_r2.txt`, `salida_probar_probe_paquete_r2.txt` |
| demo de `bash -e` con `!` y `&&` | `bash -e -c '! true; grep -q "pasan 0," /dev/null && grep -q "caen 0 " /dev/null'` | rc 1 (el paso falla si la bateria del vacio sale verde, porque la linea del `grep` es la ULTIMA del paso) | en este informe |

## 2. Veredicto por punto

### Punto 1: VCM-01 a VCM-06, si la adenda 4 los arregla y si abrio otro defecto

| hallazgo de la vuelta 1 | que hizo la adenda 4 (archivo:linea) | lo arregla | abrio otro defecto |
|---|---|---|---|
| VCM-01 denominador mas ancho que el §8.5 | `evaluar_paquete.py:133-150`: `MOTIVOS_SELLADOS` = los dos del §8.5; `falla_arnes_*` y `falla_port_*` ya no salen en silencio; `grilla_incompleta` sola no saca; `:513-528` `fallas_del_instrumento` pone cobertura en rojo; `:547-551` fila 5 con `prot_k` | **si** (t20, t21, t12, t33, t22 y mis r02 a r09) | VCR-01 (hueco de precedencia en la bateria), VCR-02 (lista «protegidas» sin vigilancia de etiqueta), VCR-05 (`grilla_incompleta` sola es un caso que no puede ocurrir), VCR-06 (`k_publica` sale del runner) |
| VCM-02 candado sin arnes ni evaluador | `manifiesto_candado.py` (39 archivos), `probe-s162-modd.yml:70-75` y `:136`, `evaluar_paquete.py:597-598`; `--commit` en `:609-612` y `:693` | **si** en lo que promete | VCR-03 (chequeo autorreferente, sin tag), VCR-04 (prefijo), VCR-07 (`externos_de_entrada` fuera de la bateria) |
| VCM-03 siete reglas sin vigilancia | t23 a t30 en `probar_evaluar_paquete.py:338-398`; mutaciones `bloque_por_pasada` a `soporte_mismo_modis` | **si**: las 8 pruebas y las 6 mutaciones estan; 33 de 33 fallan contra el vacio | ninguno visto |
| VCM-04 `npix` sin prueba | t31 `:401-403`; mutacion `s159_sin_npix` | **si** | ninguno (la fragilidad de versiones del runner sigue, como se dijo en la vuelta 1) |
| VCM-05 un run pendiente por grupo | sin cambio de codigo: procedimiento (adenda 4.4) | no aplica | ninguno |
| VCM-06 K33 por el runner | `probe_paquete.py:154-158` escribe `k33_slim`; `evaluar_paquete.py:164-166` lo pasa por el predicado; t32; mutacion `k33_por_el_runner` | **si** | VCR-08 (si el arnes dejara de escribir `k33_slim`, el evaluador cae en silencio al camino viejo; la prueba sin red del arnes solo exige `k_slim`) |

**La regla nueva (b) aprobada por la coordinadora**: esta en `veredicto()` `:547-551`, DESPUES de control rojo (fila 1), P1 veto
(2), P2 PIERDE (3) y SIN SUSTRATO (4), y ANTES de CANDIDATO (6); mira `k_publica` y solo `lab == "protegida"` con motivo en los
dos sellados (`:521-523`). Lo medi en las ocho combinaciones (r01) y en tres escenarios completos (r02, r03, r08). La bateria la
ejercita por los dos motivos con K publicando: t12 (`port_estado=volcan_fuera_del_granulo`, k=3,0, exige DECIDE NICOLAS y
`k_publica == 1`) y t33 (`motivo_vacio=escena_invalida`, k=3,0, exige DECIDE NICOLAS, `motivo == escena_invalida`, P1 SIN
PERDIDA); con K callado t22 exige CANDIDATO. Las tres fallan contra el vacio (`salida_bateria_vacio_r2.txt`). **Una falla del
port deja el control 5 en rojo**: t20 (`port_estado="error: ..."`) y mis r05 (`port_estado ok` con `port` vacio) y r06
(`estado` del arnes `error` y `no_bajado`) dan cobertura INDECIDIBLE y veredicto INDECIDIBLE.

### Punto 2: que la adenda 4 no cambie otra regla sellada

`git diff b423316c2 ff2ced531 -- evaluar_paquete.py` toca `evaluable`, `armar_tabla` (solo la rama K33), `control_cobertura`,
`veredicto` (una condicion mas en la fila 5), `externos_de_entrada` (manifiesto y procedencia) y `main` (`--commit`). No toca
`p1`, `p1b`, `_error`, `contribuciones_p2`, `p2`, `pares_m`, `m`, `chillan`, ni las filas 1 a 4 y 6 del §6. `PREREGISTRO.md`:
`--numstat` da 39 insertadas y 0 borradas, todas en la adenda 4. El ensayo en seco da los mismos numeros que antes en todos los
brazos (P1, P1b, P2, M, Chillan), con las dos unicas diferencias esperadas. **Cumple.** Observaciones menores: el `.m` ya
declara «escena invalida» por su cuenta (oraculo `mirova_v750_r2.py:154-155`), asi que sacar solo los dos motivos sellados es lo
que el §8.5 dice; que una falla del port ponga el control 5 en rojo es consecuencia del «los mismos 1.232 granulos en todos los
brazos» del §8.5, no una regla nueva. La adenda 3.6 queda contradicha por la adenda 4 y la 4 lo dice.

### Punto 3: el manifiesto, el workflow, el evaluador y la procedencia

- **Cubre lo que importan**: la sonda importa `probe_paquete` y `evaluar_paquete` y toma todo modulo cargado bajo `experiments/`
  (`manifiesto_candado.py:42-66`); los imports perezosos bajo `experiments/` son dos (`manifiesto_candado`, `probe_granulos`) y
  estan en `FIJOS`; el resto de los perezosos (`banco_paridad`, `run_pipeline`, `pipeline.*`) vive en `scripts/` y `pipeline/`,
  que el job `probe` exige iguales al main congelado (`yml:128-131`). Los datos leidos con ruta literal por los 39 modulos
  (`grillas.json`, `poblacion.json`, `objetivos_portes.json`, `MANIFIESTO.json` de MOD-B, `volcanoes.yaml`, `frontend/index.html`,
  `data/mirova_equivalent/*.json`) estan en el manifiesto o en ese `git diff`. Lo que queda fuera son informes, salidas y
  verificadores (lista medida con `git ls-tree -r`), ninguno importado.
- **Una alteracion se ve**: en una copia del arbol con los 39 archivos, un byte cambiado en `probe_paquete.py` da INDECIDIBLE con
  ese archivo en `distintos`; `probe_mxd03_ab.py` con una linea mas, idem; `grillas.json` borrado da `faltan`; pasar el arnes
  a LF puro no cambia el hash (r11). Los 39 hashes son los blobs del commit HEAD (`git ls-tree`).
- **Lo comprueban el workflow y el evaluador**: `yml:70-75` (job `prueba`, con `pipefail`), `yml:136` (job `probe`, antes del
  arnes, sin `tee`, con `-e` por defecto) y `evaluar_paquete.py:597-598`; un manifiesto INDECIDIBLE tumba el veredicto por `_rojo`
  (r12) y el evaluador toma de verdad el estado de `comprobar` (r13, con monkeypatch).
- **La procedencia exige el commit**: sin `--commit`, vacio, otro sha, dos commits o cabecera sin commit dan INDECIDIBLE; el sha
  exacto da OK (r10). El `commit` de la cabecera es `GITHUB_SHA` (`probe_cumulo.py:155-166`), que en un push es el commit de la
  rama de disparo. **Pero** es `startswith`: un prefijo de 7 y hasta de 1 letra tambien dan OK (VCR-04).
- **Limite estructural** (VCR-03): el evaluador compara su arbol local con su manifiesto local, no con el del tag; la cabecera no
  lleva el hash del manifiesto. Y el tag no existe (`git ls-remote --tags`: ninguno de MOD-D).

### Punto 4: las 31 mutaciones

**Las del candado**: lei las tres tandas al terminar (`mutar_evaluar_paquete_salida_v3_g0.txt`, `_g1.txt`, `_g2.txt`). Resultado:
**31 de 31 ATRAPADAS por asercion, 0 caen, 0 vivas**, y la copia sin mutar pasa 33 de 33 en cada tanda. Cada una la atrapa al
menos una prueba por aserción (no por excepcion: el mutador separa `falla` de `cae`, `mutar_evaluar_paquete.py:129-136`). Las seis
nuevas de la adenda 4 y quien las caza: `falla_del_port_no_roja` (t20), `grilla_incompleta_sale` (t21),
`protegida_fuera_no_decide` (t12, t33), `protegida_fuera_sin_mirar_k` (t22), `s159_sin_npix` (t31), `k33_por_el_runner` (t32).
Las seis de la vuelta 1: `bloque_por_pasada` (t23), `chillan_p_flojo` (t24), `p1_sin_mirar_k` (t25), `error_bajo1_al_reves` (t26),
`chillan_regla4_sin_bajo` (t27), `soporte_mismo_modis` (t30). Los 31 nombres de los grupos son exactamente las 31 claves de
`MUTACIONES` (medido). Dos notas de instrumento: (a) cada tanda sale con codigo 1 porque corre un subconjunto (`atr ==
len(MUTACIONES)`), asi que el codigo de salida no es veredicto, la tabla si; (b) las tandas tardaron casi 6 h y no «del orden de
una hora», porque la maquina estaba compartida con otra sesion (unos 28 procesos python a la vez).

**Las que faltan y son evidentes** (las corri sobre copia, `mutaciones_r2.py`, mismo criterio S156, contra las 33 pruebas del
candado y contra mis 13 extra; `salida_mutaciones_r2.txt`):

| mutacion (que rompe) | contra la bateria del candado | contra mis pruebas extra |
|---|---|---|
| `m1_prot_antes_que_p1` (regla (b) evaluada antes del veto de P1) | **VIVA** | ATRAPADA por r01, r02, r08 |
| `m2_fuera_toda_etiqueta` (la lista de protegidas toma toda etiqueta) | **VIVA** | ATRAPADA por r03, r04 |
| `m4_procedencia_sin_commit` (`--commit` ignorado) | **VIVA** | ATRAPADA por r10 |
| `m5_manifiesto_ignorado` (`ext["manifiesto"]` fijo en OK) | **VIVA** | ATRAPADA por r13 |

Las cuatro VIVAS no son defectos del evaluador (mis 13 pruebas pasan contra el real): son reglas de la adenda 4 sin vigilancia.
m4 la atraparia el ensayo en seco; m5 no la atrapa nada del candado (VCR-01, VCR-02, VCR-07).

### Punto 5: el ensayo en seco

Corrido hoy (`salida_ensayo_en_seco_r2.txt`): rc 0 y las 7 exigencias en SI, incluidas las dos nuevas (`procedencia INDECIDIBLE
(sin --commit)` y `manifiesto OK`). Los numeros son identicos a `ensayo_en_seco_salida.txt` (150 pasadas, INDECIDIBLE por
cobertura, port_s159 OK 148 comunes y 91 con pixeles, PM P2 GANA neto -25 B 29, M MEJORA n 78, Chillan 7 pares 6 a favor SIN
RESOLVER, protegidas fuera []); el `diff` de las lineas de numeros y controles da solo `manifiesto OK` (nuevo) y `procedencia OK`
a `INDECIDIBLE`. **Cumple.** Nota: la salida guardada en el candado es de la 01:23, anterior a la adenda 4, y no trae las dos
exigencias nuevas (VCR-10).

## 3. Hallazgos (lo peor primero; confianza y gravedad 1 a 5)

### VCR-01. La precedencia de la regla nueva (b) no tiene prueba: una mutacion que la evalue antes del veto de P1 queda viva
- ARCHIVO:LINEA: `evaluar_paquete.py:541-551` (orden correcto hoy); `probar_evaluar_paquete.py` (ninguna prueba con P1 VETADO y
  una protegida fuera con K publicando a la vez; t12/t33 solo tienen la fuera, t02/t17 solo el veto).
- QUE PASA: el codigo esta bien (mi r01 y r02 lo miden: P1 veto + protegida fuera da NO CANDIDATO; P2 PIERDE + fuera da NO
  CANDIDATO; SIN SUSTRATO + fuera da INDECIDIBLE). Pero si alguien moviera la condicion `prot_k` arriba del veto, un censo con una
  protegida perdida y otra fuera daria DECIDE NICOLAS en vez de NO CANDIDATO, y la bateria seguiria en verde.
- COMO REPRODUCIRLO: `python -I -B verificador_candado_r2/mutaciones_r2.py m1_prot_antes_que_p1` (mueve la condicion `prot_k`
  arriba del veto de P1): **VIVA** contra las 33 pruebas del candado; atrapada por r01, r02 y r08 (`salida_mutaciones_r2.txt`).
- CONFIANZA: CONFIRMADO (codigo leido; mutacion corrida). GRAVEDAD: 2 (hoy no tuerce nada; vigila una regla aprobada ayer).
- Cambio chico: una prueba con las dos cosas a la vez (mi r02 sirve tal cual) y la mutacion `m1_prot_antes_que_p1` en la lista.

### VCR-02. La lista «protegidas fuera del denominador» no tiene prueba que vigile la ETIQUETA: ampliarla a toda etiqueta no falla
- ARCHIVO:LINEA: `evaluar_paquete.py:521-523` (`f.get("lab") == "protegida"`); `probar_evaluar_paquete.py:230-233` (t12, segunda
  parte: negativo con escena invalida y k=0,4, pero solo exige `neto == -6`, no el veredicto ni la lista).
- QUE PASA: si la lista tomara bajo 1 MW o negativos con K publicando, el veredicto iria a DECIDE NICOLAS por una pasada que la
  regla aprobada no nombra (direccion segura, pero no es la regla). Hoy esta bien: r03 (bajo1 fuera, K publica) y r04 (negativo
  con escena invalida, K publica) dan CANDIDATO y lista vacia.
- COMO REPRODUCIRLO: `python -I -B verificador_candado_r2/mutaciones_r2.py m2_fuera_toda_etiqueta` (quita el filtro
  `lab == "protegida"` de la lista): **VIVA** contra la bateria; atrapada por r03 y r04 (`salida_mutaciones_r2.txt`).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (si se rompe, falla en direccion segura).
- Cambio chico: que t12 exija ademas `r2["veredicto"] == "CANDIDATO"` y lista vacia (una linea).

### VCR-03. El chequeo del manifiesto en el evaluador es autorreferente: compara el arbol local con el manifiesto local, no con el del tag
- ARCHIVO:LINEA: `manifiesto_candado.py:76-86` (`comprobar(ruta=MANIFIESTO, raiz=RAIZ)`), `evaluar_paquete.py:597-598`;
  `probe_paquete.py:204-209` (la cabecera lleva `commit`, `blobs` y el sha del tablero, no el hash del manifiesto).
- QUE PASA: quien lea el censo desde un arbol con el evaluador editado Y el manifiesto regenerado (`--escribir`) ve `manifiesto OK`.
  Lo unico que lo ata al candado es el commit del tag en `--commit`, que fija el arbol del RUNNER, no el del lector. Es relevante
  porque la adenda 4.5 anuncia que «el script se escribe y se prueba antes de leer el censo»: si ese trabajo tocara
  `evaluar_paquete.py`, el evaluador que lea seria otro que el sellado y nada lo diria. Hoy: `experiments/_s163_o2_modis/` no
  existe en este arbol (`ls`), y el evaluador no tiene nada de Delaunay ni `fillmissing` (`grep`).
- COMO REPRODUCIRLO: lectura; `grep -n "git\|ls-tree\|commit" manifiesto_candado.py` da 0 lineas de comparacion con un commit.
- CONFIANZA: CONFIRMADO (estructura); SOSPECHA (que el punto 5 toque el evaluador). GRAVEDAD: 2.
- Cambio chico: leer el censo desde el checkout del tag (o que el evaluador imprima el blob de `MANIFIESTO_CANDADO.json` junto al
  veredicto para cotejarlo con `git ls-tree <tag>`); y que el M con la regla de MATLAB sea un script aparte que lea
  `resultado_paquete.json` y las grillas, no una edicion de `evaluar_paquete.py`.

### VCR-04. `--commit` acepta un prefijo: `startswith`, hasta de una letra
- ARCHIVO:LINEA: `evaluar_paquete.py:610`.
- QUE PASA: `--commit f` da `procedencia OK` para cualquier commit que empiece con f (medido, r10: prefijo de 7 y de 1 dan OK). La
  adenda dice «exige que todos los jobs sean del commit del tag»; eso vale solo si quien lee pasa el sha completo.
- COMO REPRODUCIRLO: `pruebas_extra_r2.py`, filas «prefijo de 7» y «prefijo de 1» de r10.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.
- Cambio chico: `len(commit_esperado) == 40 and commits == [commit_esperado]`.

### VCR-05. «grilla incompleta, sola, no saca la pasada» es un caso que el port no puede producir: la pasada sale igual, como «escena invalida»
- ARCHIVO:LINEA: `probe_portes.py:338-339` (`grilla_incompleta` si `isnan(mir).sum() > mir.size // 2`); `mirova_port.py:86-88`
  (`detectar` pasa `mir` y `tir` tal cual al oraculo); `mirova_v750_r2.py:148-156` (`escena_invalida` si
  `isnan(nti).sum() >= floor(size/2)`, con `nti` NaN donde `mir` es NaN y ademas donde el TIR es frio).
- QUE PASA: si mas de la mitad de la grilla MIR es NaN, el NTI tiene al menos esos NaN, asi que la variante `fisica` declara
  `escena_invalida` siempre que el probe declare `grilla_incompleta`. El caso de t21 (grilla incompleta con detector corrido y
  cumbre publicable) es sintetico. Consecuencia: una protegida con media grilla vacia y K publicando NO cuenta como perdida de P1
  (como creia la vuelta 1), sino que va a DECIDE NICOLAS por la regla (b). Es coherente con el §8.5 (el `.m` declara la escena
  invalida), pero la frase de la adenda 4.1(a) promete una distincion que no existe en los datos.
- COMO REPRODUCIRLO: lectura de las tres lineas citadas (aritmetica: `> size//2` implica `>= floor(size/2)`).
- CONFIANZA: CONFIRMADO por lectura; no lo medi con una grilla real (SOSPECHA solo si `ORA.detectar` rellenara NaN antes de la
  linea 154, y no lo hace: `:148-153` solo agrega NaN).
- GRAVEDAD: 1. Cambio chico: una frase en la adenda (o ninguna).

### VCR-06. El `k_publica` de la lista sale de la publicacion del RUNNER, no del predicado del evaluador; el control 1 no cubre esas filas
- ARCHIVO:LINEA: `evaluar_paquete.py:522` (`(f.get("pub") or {}).get("K")`); `:156-158` (`armar_tabla` salta las no evaluables, asi
  que no tienen `_t`); `:418` (el control 1 compara predicado y runner solo en `_ev(filas)`).
- QUE PASA: para la protegida fuera del denominador, «K publica» es lo que dijo `probe_etiquetas.publica` en el runner (mismo
  `slim`, mismo node), sin la comprobacion cruzada que si tienen las evaluables. Medido (r09): con `pub.K = 0` en la fila, la lista
  dice `k_publica 0` y el veredicto es CANDIDATO aunque `k_slim` tenga 3 MW en la cumbre. El dato existe (`k_slim`) para pasarlo por
  el predicado del evaluador tambien.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (mismo codigo en los dos lados; es una asimetria, no un error observado).

### VCR-07. `externos_de_entrada` (manifiesto, blobs, predicado, procedencia, referencia, reetiquetado) no la toca ninguna prueba de la bateria ni ninguna mutacion
- ARCHIVO:LINEA: `probar_evaluar_paquete.py:108-115` (`correr` pasa `OK_EXT` directo a `evaluar`); `grep externos_de_entrada`
  en la bateria da 0 lineas.
- QUE PASA: las dos piezas nuevas de la adenda 4.2 viven ahi. La unica vigilancia es el ensayo en seco (que exige `procedencia
  INDECIDIBLE` sin `--commit` y `manifiesto OK`) y `probar_manifiesto`. Una mutacion que ignore `--commit` o que ponga
  `ext["manifiesto"] = {"estado": "OK"}` no puede ser atrapada por las 33 pruebas; la segunda tampoco por el ensayo (exige OK).
- COMO REPRODUCIRLO: `python -I -B verificador_candado_r2/mutaciones_r2.py m4_procedencia_sin_commit m5_manifiesto_ignorado`:
  las dos **VIVAS** contra la bateria; atrapadas por r10 y r13 (`salida_mutaciones_r2.txt`). m4 la atraparia tambien el ensayo
  en seco (exige `procedencia INDECIDIBLE` sin `--commit`); m5 no la atrapa nada del candado.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.
- Cambio chico: sumar r10 y r13 (o una prueba que llame a `externos_de_entrada` con cabeceras sinteticas) a la bateria.

### VCR-08. Si el arnes dejara de escribir `k33_slim`, el evaluador caeria en silencio al K33 del runner; la prueba sin red del arnes no exige el campo
- ARCHIVO:LINEA: `evaluar_paquete.py:164-166` y `:172-175` (`if "k33_slim" in f` ... si no, camino viejo); `probar_probe_paquete.py:135`
  (solo exige `k_slim`). Hoy el arnes lo escribe siempre que termina (`probe_paquete.py:154-158`, las dos claves en un mismo bucle).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1. Cambio chico: `exige("k33_slim" in rf ...)` en la prueba del arnes.

### VCR-09. El paso del job `prueba` depende de que la linea del `grep` sea la ultima
- ARCHIVO:LINEA: `probe-s162-modd.yml:84-85`.
- QUE PASA: bajo `bash -e`, `! cmd` y la primera mitad de un `a && b` no cortan el paso; el paso falla solo porque esa linea es la
  ultima y su codigo es el del script. Medido: `bash -e -c '! true; grep -q "pasan 0," /dev/null && grep -q "caen 0 " /dev/null'`
  da rc 1 (bien); con un `echo` detras da rc 0. Hoy esta bien; se rompe si alguien agrega una linea despues.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1. Cambio chico: `test "$(grep -c ... )"` o `if ! grep ...; then exit 1; fi`.

### VCR-10. Textos y salidas guardadas que quedaron de la adenda 3
- `evaluar_paquete.py:15-16` (docstring): sigue diciendo que «error» sale del denominador y que la protegida solo «se lista».
  `probe_paquete.py:3` y `probe-s162-modd.yml:3-4`: «adendas 1 a 3». `ensayo_en_seco_salida.txt` (01:23) es anterior a la adenda
  4 y no trae las dos exigencias nuevas, mientras las otras salidas se regeneraron a las 02:48.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VCR-11. Las tandas de mutaciones salen con codigo 1 al correr un subconjunto, y tardaron 6 h
- ARCHIVO:LINEA: `mutar_evaluar_paquete.py:145` (`atr == len(MUTACIONES)` exige las 31 aunque se pida un subconjunto).
- QUE PASA: correr las 31 en tres grupos (como se hizo) da tres salidas con `rc 1` y «N de 31» cada una; hay que sumar las tres
  tablas a mano para leer «31 de 31». No es un defecto del resultado; es una trampa para quien lea solo el codigo de salida.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1. Cambio chico: `atr == len(tabla)` o un `--grupo` que lo declare.

## 4. VERIFICADO LIMPIO (que no hace falta volver a mirar, y con que comando)

- **Diff de la adenda 4 acotado**: `git diff --stat b423316c2 ff2ced531` y el diff completo de `evaluar_paquete.py`: solo
  `evaluable`, `armar_tabla` (K33), `control_cobertura`, `veredicto` (fila 5), `externos_de_entrada`, `main`. `PREREGISTRO.md`:
  `--numstat` 39/0.
- **Regla (b) en la fila 5 y solo protegidas con K publicando**: `veredicto()` directo en las 8 combinaciones (r01); escenarios
  r02, r03, r04, r08; t12, t22, t33 de la bateria fallan contra el vacio.
- **Fallas del instrumento en rojo**: t20 y r05 (port), r06 (arnes `error` y `no_bajado`): cobertura INDECIDIBLE, veredicto
  INDECIDIBLE, `n_fallas_del_instrumento 1`.
- **`grilla_incompleta` sola cuenta**: t21 (protegida: P1 VETADO) y r07 (negativo: `s_b 1`, `n_evaluables` = todas).
- **Manifiesto**: `--comprobar` OK (39, 0 faltan, 0 distintos); 39 de 39 iguales a `git ls-tree HEAD`; r11 (alteracion de un byte,
  archivo faltante, modulo de MOD-B alterado, LF puro); r12 (rojo tumba el veredicto); r13 (el evaluador toma el estado de
  `comprobar`); `yml:70-75` y `:136` lo corren en los dos jobs; `"on"` parsea como cadena (A43, `yaml.safe_load`).
- **Procedencia**: r10, ocho casos (exacto OK; sin `--commit`, vacio, otro, dos commits, cabecera sin commit INDECIDIBLE; prefijos
  OK, ver VCR-04). Cabecera `commit` = `GITHUB_SHA` (`probe_cumulo.py:155-166`); `yml:146` guarda ademas `git rev-parse HEAD`.
- **Bateria**: 33 de 33 fallan por asercion contra el vacio (1,3 s); 33 de 33 pasan contra el real (`salida_bateria_real_r2.txt`, rc 0).
- **Ensayo en seco**: rc 0, 7 de 7, mismos numeros que la salida guardada salvo `manifiesto` (nuevo) y `procedencia`.
- **Grupos de mutaciones**: los 31 nombres de los tres `_grupo_mut_N.txt` son exactamente las 31 claves de `MUTACIONES`, sin
  repetidos ni faltantes (medido); cada sustitucion debe aparecer exactamente una vez o el mutador la marca invalida
  (`mutar_evaluar_paquete.py:112-116`).
- **Estados que escribe el instrumento** (para `evaluable`): `probe_portes.py:306,317,322,358,360` (`estado`: error de bajada,
  `volcan_fuera_del_granulo`, `ok`, `error: ...`), `:339` (`port_estado` `grilla_incompleta`), `mirova_v750_r2.py:155`
  (`motivo escena_invalida`); el arnes los copia en `port_estado` y `port_grilla` (`probe_paquete.py:162-163`) y escribe su
  propio `estado` `ok`, `error`, `no_bajado` (`:224,246,251,264`). Las cadenas de `evaluable()` coinciden.
- **Fecha**: el commit `ff2ced531` es de 2026-10-26T05:48:45Z, posterior a las 05:40 UTC que la adenda declara.
- **Remoto**: `origin/s162-modd-candado` = `ff2ced531`; no hay tag ni rama de disparo de MOD-D (`git ls-remote`).
- **Las 31 mutaciones**: 31 de 31 atrapadas por asercion en las tres tandas (`mutar_evaluar_paquete_salida_v3_g0/1/2.txt`), 0
  caen, 0 vivas, identidad 33 de 33 por tanda.
- **Diagnostico S-1 y arnes sin red**: `PRUEBA DIAGNOSTICO S-1 OK`; `atrapadas 6 de 6, caen 0, vivas 0`.

## 5. Veredicto

**Se puede despachar el humo con cambios chicos.** Los seis VCM estan arreglados, la regla nueva (b) hace lo aprobado y la
bateria la ejercita por los dos motivos con K publicando, ninguna otra regla sellada cambio, el manifiesto cubre lo que importan,
las 31 mutaciones caen por asercion y el ensayo en seco cumple. Ninguno de los cambios toca `pipeline/` ni re-sella una regla;
todos van ANTES del tag, porque el tag fija el arbol que se lee:
1. VCR-01 y VCR-02: una prueba con P1 veto y protegida fuera a la vez (r02 sirve tal cual) y que la segunda parte de t12 exija
   `CANDIDATO` y lista vacia; las mutaciones `m1_prot_antes_que_p1` y `m2_fuera_toda_etiqueta` a la lista.
2. VCR-07: una prueba que llame a `externos_de_entrada` con cabeceras sinteticas (r10 y r13 sirven) para que `--commit` y el
   manifiesto queden vigilados por la bateria y no solo por el ensayo.
3. VCR-04: `--commit` exacto de 40 caracteres, no `startswith`.
4. VCR-03 (procedimiento): leer el censo desde el checkout del tag, y el M con la regla de MATLAB (adenda 4.5) como script aparte
   que lea `resultado_paquete.json`, no como edicion de `evaluar_paquete.py`.
Lo demas (VCR-05, 06, 08, 09, 10, 11) se informa y no bloquea. Mis pruebas y mutaciones quedan en esta carpeta para reusarlas.

## 6. Nota de cierre: el arbol se movio debajo de la verificacion (08:50 local, 11:50 GMT)

Al cerrar, `git status` mostro **modificados sin commit** `evaluar_paquete.py` (08:50:22), `probar_evaluar_paquete.py` (08:50:49)
y `evaluar_vacio.py` (08:51:00), que yo no toque: otra sesion esta aplicando VCR-03, VCR-04 y VCR-06 de este informe en el mismo
worktree mientras yo cerraba (el diff lleva comentarios «VCR-0N (ronda 2)»). Consecuencias, con evidencia de esta sesion:
- **Todo lo medido arriba es del commit `ff2ced531`**: mis corridas terminaron entre las 03:05 y las 07:55 local, y las tandas
  del autor entre las 08:34 y las 08:48, todas ANTES del primer cambio (08:50:22). El veredicto vale para ese commit.
- **El arbol de trabajo ya no cumple su propio candado**: el blob LF de `evaluar_paquete.py` en disco es `f5be97b9c` y el
  manifiesto dice `957de7cdf`; `manifiesto_candado.py --comprobar` daria INDECIDIBLE hasta regenerar el manifiesto y commitear.
- **Las reglas corregidas se re-verifican** (regla del proyecto: cada vuelta encontro un error en la regla que decide). El cambio
  de VCR-06 que vi en el diff pasa las protegidas fuera por `predicado()` y pone el control 5 en rojo si difiere del runner; es
  logica nueva en `control_cobertura`, sin bateria corrida por mi. No lo verifique y no lo doy por bueno ni por malo.
- Nadie me aviso de estas ediciones; las vi por `git status`. Si el candado se despacha desde un commit posterior a `ff2ced531`,
  ese commit necesita su propia vuelta de verificador (puede ser corta: los caminos de esta carpeta sirven).

Pendientes que no me correspondian y no hice: commit, push, tag, rama de disparo, despacho, edicion de nada fuera de
`verificador_candado_r2/`.
