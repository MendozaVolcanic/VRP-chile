# Verificacion con contexto limpio del candado MOD-D, tercera vuelta (arreglos VCR-01 a VCR-10)

Hora del servidor de GitHub: al empezar Mon, 26 Oct 2026 12:58:29 GMT; caminos de ruptura escritos antes de abrir el codigo a las
12:59:12 GMT (sha256 `3efd8210e8265d5d12451e7a6f9cfb22cf1d17a150febda299bc793c24dfce08`, en `CAMINOS.md` y `CAMINOS.sha256.txt`);
al cerrar Mon, 26 Oct 2026 13:43:07 GMT. Material: worktree `C:\vrp-trabajo\s162-modd`, rama `s162-modd-candado`, HEAD
`1166cea702d00516e36934ca7dfa41b29f3fe3d5` = `origin/s162-modd-candado` (`git rev-parse`, `git ls-remote`); el arbol solo tenia sin
seguimiento esta carpeta. Modelo: Claude Sonnet 5.5; esfuerzo: el que fijo quien me lanzo (no lo veo desde adentro).

**Que no mire**: el arnes real con red (`probe_paquete.py` sobre HDF; pyhdf no corre en Windows), `recorrer_en_sha.py`, el contenido
del `.m` de MIROVA ni la verificacion de la regla de Delaunay contra MATLAB (191 de 191: solo comprobe que las cifras de la
adenda coinciden con `RESULTADO_O2_MODIS_MATLAB.md`), el cuerpo de `delaunay_perturbado.py` mas alla de su cabecera e imports, la
corrida del humo en GitHub (el job no corrio nunca todavia), y la logica de las 31 mutaciones antiguas salvo las 6 que repeti. No
vi la primera vuelta; de la segunda lei su `INFORME.md` (lista VCR-01 a VCR-11) antes de escribir los caminos. Discos: al empezar C:
16 GB y D: 8,4 GB libres, al cerrar C: 15 GB y D: 8,4 GB (siempre sobre 3 GB).

Todo lo que afirmo sale de un archivo que lei o de un comando que corri en esta sesion; lo que no, va como SOSPECHA.

## En una pantalla

1. **Los diez arreglos de la segunda vuelta estan hechos y ninguno abrio un defecto que tuerza un veredicto.** El diff de
   `evaluar_paquete.py` entre `ff2ced531` y `1166cea70` son 21 lineas nuevas y 6 borradas, solo en el docstring,
   `control_cobertura`, `externos_de_entrada` y un `print` de `main`; P1, P1b, P2, M, Chillan, `veredicto` y `evaluable` no cambian.
2. **La logica nueva de «K publica» para las protegidas fuera del denominador es correcta y de direccion segura**: sale del
   predicado sobre `k_slim`, se compara con lo que dijo el runner y una diferencia pone el control 5 en rojo (INDECIDIBLE); `--commit`
   exige 40 caracteres e igual. Batería: 37 de 37 pasan contra el real; contra el vacio fallan 37 de 37 por aserción, 0 caen.
3. **El apendice de la adenda 4 no cambia ninguna regla sellada** (29 lineas nuevas, 0 borradas; las cifras de MATLAB coinciden con su
   documento). Matiz: VCR-04 y VCR-06 endurecen dos puertas del instrumento (en direccion segura) y el apendice dice «nada cambia».
4. **Mutaciones**: las 6 nuevas corrieron sobre el codigo final y quedan atrapadas por aserción; las 31 anteriores corrieron sobre
   `ff2ced531` y ninguna toca una linea que cambio (las 37 sustituciones aparecen exactamente una vez hoy; repeti 6 de las
   adyacentes sobre el codigo de hoy: 6 de 6 atrapadas, identidad 37 de 37). Pero hay huecos chicos nuevos (VC3-01, 06, 07, 09).
5. **`m_con_regla_matlab.py` hace lo que dice** (script aparte, importa el evaluador sin editarlo, su `--probar` puede fallar y lo
   corri de punta a punta sobre artefactos sinteticos), con una cobertura de prueba mas corta que su alcance (VC3-03, VC3-04).
   **Veredicto: se puede despachar el humo tal como esta**; lo de abajo son endurecimientos opcionales, ninguno bloquea.

## 1. Que corri y que dio

Desde `experiments/_s162_modis_paquete/`, `PYTHONIOENCODING=utf-8 VRP_PROFILE=mirova_equivalent python -I -B ...`.

