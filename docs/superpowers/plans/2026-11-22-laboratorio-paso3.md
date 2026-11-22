# Perfil `laboratorio`, paso 3 (S195): zona A en la vía y barrido de 9 brazos

> **Para agentes:** se ejecuta en línea con `executing-plans` y `test-driven-development`. Pasos con casillas.

**Objetivo:** dar efecto a la zona A del perfil `laboratorio` (extensión MEJ-5) dentro de la vía «código MIROVA»,
sólo cuando un perfil la enciende, y dejar listo (sin despachar) el barrido de 9 brazos s = 5,0 a 1,0 que pide
`experiments/_s194_lab_zona_a/evaluar.py calibrar` (§5 del PREREGISTRO sellado).

**Base:** `origin/main` en `3bb44e830`, tag defensivo `pre-s195-laboratorio-paso3` (A45: Nicolás, 2026-11-22,
«Sí, A45 (Recomendado)» a implementar la zona A en la vía sólo para el laboratorio y correr el barrido; toca
`pipeline/mirova_v750_codigo.py` y `pipeline/profile.py`). Producción no cambia ni un byte.

**Decisión de diseño (Nicolás, 2026-11-22, opción (a), textual: «(a) Sólo la caja sensible (Recomendado)»):** la
zona A es el círculo de `inner_radius_km` alrededor del cráter **cortado por la región sensible** de la vía
(BOX == 2). Por qué: el pre-registro sellado exige que el brazo s = 5,0 dé exactamente las cuentas de producción
(`evaluar.control_barrido`). Con la zona A como el círculo entero y los pisos sensibles, 4.636 celdas de la zona A
(10 volcanes, 3 sensores) que en producción son conservadoras (s1 = 10, pisos 0,02 / 0,01) bajarían de umbral con
s = 5, y el control fallaría por construcción (conteo:
`experiments/_s195_lab_paso3/contar_zona_a_fuera_de_sensible.py`, salida `salida_contar_zona_a.txt`). Con la intersección, s = 5 es la
identidad exacta y el sello vale tal cual. Lo que se pierde: la extensión sólo baja s2 dentro de la caja sensible
(5 x 5 en MODIS, 7 x 7 en VIIRS 750, C13 en VIIRS 375), no en el anillo entre la caja y el círculo.

## El fenómeno y el mecanismo

Un foco chico en el cráter calienta su celda lo justo para quedar bajo el umbral contextual de MIROVA,
`max(mu + s2·sd, piso)` con s2 = 5 de noche en la región sensible. La zona A cambia sólo ese multiplicador, a `s_A`,
en las celdas sensibles a no más de `inner_radius_km` del cráter, con los mismos pisos (0,003 / 0,003) y los mismos
`mu` y `sd` de toda la grilla. Menor `s_A`, más alertas (monótono); `s_A <= s2` (si no, el laboratorio vería menos
que producción en el cráter). Sólo de noche (MIR sólo nocturno; de día el .m usa s = 15 en las dos regiones y la zona
no actúa). Cordón Caulle fuera (`volcanes_fuera`, D6).

## Archivos

- Modificar `pipeline/mirova_v750_codigo.py`:
  - `_pasada_contextual(..., zona_a=None, s_a=None)`: si hay zona, `u_ntiA = max(mu + s_a·sd, n2)` y
    `u_etiA = max(mu_e + s_a·sd_e, e2)` (mismo manejo de NaN que u2), y la región 2 compara contra
    `np.where(zona_a, u_A, u_2)`. `s_a > s2` es error.
  - `detectar_mirova(..., zona_a=None, s_a=None)`: pasa la zona a los dos pases sólo si `dayflag == 0`; guarda
    `d["zona_a"]`.
  - `celda_decisiva`: en una celda de la zona usa `u_ntiA`/`u_etiA` del pase (con s = 5 son iguales a u2: el record
    no cambia).
  - `procesar_grilla(..., zona_a=None, s_a=None)`: los pasa a `detectar_mirova`.
  - Nuevas funciones puras `mascara_zona_a(box, pos_crater, paso_m, inner_km)` (= `(box == 2) & dist <= inner_km`,
    la misma distancia que `distance_class`) y `s_zona_a(nombre_volcan)` (lee `pipeline.profile` al llamarse; None si
    la zona está apagada o el volcán está fuera).
  - `calcular_vrp_granulo`: si `s_zona_a` no es None, arma la máscara y la pasa a `procesar_grilla`.
