# S157: propagación del detector K a los textos (tarea 1.37 y arreglo 5 de AUDIT_S155)

Sólo documentación. Esta carpeta guarda la única medición nueva de la tarea: si la reversión pre-autorizada de K
sigue siendo un `git revert` limpio sobre el `main` de hoy.

- `simular_revert.sh`: copia del script del frente 1 de S155. Simula `git revert 34cea39e` (squash de #850) sobre
  `HEAD` con `git merge-tree`, sin tocar el árbol (sólo escribe objetos).
  Pregunta 1 (si estuviera roto, ¿lo vería?): una reversión limpia sale con 0 y sin líneas CONFLICT; acá sale 1.
  Pregunta 2 (¿mide lo que dice?): control, el árbol resultante trae el perfil de producción con los flags de C0
  (`enable_test1_path: true`, `enable_modis_b22_primary: false`), así que la simulación sí revierte.
- `revert_hoy.out`: salida sobre `main` en `57d18ad78` (2026-10-20). Tres conflictos:
  `frontend/cambio_detector.js` y `tests/test_cambio_detector_s153.py` (modify/delete, los tocaron #851 y #860) y
  `scripts/auto_audit_weekly.py` (contenido, lo tocó #862). Comando para el control:
  `git show <primera línea de revert_hoy.out>:pipeline/profiles/mirova_equivalent.yaml | grep -n "enable_test1_path:\|enable_modis_b22_primary:"`
  da `263: enable_test1_path: true` y `567:enable_modis_b22_primary: false`.
  Salida guardada en `revert_hoy_control.out`, junto con los mismos flags en `HEAD` (K) para comparar; en el árbol
  revertido `enable_tests_23_prose_branch` no aparece, o sea vale su default `False` (C0).

Lo que esto no mide: los records reescritos con K (fecha de observación desde el 2026-09-18) no los toca ningún
revert; eso sale de los commits `data(backfill)` del 2026-10-18 (por ejemplo `5783192c1`) y de `docs/AUDIT_S155.md` §2.