| que | resultado | salida |
|---|---|---|
| `manifiesto_candado.py --comprobar` | `estado OK, n 41, faltan [], incompleto False, distintos []`, prueba del manifiesto True, rc 0 | `salida_manifiesto_r3.txt` |
| los 41 hashes contra `git ls-tree HEAD <ruta>` | 41 de 41 iguales, 0 distintos (comando en §4) | en este informe |
| `probar_evaluar_paquete.py` (real) | `pasan 37, fallan 0, caen 0 (de 37)`, rc 0 | `salida_bateria_real_r3.txt` |
| `probar_evaluar_paquete.py --modulo evaluar_vacio.py` | `pasan 0, fallan 37, caen 0 (de 37)`, rc 1; las 37 por aserción (t35, t36 y t37 ya no «caen»: el vacio ahora tiene `externos_de_entrada`) | `salida_bateria_vacio_r3.txt` |
| `ensayo_en_seco.py --ref D:/vrp-trabajo/temporales/s162_mxd03/ref` | rc 0, 7 de 7 exigencias SI; las lineas de controles, brazos, Chillan y manifiesto son **iguales** a `ensayo_en_seco_salida.txt` (`diff` vacio); `blob_manifiesto` impreso `c3bc1c3af...` = blob del `MANIFIESTO_CANDADO.json` de HEAD | `salida_ensayo_en_seco_r3.txt` |
| `probar_probe_paquete.py` | `SIN MUTAR: OK`, `atrapadas 6 de 6, caen 0, vivas 0`, rc 0 (exige ahora `k33_slim`) | `salida_probar_probe_r3.txt` |
| `m_con_regla_matlab.py --probar` | `{'vrp_port': 3.7588..., 'vrp_regla': 3.7588..., 'semillas_donde_difieren': 13}`, rc 0 | `salida_m_probar_r3.txt` |
| `m_con_regla_matlab.py` completo sobre artefactos sinteticos (jsonl + `grilla_NNN.npz`) | corre de punta a punta, escribe `m_con_regla_matlab.json`, 3 pares | `extremo_a_extremo_m_r3.py`, `salida_extremo_a_extremo_m_r3.txt` |
| identidad de `hueco`/`vrp_con` con `mirova_port.vrp` en n = 1, 2, 4, 5, 12, 30, 31, 45 (12 escenas c/u, con bandas NaN y bordes) | 0 de 96 fallan | `pruebas_extra_r3_m.py` |
| 10 mutaciones propias de `m_con_regla_matlab.py` (mas la copia sin mutar) contra su `probar()` | 3 atrapadas, 7 vivas, la copia sin mutar pasa (§3 VC3-03) | `mutaciones_m_r3.py`, `salida_mutaciones_m_r3.txt` |
| 12 mutaciones propias del evaluador, sobre un subconjunto de 12 pruebas (t01, t11, t12, t17, t20, t21, t22, t33 a t37) | atrapadas 2, vivas 10 (de ellas 2 equivalentes en la practica, ver VC3-08 y VC3-11) | `mutaciones_r3.py`, `salida_mutaciones_r3*.txt` |
| 6 de las 31 mutaciones antiguas repetidas sobre el codigo de hoy (`mutar_evaluar_paquete.py <nombres>`) | identidad 37 de 37; 6 de 6 atrapadas por aserción, 0 caen, 0 vivas | `salida_mutaciones_viejas_a_r3.txt`, `_b_r3.txt` |
| workflow: `yaml.safe_load` | claves `['name', 'on', 'concurrency', 'env', 'jobs']`, la clave `on` es `str`; jobs `plan, prueba, probe` | en este informe |

## 2. Veredicto por arreglo

