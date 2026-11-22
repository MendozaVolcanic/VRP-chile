# Perfil `laboratorio`, paso 1 (S193): plan de implementación

> **Para agentes:** se ejecuta en línea con `executing-plans` y `test-driven-development`. Pasos con casillas.

**Objetivo:** crear el perfil `laboratorio` (D2 (a): hereda de `mirova_equivalent`, la vía «código MIROVA» en los
tres sensores) que escribe en `data/laboratorio_v1/` (D3), con la extensión MEJ-5 (zona A) declarada en la
configuración y APAGADA, más los guards 1 a 4 del §4 de `docs/PLAN_EXPERIMENTAL_S190.md`.

**Base:** `origin/main` en `358e0ed81`, tag defensivo `pre-s193-laboratorio-paso1` (A45; autorización de Nicolás
del 2026-11-21 en la coordinadora S193: «continua con todo lo que recomiendes», tras la recomendación «sí A45 al paso 1»).

**Fuera de alcance (pasos siguientes del plan S190 §7):** el umbral de la zona A (paso 3), su efecto en el detector
(paso 3 o 4), el cron y el reproceso (paso 4), sellar el criterio §6 (paso 2). El perfil `experimental` (sombra C0)
no se toca (D1 (a)).

## El fenómeno y la decisión de diseño

Un foco chico en el cráter calienta su píxel lo justo para quedar al borde del umbral de MIROVA. La vía copia ese
umbral a propósito. El laboratorio existe para bajarlo **sólo** dentro de la zona A (el círculo de
`inner_radius_km` alrededor del cráter, donde el prior volcánico es alto) y medir lo que aparece contra NHI y
persistencia, nunca contra MIROVA (A115).

**Qué umbral de la vía se modularía (leído en `pipeline/mirova_v750_codigo.py`, `detectar_mirova` y
`_pasada_contextual`).** El detector del `.m` alerta una celda por contexto si su contraste NTI y su contraste ETI
superan `max(mu + s·sd, piso)`, con `mu` y `sd` de toda la grilla y `(s, piso)` por región de la caja: conservadora
`s1 = 10`, pisos 0,02 / 0,01; sensible `s2 = 5`, pisos 0,003 / 0,003 (de noche). Ya hay, por tanto, una región
«sensible» en el cráter; la zona A sería una tercera región con su propio multiplicador `s_A` (pisos de la región
sensible). Es un solo número y es monótono en «ver más» (menor `s_A`, más alertas), así que el guard S147 lo puede
vigilar: `s_A <= s2`. MIR sólo nocturno: el parámetro es nocturno. El valor lo elige el paso 3 (barrido sobre
negativos limpios, S147 §6); hoy es `null`.

**Por qué el flag encendido falla en vez de no hacer nada.** Si alguien enciende `enable_lab_zona_a` antes del paso 3,
el laboratorio correría idéntico a producción creyendo que mide la extensión: un nulo silencioso (A87, S156). Por eso
`pipeline/profile.py` levanta un error al importar un perfil con la zona encendida mientras la vía no la implemente.

## Archivos

- Crear `pipeline/profiles/laboratorio.yaml`: `extends: mirova_equivalent`, `data_subdir: laboratorio_v1`,
  `thresholds.enable_lab_zona_a: false`, bloque `laboratorio_zona_a` (radio, parámetro, valor `null`, volcanes fuera).
  Cabecera FICHA y POR QUÉ.
- Modificar `pipeline/profile.py`: función pura `_zona_a_de(t, cfg)` que valida y devuelve
  `(ENABLE_LAB_ZONA_A, LAB_ZONA_A)`; error si la zona está encendida. Comentario POR QUÉ.
- Crear `tests/test_laboratorio_paso1_s193.py`: guards.
- Crear `tests/_pasada_sintetica_laboratorio.py`: script que corre en subproceso los tres `calculate_vrp` sobre un
  gránulo sintético de Villarrica e imprime los records (no es test: pytest sólo recoge `test_*.py`).
- Modificar `tests/test_guard_laboratorio_no_mas_ciego_s147.py`: `laboratorio` en `LABORATORIOS` y comparación
  `s_A <= s2`.