- Modificar `pipeline/profile.py::_zona_a_de`: sin el `ValueError` de «aún no tiene efecto»; encendida exige el bloque
  y un `valor` numérico; `volcanes_fuera` lista de nombres.
- Crear `pipeline/profiles/_s195_lab_control.yaml` y `_s195_lab_s50.yaml` ... `_s195_lab_s10.yaml` (9 brazos):
  copia de `laboratorio.yaml` (extends `mirova_equivalent`; el cargador no encadena `extends`), zona encendida con su
  valor (el control, apagada), `data_subdir` igual al nombre del perfil.
- Crear `tests/test_laboratorio_paso3_s195.py`: guards de identidad, efecto, perfiles del barrido y workflow.
- Modificar `tests/_pasada_sintetica_laboratorio.py`: opción de escena «débil» (un foco tibio en la caja sensible
  que s = 5 no alerta y s = 1 sí) además de la escena con calor.
- Modificar `tests/test_laboratorio_paso1_s193.py`: G4 (lectores de la zona = `profile.py` y
  `mirova_v750_codigo.py`; perfiles que declaran la zona = laboratorio y los 10 del barrido), G7 (encender ya no es
  error; sí lo es encender sin valor), mensaje del control de G1 (el valor del laboratorio lo fija el paso 4).
- Modificar `tests/test_guard_laboratorio_no_mas_ciego_s147.py` (G8): `s_A <= s2` también para los 9 brazos.
- Crear `.github/workflows/reproc-s195-lab-barrido.yml`: despacho manual por volcán y ventana, los 10 perfiles en
  el mismo job con `scripts/reproc_brazos.py` (bajan los gránulos una vez), artefactos y rama propia, sin push a
  main; recolector que exige identidad record a record entre `_s195_lab_s50` y `_s195_lab_control`.
- Crear `experiments/_s195_lab_paso3/`: `identidad_antes_despues.py` (la pasada sintética con el código del tag y
  con el nuevo, byte a byte, en mirova_equivalent, laboratorio, guardia K y sombra_34), `comparar_control.py`
  (usado por el recolector), `mutar.py` y sus salidas.

## Guards

| # | qué | prueba | mutación que debe atrapar |
|---|---|---|---|
| P1 | zona apagada = producción, byte a byte, 3 sensores, escena con calor | records de `mirova_equivalent`, `laboratorio` y `_s195_lab_control` iguales (G2 ya lo hace para los dos primeros) | `if s_a is not None` que actúe con la zona apagada |
| P2 | s_A = 5 encendida = producción, byte a byte, 3 sensores, escena con calor y escena débil | `_s195_lab_s50` contra `mirova_equivalent` | `u_ntiA = max(mu + s_a·sd, n1)` (piso conservador) |
| P3 | s_A < 5 cambia algo, sólo en la intersección | escena débil: `_s195_lab_s10` alerta más que producción en los tres sensores y todo alertado extra está en `mascara_zona_a` | máscara = círculo entero; máscara = caja entera |
| P4 | sólo de noche | detector puro con dayflag 1: zona y sin zona iguales | quitar el `dayflag == 0` |
| P5 | Cordón Caulle fuera | `s_zona_a("PuyehueCordonCaulle")` None con la zona encendida | quitar el chequeo de `volcanes_fuera` |
| P6 | monotonía y tope | detector puro: alertas(s) no decrecen al bajar s; `s_a = 6` es error | quitar el error de `s_a > s2` |
| P7 | perfiles del barrido difieren del laboratorio sólo en lo declarado | resueltos con `VRP_PROFILE` | un brazo con `enable_modis_b22_primary: false` |
| P8 | el workflow no pushea a main ni toca `data/mirova_equivalent` ni `laboratorio_v1`, y corre los 10 perfiles | texto del yml | `git push origin main` en el yml |