| arreglo | hecho | abrio otro defecto | donde y que lo prueba |
|---|---|---|---|
| **VCR-01** precedencia del veto de P1 | **si** | no | `probar_evaluar_paquete.py:430-437` (t34: P1 vetado + protegida fuera con K publicando exige `NO CANDIDATO` y exactamente 1 fila en la lista); mutacion nueva `prot_fuera_antes_que_p1` atrapada por t34 (`mutar_evaluar_paquete_salida_v4_a.txt`); t34 falla contra el vacio |
| **VCR-02** etiqueta de la lista | **si, en lo que el informe pedia** | no | `:232-237` (t12, segunda parte: `CANDIDATO` y lista `[]` para un negativo fuera con K publicando); mutacion `fuera_toda_etiqueta` atrapada por t12. Queda libre el caso bajo1 (VC3-06) |
| **VCR-03** chequeo autorreferente | **parcial, por diseño** | no | el evaluador imprime el blob del manifiesto (`evaluar_paquete.py:611`, `:730`) para cotejarlo con `git ls-tree <tag>`; el resto es procedimiento (apendice punto 2). Nada compara el HEAD local con `--commit` (VC3-02); la impresion no tiene prueba |
| **VCR-04** `--commit` exacto | **si** | no | `evaluar_paquete.py:624` (`len == 40` e igualdad de lista); t35 cubre exacto, sin commit, prefijo de 7, otro, dos commits; mutaciones `procedencia_sin_commit` y `procedencia_prefijo` atrapadas por t35. Quitar solo el `len == 40` no se ve (VC3-08) |
| **VCR-05** grilla incompleta | **si (solo texto)** | no | apendice punto 4, y mi lectura de la ultima vuelta sigue en pie: no hay cambio de codigo; `evaluable` (`:137-151`) intacto |
| **VCR-06** «K publica» por el predicado | **si** | no (ver §3 VC3-10 por lo no ejercido con datos reales) | `evaluar_paquete.py:519-537`; t37 (`pub={"K":0}` con k=3,0 en una fuera exige `k_publica 1`, `INDECIDIBLE`); mutaciones `k_publica_del_runner` (t37) y mi `falla_solo_si_runner_mayor` (t37) atrapadas; mi `falla_solo_si_pub_mayor` queda VIVA (VC3-01) |
| **VCR-07** `externos_de_entrada` sin prueba | **si** | no | t35 y t36 llaman a la funcion real; `evaluar_vacio.py` gano `BLOBS_SELLADOS` y su propia `externos_de_entrada`, asi que contra el vacio ahora fallan por aserción, no por excepcion; `manifiesto_ignorado` atrapada por t36. Queda sin prueba el pegamento `ctl.update(externos)` (VC3-09) |
| **VCR-08** `k33_slim` en el arnes | **si** | no | `probar_probe_paquete.py:136-137` exige `k33_slim` con `primary_cluster`; la prueba pasa (`SIN MUTAR: OK`) |
| **VCR-09** paso del vacio en el yml | **si** | no | `probe-s162-modd.yml:86-89`: `if ! grep ... || ! grep ...; then exit 1; fi`, ya no depende de que sea la ultima linea; `-e` por defecto de GitHub y `pipefail` puesto |
| **VCR-10** textos | **si** | no | docstring `evaluar_paquete.py:15-17`, cabeceras `probe_paquete.py:3` y `yml:3-4` dicen «adendas 1 a 4»; `ensayo_en_seco_salida.txt` regenerado con las dos exigencias nuevas (lei su diff); `grep "adendas 1 a 3"` sobre `*.py` y el yml: 0 coincidencias |

Sobre **VCR-06 y falsos rojos** (el camino 8 de `CAMINOS.md`): `predicado([(None, inner)])` devuelve `(0, 0.0)` sin llamar a node
(`evaluar_paquete.py:125-126`), asi que una fila con `k_slim` nulo no revienta; el arnes escribe `k_slim = None` solo si K no
devolvio record (`probe_paquete.py:154-158`) y en ese caso `P.publica` del runner tampoco publica (mismo origen), de modo que los dos
lados coinciden. Tipos: el predicado da `int(p[4])`, el runner `int(... or 0)`, los dos enteros. Lo medi con t37 (y sus dos
mutaciones) pero **no con datos reales**: el ensayo en seco da `protegidas fuera del denominador: []` (VC3-10).

## 3. Hallazgos (lo peor primero; confianza y gravedad 1 a 5)

### VC3-01. El control de VCR-06 solo esta vigilado en una direccion: una mutacion `pub > runner` queda viva
- ARCHIVO:LINEA: `evaluar_paquete.py:532` (`if pub != runner:`); `probar_evaluar_paquete.py:475-483` (t37 solo tiene predicado 1 y runner 0).
- QUE PASA: si alguien «simplificara» la comparacion a `pub > runner`, el caso inverso (el runner dice que K publica y el predicado
  dice que no) dejaria de poner el control en rojo y nada lo veria. Hoy el codigo es correcto.
