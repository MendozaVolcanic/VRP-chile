# S157: búsqueda en CMR por ventana y brazos de un A/B en el mismo job

Rama `s157-busqueda-ventana`, tag defensivo `pre-s157-busqueda-ventana` (= `origin/main` ac015254a). Plan en
`PLAN.md`; medición previa en `MEDICION.md`.

## Qué cambia

- `pipeline/fetch.py`: con una ventana configurada, la primera búsqueda de un producto consulta CMR una vez para toda
  la ventana y la reparte por día con la regla con que CMR responde la consulta de un día (traslape con
  [D 00:00:00Z, D 23:59:59Z], bordes incluidos), conservando por día la regla standard primero, versiones en orden,
  NRT si el día viene vacío. Hoy y ayer (UTC) se siguen consultando por día, cuando el proceso llega a ellos. Donde la
  equivalencia no es segura (gránulo a menos de 2 s de una medianoche, tiempos ilegibles, 20 o más en un día, ventana
  truncada) ese día va por el camino de antes. Si la ventana falla dos veces, el resto del proceso va por día. Toda
  búsqueda o descarga que no se pudo hacer queda en la cobertura con volcán, día y plataforma.
- `scripts/run_pipeline.py`: configura la ventana con sus fechas, `--cobertura-json`, `--estricto-cobertura` (sale
  con 3), `VRP_CONSERVAR_GRANULOS`. Sin el flag estricto (el NRT) avisa con `::warning::` y sale con 0.
- `scripts/reproc_brazos.py`: brazos en serie, día por fuera, con caché de búsquedas y gránulos compartida; borra
  cada día al terminar sus brazos; `dias_por_trozo(n)` dimensiona el trozo para el paso de 170 min.
- `.github/workflows/reproc-s146-ab-sin-test1.yml`: job `plan` (`scripts/plan_trozos_ab.py`), matrix volcán por
  trozo con todos los brazos adentro, `recolectar` une con `scripts/unir_trozos_ab.py` (sin `merge-multiple`).
- `.github/workflows/reproc-chunked.yml`: `--estricto-cobertura`; un trozo con búsquedas fallidas sale rojo y no se
  sube (main conserva lo que tenía), y su cobertura se sube igual como artefacto.
- `.github/workflows/probe-s157-busqueda-ventana.yml`: validación tag contra rama (push a `s157-validar-busqueda`).

## Evidencia

| qué | script | resultado |
|---|---|---|
| identidad de gránulos contra el CMR real | `identidad_cmr.py` | 0 diferencias en 327 producto-días (Chillán 10 días de julio: 155; Láscar 12 a 19-oct: 128; Láscar 18 a 20-oct, con hoy: 44); 9 producto-días sin dato por CMR caído; 807 gránulos |
| records tag contra rama, mismo volcán y ventana | `comparar_records.py` sobre `probe_intento2/` | 74 records en los dos lados: 0 diferencias exactas, 72 sólo de redondeo (máx. relativo 9,1e-12); 36 pasadas sólo en la rama, las 36 explicadas por fallas de CMR en el log del tag |
| control del redondeo | `comparar_records.py` rama contra rama (intentos 1 y 2) | el mismo código en dos corridas da el mismo redondeo (3,4e-12): es del runner, no del cambio |
| tiempos | `resumir_probe.py` → `probe_resumen.md` | intento 2: Chillán 4 días y 2 brazos, tag 1381 s contra rama 810 s; Láscar 2 días, 703 contra 544 s. El tag perdió búsquedas por CMR caído, así que hizo menos trabajo: el ahorro medido es una cota inferior |
| pérdida silenciosa, en vivo | `probe_intento1/` | con CMR caído (HTTP 500) el código del tag terminó verde en 11 y 14 s sin ningún record; la rama dejó escrita la cobertura incompleta |
| mutaciones (A110) | `mutaciones.py` → `resultado_mutaciones.json` | control sin mutar pasa; 29 atrapadas por aserción, 0 sobreviven, 0 caídas, 2 equivalentes declaradas antes de correr (bordes `<=` contra `<`, que el margen de 2 s vuelve inobservables) |
| suite completa, árbol quieto | `python -m pytest tests` | 2311 pasan, 28 omitidas, 2 xfail (antes de los arreglos del verificador; las 53 pruebas de S157 pasan después) |

## Sin verificar

- La regla NRT (LANCE) contra el CMR real sólo se ejercitó con respuestas vacías: en las tres ventanas el standard
  ya cubría todos los días, incluido hoy.
- El costo del NRT con CMR caído (estimado 2,5 a 4,5 min extra por volcán) y su tiempo con CMR rápido no se midieron
  en el NRT real: el NRT no corrió con este código.
- El A/B reestructurado y `reproc-chunked.yml` no se corrieron de punta a punta en Actions; sus partes (plan, driver,
  unión, modo estricto) tienen pruebas y el driver corrió en el probe.
- Que correr un proceso por día y brazo dé lo mismo que uno por ventana: el probe lo compara (tag por ventana entera,
  rama por día) para 6 días de 2 volcanes, no más.