Mutaciones en copia del árbol (`D:\vrp-trabajo\temporales\s195\lab_paso3\mut\`), nunca en el worktree; una mutación
cuenta como atrapada sólo si alguna prueba falla por aserción y ninguna por excepción (S152); control sin mutar verde.

## Pasos

- [ ] Pruebas P1 a P8 y cambios de G4, G7 y G8 escritos; correr y ver rojo.
- [ ] `profile.py` y `mirova_v750_codigo.py`; perfiles del barrido; correr y ver verde.
- [ ] `identidad_antes_despues.py` contra el tag (byte a byte) y su salida.
- [ ] Workflow del barrido y su guard.
- [ ] Mutaciones en copia; tabla.
- [ ] Suite completa `pytest -q`; anotar passed, failed y skipped.
- [ ] Commit por archivo, push, PR con la fila de la ficha en la descripción; `gh pr checks <N> --watch`. No mergear.

## Hallazgo al preparar el barrido: el piso de 0,003 limita la palanca

`experiments/_s195_lab_paso3/cuanto_manda_el_piso.py` (salida `salida_cuanto_manda_el_piso.txt`) mira el primer pase
de los records nocturnos de la vía en `data/mirova_equivalent` (10 volcanes de la zona A, desde 2026-03-01): en cuántos
el término `mu + s·sd` supera al piso 0,003 de la región sensible. En NTI lo supera con s = 5 en 3.823 de 5.518 pases
MODIS, 7.674 de 10.362 VIIRS 750 y 7.464 de 10.368 VIIRS 375; con s = 1, en 16, 26 y 0. En ETI con s = 5 lo supera en
1.197, 1.107 y 2.656. Lectura (SOSPECHA, sin el barrido corrido): como la alerta exige NTI y ETI a la vez, y en ETI ya
manda el piso en la mayoría de los pases con s = 5, bajar s mueve sobre todo el umbral NTI, y por debajo de algún s
los brazos se vuelven casi idénticos (manda el piso en los dos). El barrido lo medirá; si la tasa se aplana muy arriba
del 30 %, la palanca útil sería el piso y no el multiplicador, y eso es otro pre-registro (decisión de Nicolás).

## Cómo se despacha el barrido (tras el merge)

`workflow_dispatch` de `.github/workflows/reproc-s195-lab-barrido.yml` con `barrido_aprobado: si`, por tandas:
primero la prueba de humo por defecto (Villarrica, 2026-11-10 a 2026-11-12) y mirar `identidad_s50.txt` en la rama
`s195-lab-barrido/<run_id>`; después ventanas de algunas semanas y algunos volcanes por despacho hasta cubrir
2026-03-01 al último día en los 10 volcanes de la zona A. Con 10 perfiles por job el trozo es de 5 días
(`dias_por_trozo(10)`): la ventana entera son ~54 trozos por volcán, ~540 jobs. Con las constantes de
`scripts/reproc_brazos.py` (medidas en S151 sobre K, SIN VERIFICAR para la vía) cada día de ventana cuesta ~17,6 min de
runner por volcán en la mediana (25 en el peor caso): del orden de 47.000 minutos de runner para todo, ~5,6 días
seguidos con `max-parallel: 6`. Después: `python experiments/_s194_lab_zona_a/evaluar.py calibrar --barrido
5.0=<salidas>/_s195_lab_s50 ... --barrido 1.0=<salidas>/_s195_lab_s10 --prod <salidas>/_s195_lab_control --dest <tmp>
--out c.json` sobre los trozos unidos de todas las tandas.

## Lo que queda (paso 4)

Despachar el barrido (tras el merge: `workflow_dispatch` sólo existe con el yml en main), correr
`evaluar.py calibrar` con los 9 brazos y `--prod` = el brazo de control, fijar `laboratorio_zona_a.valor` y encender
la zona en `laboratorio`, y su cron por tandas (D7).