- REPRODUCIR: `python -I -B verificador_candado_r3/mutaciones_r3.py falla_solo_si_pub_mayor` (VIVA; `falla_solo_si_runner_mayor` en cambio la atrapa t37).
- CONFIANZA: CONFIRMADO (4). GRAVEDAD: 2. Cambio chico: una segunda protegida fuera con `pub={"K":1}` y `k=None` (o `k=0`) exigiendo rojo.

### VC3-02. VCR-03 queda en procedimiento: nada compara el arbol que lee con el commit del tag, y la impresion del hash del manifiesto no tiene prueba
- ARCHIVO:LINEA: `evaluar_paquete.py:605-611`, `:730`; apendice punto 2.
- QUE PASA: el control `manifiesto` sigue comparando el arbol local con su manifiesto local. Lo que ata al tag es que quien lee
  coteje el blob impreso con `git ls-tree <tag> experiments/_s162_modis_paquete/MANIFIESTO_CANDADO.json`. El evaluador podria
  tambien comparar `git rev-parse HEAD` con `--commit`; no lo hace. Y quitar la linea que agrega `blob_manifiesto` no la ve ninguna
  prueba (mutacion `sin_blob_manifiesto`: VIVA); el ensayo en seco solo exige `manifiesto OK`.
- CONFIANZA: CONFIRMADO (4) para la estructura; es una decision de diseño que el apendice declara. GRAVEDAD: 2 (la direccion es segura: un arbol distinto da manifiesto INDECIDIBLE o blob distinto).
- Cambio chico: dejar escrito en el prompt de la lectura el comando `git ls-tree` a cotejar, o agregar el chequeo de HEAD contra `--commit`.

### VC3-03. La prueba de `m_con_regla_matlab.py` es mas corta que lo que el script hace: 7 de 10 mutaciones propias la dejan pasar
- ARCHIVO:LINEA: `m_con_regla_matlab.py:44-48` (`hueco`, regla de k = 3 / 5 / 7), `:57-61` (`mascara`), `:67-85` (`pares_con_regla`), `:112-143` (`probar`).
- QUE PASA: `probar()` usa una escena de 1 pixel (k = 3), asi que cambiar la rama k = 5 o k = 7 (`k_siempre_3`, `k_5_en_vez_de_7`,
  `corte_30_a_20`, `corte_4_a_2`), trasponer filas y columnas de la mascara (`mascara_traspuesta`) o sacar el filtro de pares
  (`pares_sin_filtro_pub_k`) no falla; tambien `umbral_distintas_0` (la exigencia «difieren en al menos 5 de 20» no se vigila). Si
  caen las tres que si deben: `coef_mal` (identidad con el port), `regla_es_el_port` (difieren en 0 de 20) y
  `regla_marco_col_fila_solo_en_regla` (aserción «regla a mano»).
  La prueba **si puede fallar** y mide lo que dice en el sentido que dice (identidad con `mirova_port.vrp` a 1e-12; la regla distinta
  del port en 13 de 20 escenas); pero la identidad solo se mide en el caso de un pixel. Medi yo la identidad en n = 1 a 45: 0 de
  96 fallan, asi que hoy el codigo es correcto. Ademas la segunda aserción («regla a mano») arma el hueco con la misma funcion que
  el calculo, y por eso en parte repite lo que prueba.
- REPRODUCIR: `python -I -B verificador_candado_r3/mutaciones_m_r3.py` (tabla en `salida_mutaciones_m_r3.txt`); `pruebas_extra_r3_m.py`.
- CONFIANZA: CONFIRMADO (4). GRAVEDAD: 2 (columna informativa, no decide; pero se publica «al lado de la sellada»). Cambio chico:
  que `probar()` repita la identidad con n = 5 y n = 31 y con la mascara de dos pixeles no simetrica.