- Modificar `tests/test_profile_data_isolation_s124.py`: `("laboratorio", "laboratorio_v1")`.
- Modificar los `VIVOS` de `tests/test_guard_v750_codigo_mirova_encendido_s177.py`,
  `tests/test_guard_v375_codigo_mirova_encendido_s177.py` y `tests/test_guard_modis_codigo_mirova_encendido_s172.py`:
  `"laboratorio": True`.
- Modificar `tests/test_guard_pyproj_vias_s172.py` (hallado al correr la suite): contaba como «corre el perfil» toda
  mención fuera de comentarios, y la palabra «laboratorio» está en el nombre visible de `experimental-diario.yml`
  («Experimental diario (laboratorio congelado, 11 Tier A)») y en la lista `workflows:` de `vigilancia-sombra.yml`.
  Las líneas `name:` y `workflows:` dejan de contar (un nombre no corre nada), con un control nuevo en las dos
  direcciones. Comprobado que en todos los workflows y perfiles el filtro nuevo sólo deja de ver esas dos menciones.

## Guards (cada uno rojo antes, y una mutación atrapada por aserción)

| # | guard | prueba | mutación que debe atrapar |
|---|---|---|---|
| G1 | difiere de producción sólo en lo declarado (§4.1) | constantes de `pipeline.profile` resueltas con `VRP_PROFILE` en subproceso; diferencia = `{PROFILE_NAME, DATA_SUBDIR, LAB_ZONA_A}` | `enable_modis_b22_primary: false` en el laboratorio |
| G2 | con el flag apagado el record es el de producción para la misma pasada | `_pasada_sintetica_laboratorio.py` bajo los dos perfiles; control: los tres records son de la vía y con VRP > 0 | `enable_v375_codigo_mirova: false` en el laboratorio |
| G3 | no escribe en `data/mirova_equivalent` | `pipeline.store.DATA_DIR` resuelto termina en `data/laboratorio_v1` | `data_subdir: mirova_equivalent` |
| G4 | producción no cambia | `mirova_equivalent` resuelve la zona apagada y vacía; ningún perfil salvo `laboratorio` declara la zona; nadie en `pipeline/` lee `LAB_ZONA_A`/`ENABLE_LAB_ZONA_A` fuera de `profile.py` (frontera de palabra, A92) | bloque `laboratorio_zona_a` en `mirova_equivalent.yaml`; una lectura de `ENABLE_LAB_ZONA_A` en `process_viirs.py` |
| G5 | el tablero operacional no lee el laboratorio (§4.2) | `frontend/index.html`, `diario.html`, `mosaico.html` sin `laboratorio_v1`; control: nombran `mirova_equivalent` | `laboratorio_v1` en `index.html` |
| G6 | el commit del NRT no lo agrega y ningún workflow lo corre (§4.3 y requisito 4) | cada `git add` de `nrt.yml` apunta a `mirova_equivalent`, `experimental` o `mirova`; ningún `.github/workflows/*.yml` nombra `laboratorio_v1` ni el perfil `laboratorio` | `git add data/laboratorio_v1/...` en `nrt.yml` |
| G7 | zona encendida = error, no nulo silencioso | `_zona_a_de({"enable_lab_zona_a": True}, ...)` levanta `ValueError` | quitar el `raise` |
| G8 | S147 extendido (§4.4) | pisos del laboratorio `<=` producción; `s_A` nulo hoy y `<= s2` cuando exista, con `s2` leído de `detectar_mirova` | `valor: 6` |

Mutaciones en una copia del árbol (`D:\vrp-trabajo`), nunca en el worktree; una mutación cuenta como atrapada sólo si
la prueba cae por aserción, no por excepción (S152).

## Pasos

- [ ] Pruebas G1 a G8 escritas; correr y ver rojo (perfil inexistente, función inexistente).
- [ ] `laboratorio.yaml` y `_zona_a_de` en `profile.py`; correr y ver verde.
- [ ] Mutaciones en copia; tabla con el resultado de cada una.
- [ ] `tests/test_guard_laboratorio_no_mas_ciego_s147.py`, `tests/test_experimental_congelado_s150.py` y suite
      completa `pytest -q` verdes.
- [ ] Commit (`git add` por archivo), push, PR con la fila de ficha en la descripción (sin escribir la ficha).
