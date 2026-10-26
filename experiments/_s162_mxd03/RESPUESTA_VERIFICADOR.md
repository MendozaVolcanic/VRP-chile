# Respuesta al verificador del arnés y el evaluador de MxD03 sobre K (2026-10-24)

Verificador con contexto limpio: Fable 5.1, esfuerzo alto (`verificador/INFORME.md`, caminos sellados con sha256
`d2cbfe92…` a las 15:49:57 GMT antes de abrir nada). Veredicto: **LISTO CON CAMBIOS CHICOS**. Ninguno de sus hallazgos
hace que el A/B dé CUMPLE SIN DAÑO cuando X daña. Se arreglaron los nueve antes de pedir el despacho:

| hallazgo | grav. | qué se hizo | dónde | comprobado con |
|---|---|---|---|---|
| VMX-01 el humo no ejercita el control 1 | 3 | el gránulo `MYD021KM.A2026073.0705` (Láscar, control S151) entra al humo, que pasa de 3 a 4 gránulos | `.github/workflows/probe-s162-mxd03.yml`, job `plan` | lectura del yml; `yaml.safe_load` da las mismas claves |
| VMX-02 el evaluador no deduplica | 3 | control `duplicados`: una pasada (volcán, hora) repetida da INDECIDIBLE | `evaluar_mxd03.py`, `control_duplicados` | prueba 20 |
| VMX-03 la suite no fija el camino real | 2 | diez pruebas nuevas (13 a 22): ruido = segundo mayor, saldo con bajo 1 MW, `vara_desde_estado`, veredicto sin vara y con control externo rojo, P1b, módulo de R, cableado, geometría, duplicados, re-etiquetado, partidas | `probar_evaluar_mxd03.py` | 22 de 22; 0 de 22 contra el vacío; las 11 mutaciones propias del verificador quedan atrapadas (`verificador/verif_mutaciones_propias_evaluador.py`: 11 de 11) |
| VMX-04 el control de unión era tautológico, sin re-etiquetado | 2 | con `--ref`, el evaluador regenera la población desde la referencia congelada (`poblacion_mxd03.py --sin-bajar --salida`) y la compara con la del arnés (control `reetiquetado`); sin `--ref` el veredicto queda INDECIDIBLE | `evaluar_mxd03.py`, `poblacion_mxd03.py` | prueba 21; sobre la población real: 0 distintas e idéntica byte a byte (`control_reetiquetado_salida.txt`) |
| VMX-05 a: una bajo 1 MW partida salía de P2 | 1 | sólo un negativo limpio partido con hermana sin_info es invisible; una alerta partida sí entra a P2 | `_invisible` | prueba 22 |
| VMX-05 b: P6 listaba sólo las partidas invisibles | 1 | P6 lista todo cambio en las 222 mitades partidas, en sin_info y en far_ref, con la marca de si también entra a P2 | `p6` | prueba 22 |
| VMX-05 c: no se comparaba el signo de P2 sin Cordón Caulle | 1 | la salida lo marca con «ATENCION (§6)» si difiere | `main` | lectura |
| VMX-05 d: sin sha256 del predicado | 1 | la cabecera del job guarda el sha256 de `frontend/index.html` y el evaluador lo exige igual al local (control `predicado`) | `probe_mxd03_ab.py`, `evaluar_mxd03.py` | punta a punta (sin cabecera real da INDECIDIBLE) |
| VMX-06 módulo homónimo | 1 | `vara_mxd03.py` agrega las carpetas de 1.17 a 1.23 al final de `sys.path`; la prueba del arnés deja su carpeta primero | `vara_mxd03.py`, `probar_probe_mxd03_ab.py` | `import vara_mxd03, evaluar_mxd03` toma el de esta carpeta |
| VMX-07 vara sin control de sesgo | 1 | «INTERP MAS CERCA SIN CONTROL DE SESGO» pasa a «DETIENE SIN CONTROL DE SESGO» y el veredicto va a Nicolás | `vara_desde_estado`, `veredicto` | pruebas 15 y 16 |
| VMX-08 fetch por sha sin probar | 2 | el job prueba `git fetch --depth 1` del sha mayoritario y `git worktree add` antes del arnés, y se cae al instante si falla | workflow, paso «Código del job = main congelado» | se ejercita en el humo |
| VMX-09 el job no comprobaba su código | 1 | el mismo paso exige `git diff --quiet <main congelado> HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent` | workflow | se ejercita en el humo |

Re-corridas finales (salidas al lado): `probar_probe_mxd03_ab_salida.txt` (caso base OK, 4 de 4),
`probar_evaluar_mxd03_salida.txt` (22 de 22, 5 de 5), `probar_evaluar_mxd03_contra_vacio_salida.txt` (0 de 22),
`probar_punta_a_punta_salida.txt` (OK), `control_reetiquetado_salida.txt`.

Lo que el verificador dejó como CONFIRMADO EN PARTE y queda así, declarado:
- **A3**: el control 4 no tiene prueba en un runner real; el humo lo ejercita (Láscar 03-27 y Chillán 10-10 son del sha
  mayoritario) y ahora el fetch por sha se prueba al arrancar cada job.
  ⚠️ **Corregido tras el resultado (VRB-05)**: el humo NO ejercitó la re-corrida en sha, ni lo hicieron las tandas (no
  hubo ningún record que decide con K distinto de `data/`); sí se probó en el runner el fetch por sha y el worktree.
- **A5**: el bucle de selección de la vara es una copia adaptada de `construir_vara_viirs.main`, no un import (A102);
  misma lógica por lectura y la vara se reproduce byte a byte. Se deja así porque la de 1.23 lee la población de la 1.17.
- **Dependencias**: el yml no instala `pyproj` ni `pandas`; el verificador midió con bloqueo que el arnés no los necesita.

## Ronda 2 (mismo verificador, 2026-10-24): «se puede despachar el humo»

Informe: `verificador/ronda2/INFORME_RONDA2.md`. Los nueve, ARREGLADOS salvo VMX-06 y VMX-08 en parte. Lo nuevo:
- **VMX-10** (VMX-06 en parte): `probar_probe_mxd03_ab.py` vuelve a poner su carpeta primera en `sys.path` después de
  importar el arnés. Arreglado aquí.
- **VMX-11, regla de operación**: una parte que se repite **reemplaza** su artefacto en la carpeta de evaluación, no
  se suma (si no, el control de duplicados da INDECIDIBLE, como debe).
- **VMX-12, regla de operación**: el evaluador se corre desde un checkout del tag (el `merge-base` con `origin/main`
  tiene que seguir siendo el main congelado para que el re-etiquetado regenere la misma población).
- **VMX-08 en parte**: el `git fetch --depth 1` por sha sólo lo prueba el runner; el humo lo decide antes del arnés.