### VC3-04. El alcance de la validacion con MATLAB (huecos de 3 x 3, sin alertas de borde) es mas angosto que el alcance de uso de la columna
- ARCHIVO:LINEA: `PREREGISTRO.md` apendice punto 8; `m_con_regla_matlab.py:7-10` (docstring), `:44-48`; `RESULTADO_O2_MODIS_MATLAB.md` (lineas 8-9: «todas tienen hueco de 3 × 3 (4 píxeles o menos) y ninguna alerta cerca del borde»).
- QUE PASA: el apendice y el docstring dicen que 161 de las 191 escenas son de Láscar y de 3 x 3, pero `m_con_regla_matlab.py`
  aplica la regla tambien a alertas de 5 a 30 pixeles (k = 5) y de mas de 30 (k = 7), y a las de borde; ahi «reproduce MATLAB»
  es extrapolacion (SIN DATO), y la regla del hueco k = 5/7 (copiada del `.m`) la comprueba solo mi identidad contra el port, no
  contra MATLAB. Tambien: la cabecera de `delaunay_perturbado.py` dice todavia «SOSPECHA, NO DATO: que MATLAB use CGAL», anterior al
  resultado que el apendice invoca.
- CONFIANZA: CONFIRMADO (4) en lo escrito; que importe en el censo es SOSPECHA. GRAVEDAD: 2. Cambio chico: una frase en el apendice o en la salida del script que cuente cuantos pares tienen k > 3 y cuantos son de borde.

### VC3-05. `--commit` en `m_con_regla_matlab.py` se imprime pero no se compara con la cabecera, y el script no pasa por el control `manifiesto`
- ARCHIVO:LINEA: `m_con_regla_matlab.py:148-153`.
- QUE PASA: el JSON guarda `commits` y `commit_esperado` lado a lado, sin comparar; el script no llama a `manifiesto_candado.comprobar`. Esta cubierto por el procedimiento (leer desde el tag), no por codigo.
- CONFIANZA: CONFIRMADO (4). GRAVEDAD: 1.

### VC3-06. Un bajo1 fuera del denominador con K publicando no esta vigilado: `fuera_protegida_o_bajo1` queda viva
- ARCHIVO:LINEA: `evaluar_paquete.py:521-522`; `probar_evaluar_paquete.py:221-237` (t12 usa un negativo).
- QUE PASA: ampliar la lista a `lab in ("protegida", "bajo1")` mandaria a DECIDE NICOLAS un censo que la regla aprobada manda a CANDIDATO; no falla ninguna prueba. Direccion segura.
- REPRODUCIR: `mutaciones_r3.py fuera_protegida_o_bajo1` (`salida_mutaciones_r3_b.txt`). CONFIANZA: CONFIRMADO (4). GRAVEDAD: 1.

### VC3-07. En las pruebas K y K33 valen lo mismo: no se ve si la lista usa `k_slim` o `k33_slim`
- ARCHIVO:LINEA: `evaluar_paquete.py:526` (`f.get("k_slim")`); el `fila()` de las pruebas arma `k_slim` y `k33_slim` iguales.
- QUE PASA: mutacion `sel_usa_k33` VIVA. En datos reales difieren solo con B22 saturada. CONFIANZA: CONFIRMADO (4). GRAVEDAD: 1.

### VC3-08. `len == 40` en `--commit` no tiene prueba propia
- ARCHIVO:LINEA: `evaluar_paquete.py:624`. `ok_sin_len40` (quitar la clausula, queda `commits == [commit_esperado]`) VIVA, porque t35 usa un `--commit` corto frente a una cabecera de 40. Equivalente en la practica mientras la cabecera lleve `GITHUB_SHA` (40 caracteres). Tampoco hay prueba de mayusculas (`commit_mayusculas_normaliza` VIVA; hoy mayusculas dan INDECIDIBLE, direccion segura). GRAVEDAD: 1. CONFIANZA: CONFIRMADO (4).

### VC3-09. Ninguna prueba de la bateria pone un `manifiesto`, `procedencia` o `blobs` rojo dentro de `evaluar()` y comprueba que tumba el veredicto
- ARCHIVO:LINEA: `evaluar_paquete.py:576` (`ctl.update(externos)`); `probar_evaluar_paquete.py:292` (el unico externo rojo inyectado es `referencia`).
- QUE PASA: t35 y t36 llaman a `externos_de_entrada`, no a `evaluar`. Mis tres mutaciones que sacan una de esas tres claves de los controles quedan VIVAS (`manifiesto_fuera_de_controles`, `procedencia_fuera_de_controles`, `blobs_fuera_de_controles`; subconjunto de 12 pruebas, pero el `grep` de `ext=` en toda la bateria da una sola inyeccion, la de `referencia`). El ensayo en seco si lo cubre para `manifiesto` y `procedencia` (exige `procedencia INDECIDIBLE` y `manifiesto OK` leidos de los controles de `main`), pero el ensayo no corre en el workflow.
- CONFIANZA: CONFIRMADO (4) en que ninguna prueba lo cubre; el codigo es una linea generica. GRAVEDAD: 1.

