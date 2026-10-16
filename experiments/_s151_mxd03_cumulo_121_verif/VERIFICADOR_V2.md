# Verificador, segunda vuelta: pre-registro 1.21 (PR #840, head bce080328)

Worktree `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-aa3ef748ab319056b\`
en `bce080328` (`git log`), sin cambios al terminar (`git status --short` vacío). `gh pr view 840`: head
`bce0803284ab...`, `mergeStateStatus` CLEAN. Mis scripts: `C:\Users\nmend\AppData\Local\Temp\claude\verif_121\scripts\`.

## Veredicto: SELLABLE CON ARREGLOS (uno, chico, nuevo en la v2)

Los dos bloqueantes de la v1 están arreglados en el código, no sólo en el README, y cada arreglo
falla cuando se lo deshace. Queda un defecto que entró con la v2: el despacho partido en dos.

## Lo que corrí

- `pytest tests/test_mxd03_cumulo_121.py`: **45 passed** (eran 39).
- `probar_probe_cumulo.py`: OK, con el caso TEST1 en C 1 / CC 0.
- `cobertura_estimador.py` re-corrido (salida al temporal): **idéntico** a `cobertura_estimador_salida.txt`.

## Bloqueante 1 (rama del Test 1): arreglado

- El espía (`probe_cumulo.py:78-82`) guarda los cuatro argumentos y el resultado, y
  `cumulo_de_la_etiqueta` compara el cúmulo que vio `derivar` con el guardado.
- Caso TEST1 (`probar_probe_cumulo.py:59-75`, chequeos `:116-128`). Mutaciones **de código**
  (`mutaciones_v2.py`), no del dict de salida como las del test del autor:
  - M1, `derivar` ignora el pc (la rama no se ejercita): falla con `TEST1: publicaciones [1, 1, 1, 1, 1, 1]`.
  - M2, escena a +0,6 K, donde el Test 1 no dispara: falla con `TEST1: la fuente final de C no es test1`.
  - M3, espía ciego: falla con `TEST1: el espia no registro...`.
- La predicción como cota sale de los scripts: `fuente_test1|protegida|n = 4` y `pub_CC_cota = 4` en
  `prediccion_cumulo.json`. De ahí «42 a 46» y «0 a 4». Los 106 de los negativos limpios cuadran con
  `predecir_etiqueta_cumulo_salida.txt`.
- La prueba del replay se informa por grupo y la credibilidad se decide sólo con «resto»
  (`evaluar_cumulo.py:285-302`).
- La nota A45 está en el README.

## Bloqueante 2 (FRÁGIL): arreglado

Intersección de `perdidas_detalle` (`evaluar_cumulo.py:262-271`). Hice una copia del evaluador con la
línea global de la v1 (`fragil_mut.py`): `test_no_es_fragil_si_el_ruido_pierde_otra_pasada` **falla con
el global y pasa con la v2**. Es el caso en que deben diferir, porque el nulo pierde 1 protegida, pero
otra.

## Números nuevos del README

Coinciden con la salida re-corrida: apaga 50 / 70 / 90 % da MEJORA 0,050 / 0,463 / 0,917, y enciende
5 / 10 % da EMPEORA 0,020 / 0,393. Las filas viejas cambiaron (raro +28, A_solo +155, replay 0,997)
porque los escenarios nuevos consumen el mismo generador aleatorio. El README las actualizó: no es
una regresión.

## Anisotropía del nulo: basta documentarla

No bloquea, por cuatro razones:
- el veredicto global es el de la principal (MC contra C), que no usa el nulo;
- FRÁGIL sólo anota;
- las dos pérdidas de la 1.17 están a 15,6° y 17,4° de cenit, donde el nulo es comparable (razón 1,00);
- el README manda a leer FRÁGIL y `M_contra_ruido` por cenit.

El argumento del autor es correcto: corregirla dejaría sin control sintético un código que sólo corre
sobre el L1B real. Ojo con un detalle: FRÁGIL no viene partido por cenit. Hay que cruzar `fragil_pasadas`
con el cenit de cada clave a mano.

## Arreglo que queda (regresión de la v2)

**El despacho en dos partes no garantiza el mismo código** (A108). El README ahora despacha Lascar-2 y
después los otros 11, los dos con `--ref main`, y junta los 12 artefactos en local. Ningún JSON guarda
el commit: `grep GITHUB_SHA|rev-parse` sobre `probe_cumulo.py` y `probe_etiquetas.py` no da nada. Si entre
los dos despachos cambia `pipeline/`, el veredicto mezcla dos pipelines sin que nada lo detecte. El
arreglo:
- escribir `GITHUB_SHA` en el JSON de cada job;
- que `evaluar_cumulo.py` dé INCOMPLETO si hay más de un commit;
- o, como mínimo, despachar los dos desde un mismo tag.

## No bloqueantes

- El grupo `fuente_test1` del replay sale de la fuente **guardada** (`p["fuente"]`), no de la medida en C
  hoy. Conviene informar también por `f["brazos"]["C"]["fuente"]`.
- El test de mutación del autor muta la salida, no el código. Las mutaciones de arriba cubren ese hueco.
