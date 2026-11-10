# PR A del encendido de los dos VIIRS (S176): plan de implementación

> Diseño: `docs/superpowers/specs/2026-11-08-encendido-v375e-design.md` (decisiones 1 a 8). Rama `claude/s176-guardia-viirs`.
> Tag defensivo `pre-s176-adopcion-viirs`. Se ejecuta en esta misma sesión, tarea a tarea, cada prueba en rojo antes de su código.

**Meta.** Dejar en main, con las vías de VIIRS apagadas en producción, todo lo que el encendido necesita: guardia K de los dos VIIRS, su vigilancia, el
audit por detector, la marca del tablero y la regla de reversión en borrador. Ningún record publicado cambia.

**Arquitectura.** Se calca lo de MODIS. Las funciones de la vigilancia de MODIS reciben el sensor como argumento con el valor de hoy por defecto (MODIS no
cambia); los dos VIIRS las llaman desde un script propio, con su issue propio, porque se revierten por separado (B1 y B2).

## Archivos

| Archivo | Qué es |
|---|---|
| `pipeline/profiles/guardia_k_viirs.yaml` | Perfil de la guardia (nuevo) |
| `.github/workflows/guardia-k-viirs.yml`, `scripts/revisar_guardia_viirs.py` | Workflow de la guardia y revisión de su corrida (nuevos) |
| `.github/workflows/pages-deploy.yml` | La carpeta de la guardia no dispara el sitio ni se publica |
| `scripts/vigilancia_guardia_modis.py` | Argumento `sensor` con default MODIS, sin cambio de conducta |
| `scripts/vigilancia_guardia_viirs.py`, `.github/workflows/vigilancia-guardia-viirs.yml` | Vigilancia diaria (nuevos) |
| `experiments/_s176_v375e_adopcion/sombra_pasadas_juzgadas_viirs.json` | Pasadas ya juzgadas (nace vacío) |
| `scripts/vigilancia_sombra.py` | La vigilancia de K deja fuera los records de la vía de cualquier sensor |
| `scripts/auto_audit_weekly.py` | `VIA_V375` y `VIA_V750`, sin recalibrar bandas |
| `frontend/cambio_detector.js` | Marca desde los datos para cada VIIRS, en un solo lugar |
| `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md` | Regla en borrador para el sello |
| `experiments/_s176_v375e_adopcion/medir_cirrus_viirs.py`, `cotas_retrospectiva.py`, `control_lectores.py` | Mediciones y controles, con su salida |

## Tareas (TDD: rojo, verde, commit)

1. **Perfil.** `tests/test_guardia_k_viirs_s176.py`: resuelve K en los dos VIIRS, sólo VIIRS, carpeta propia; difiere de producción sólo en lo permitido.
2. **Workflow y revisión.** Mismo archivo de pruebas: aserción desde `pipeline.profile`, sólo token (A71), grupo propio, commit sólo de su carpeta,
   revisión después del commit, hora libre; `revisar` rojo sin escribir, con marca de la vía, con otro perfil, con un día sin ninguno de los dos VIIRS.
   `tests/test_pages_sin_sombras_s173.py` ya exige la exclusión en Pages.
3. **Vigilancia.** `tests/test_vigilancia_guardia_viirs_s176.py`: el sensor argumento no cambia MODIS (pruebas existentes en verde); escenas sintéticas para
   V375 y V750: protegida que la guardia publica y la vía calla dispara; una de otro sensor no; caída a K investiga; guardia sin datos da ciega; nulo.
4. **Vigilancia de K.** `tests/test_vigilancia_sombra_via_viirs_s176.py`: records de la vía de VIIRS fuera de K y frescura de K no exigida en ese sensor.
5. **Audit.** `tests/test_auto_audit_via_viirs_s176.py`: `detector_de_record`, `detector_de_noche`, `fronteras_via`, por detector, sin juzgar, salida idéntica
   sin records de VIIRS.
6. **Tablero.** `tests/test_cambio_detector_via_viirs_s176.py` (node): fecha por sensor, aviso propio, línea sólo en su serie, MODIS intacto.
7. **Mediciones.** Cirrus sobre la sombra, cotas sobre la retrospectiva.
8. **Regla** en borrador, con PENDIENTE DE NICOLÁS donde no haya fuente citable.
9. **Controles.** Lector V375-E y V750-A con control positivo; producción sin cambios; mutaciones de cada prueba nueva (A110).
10. **PR en borrador**, CI verde de verdad.

## Comandos

Pruebas locales: `python -m pytest tests/test_guardia_k_viirs_s176.py -q` y análogos. La suite completa, en el CI.