### VC3-10. El camino nuevo de VCR-06 sobre datos reales no se ha ejercido: el ensayo en seco da `protegidas fuera del denominador: []`
- ARCHIVO:LINEA: `ensayo_en_seco_salida.txt` (linea «protegidas fuera del denominador: []»).
- QUE PASA: la primera vez que `predicado([... k_slim ...])` se ejecuta con una fila real de «volcan fuera del granulo» o «escena invalida» sera en el humo o en las tandas. Si K y el predicado discreparan por una razon que no vi, el efecto es INDECIDIBLE (se repite la parte), no un veredicto torcido. No pude comprobar si alguna de las 5 pasadas del humo cae en esos motivos (no corri el humo).
- CONFIANZA: SOSPECHA (2) de que pueda ocurrir; CONFIRMADO que no esta ejercido. GRAVEDAD: 1.

### VC3-11. Equivalente: `motivo_extra_grilla_incompleta` queda «viva» porque no es un cambio observable
- `MOTIVOS_SELLADOS + "falla_port_grilla_incompleta"` (mutacion propia) no cambia nada: el probe escribe «grilla_incompleta» en `port_grilla`, no en `port_estado` (`probe_paquete.py:162-163`), asi que `evaluable` nunca produce ese motivo. No es un hueco; lo anoto para que nadie lo agregue a la lista de mutaciones. GRAVEDAD: 1.

### VC3-12. El apendice dice «Nada de esto cambia una regla sellada», pero VCR-04 y VCR-06 agregan dos condiciones de rojo
- ARCHIVO:LINEA: `PREREGISTRO.md` apendice, frase inicial y puntos 3 y 5.
- QUE PASA: el control 5 gana una causa de rojo (predicado distinto del runner) y la procedencia deja de aceptar prefijos. Las dos solo pueden convertir un resultado en INDECIDIBLE, nunca en CANDIDATO, y estan escritas en el mismo apendice; el §6 y los demas controles no cambian (lo medi con el diff). Es una precision de redaccion, no un cambio de regla. GRAVEDAD: 1. CONFIANZA: CONFIRMADO (4).

### VC3-13. El umbral de `probar()` (difieren en al menos 5 de 20) esta medido solo en Windows
- ARCHIVO:LINEA: `m_con_regla_matlab.py:139-142`. Medi 13 de 20 aqui; el job `prueba` lo corre en ubuntu con otra version de scipy/Qhull y una falla alli detendria el humo (falso alto). El margen (13 contra 5) es amplio.
- CONFIANZA: SOSPECHA (2). GRAVEDAD: 1.

### VC3-14. Informacion: las 31 mutaciones antiguas corrieron sobre el codigo anterior a esta ronda
- Salidas `mutar_evaluar_paquete_salida_v3_g0/1/2.txt`: identidad `33 de 33`, 11 + 10 + 10 atrapadas por aserción, 0 caen, 0 vivas; las dos v4 (`_a`, `_b`): identidad `37 de 37`, 3 + 3. La union de las cinco salidas son exactamente las 37 claves de `MUTACIONES` (medido), todas ATRAPADA.
  El codigo de `evaluar_paquete.py` no cambio entre `eb98bf9d6` y `1166cea70` (el diff solo toca manifiesto y salidas), asi que las v4 valen para HEAD. Las v3 se corrieron antes de la ronda: ninguna de las 31 toca una linea cambiada (comparacion por lineas con `difflib`, §4), y repeti 6 de las mas cercanas a las zonas cambiadas sobre el codigo de hoy: 6 de 6 atrapadas (`escena_invalida_cuenta`, `falla_del_port_no_roja`, `grilla_incompleta_sale`, `cobertura_sin_duplicados`, `protegida_fuera_no_decide`, `protegida_fuera_sin_mirar_k`). Las otras 25 no las repeti: SOSPECHA sobre su validez individual hoy, aunque las pruebas son un superconjunto de las que las atrapaban y su codigo no cambio.
- GRAVEDAD: 1. CONFIANZA: CONFIRMADO (4) en lo medido.

## 4. VERIFICADO LIMPIO (no hace falta volver a mirar, y con que comando)

- **Diff acotado**: `git diff ff2ced531..1166cea70 -- experiments/_s162_modis_paquete/evaluar_paquete.py` (hunks solo en docstring, `control_cobertura`, `externos_de_entrada`, `main`); `git diff --numstat ... PREREGISTRO.md` da `29 0`; en `veredicto`, `evaluable`, `p1`, `p2`, `m`, `chillan` no hay hunks.
- **Manifiesto = commit**: `python -I - <<'EOF'` que recorre `MANIFIESTO_CANDADO.json` y compara con `git ls-tree HEAD <ruta>` dio `41 41 distintos al blob de HEAD: []`; en el diff, los archivos nuevos que el evaluador/arnes usan (`m_con_regla_matlab.py`, `delaunay_perturbado.py`) estan en el manifiesto; lo que queda fuera (salidas, verificadores, `MANIFIESTO_CANDADO.json` mismo) no es importado por nadie.
- **Workflow**: `python -I -c "import yaml;d=yaml.safe_load(open('.github/workflows/probe-s162-modd.yml',encoding='utf-8'));print(list(d.keys()))"` → `['name', 'on', 'concurrency', 'env', 'jobs']`, `on` es `str`, no booleano; el paso `prueba` corre `--probar` de M con `VRP_PROFILE` y `pipefail`; `pip install numpy scipy pyyaml pyproj` cubre `scipy.ndimage` y `scipy.spatial`; el job `probe` sigue comprobando el manifiesto antes del arnes (`yml:140`).
- **Bateria**: 37 de 37 contra el real; 37 de 37 fallan por aserción contra el vacio (§1).
- **Ensayo en seco**: rc 0, 7 de 7, numeros iguales a la salida guardada.
- **Arnes sin red**: `SIN MUTAR: OK`, `atrapadas 6 de 6`.
- **M con la regla de MATLAB**: script aparte (no escribe `evaluar_paquete.py`, solo lo importa: `import evaluar_paquete as EP`, `:36`); lee `resultado`/artefactos con `EP.cargar`, `EP.unir`, `EP.armar_tabla`; usa las mismas formulas de `d` y `regla_m` que `EP.m` (`m_con_regla_matlab.py:88-98` contra `evaluar_paquete.py:269-276`); el blob de `delaunay_perturbado.py` es `f273a47a...` = el del manifiesto = el de `experiments/_s163_o2_modis/delaunay_perturbado.py` (`git hash-object`); las cifras del apendice (191 de 191, 161 de Lascar, 12 ordenes) coinciden con `RESULTADO_O2_MODIS_MATLAB.md`; el conteo de rayas largas y medias (con Python, U+2014 y U+2013) da 0 en `PREREGISTRO.md` y `m_con_regla_matlab.py`.
- **Las 37 sustituciones** aparecen exactamente una vez en `evaluar_paquete.py` de HEAD (script en linea con `mutar_evaluar_paquete.MUTACIONES`).
- **Remoto**: `git ls-remote origin s162-modd-candado` = `1166cea70`. Tag: no lo revise (el encargo dice que se crea despues de esta vuelta).

## 5. Veredicto final

**Se puede despachar el humo tal como esta.** Los diez arreglos estan hechos en el codigo, ninguno cambia una regla sellada ni abre un
defecto que pueda convertir un veredicto malo en CANDIDATO (lo nuevo solo puede llevar a INDECIDIBLE o a DECIDE NICOLAS), la bateria y
las mutaciones del candado estan en verde y atrapan por aserción, el manifiesto coincide con el commit y cubre los archivos nuevos, y
el workflow sigue siendo valido. Los hallazgos VC3-01 a VC3-14 son huecos de vigilancia de gravedad 1 a 2, todos en direccion segura;
arreglarlos obligaria a regenerar el manifiesto, crear otro commit y otra vuelta antes del tag, y no compensa. Si de todos modos se
abre otra ronda, lo mas util en orden: VC3-01 (una prueba inversa en t37), VC3-03 (identidad de `probar()` con n = 5 y 31) y VC3-02
(el comando `git ls-tree` en el prompt de lectura). Mis scripts y salidas quedan en esta carpeta.

Pendientes que no me correspondian y no hice: commit, push, tag, rama de disparo, despacho, edicion de nada fuera de `verificador_candado_r3/`.
