# F49 — "Scraper MIROVA caído" — falso positivo: el roto es el sync VRP-Chile ← Mirova-v1

**Sesión**: S77
**Fecha**: 2026-05-24
**Severidad**: ALTA (bloqueante para validación contra MIROVA NRT)
**Tipo**: bug de proceso (no de código), data freshness
**Estado**: diagnóstico — fix NO ejecutado

---

## Diagnóstico ejecutivo

El reporte inicial fue: *"el scraper Mirova-v1 se cayó, última fecha en CSV es
2026-05-01, hoy 2026-05-24 = 23 días sin data, blocker para validar VRP Chile"*.

**Eso es falso.** El scraper Mirova-v1 está **vivo y corriendo cada 5 min en GitHub
Actions** (workflow `Monitor Volcanico VRP` + `Scraper OCR` + `Generador de
Graficos`). Verificado en `gh run list -R MendozaVolcanic/Mirova-v1` — todas las
corridas de las últimas horas terminan en `success`. El último commit auto
`Sincronización de datos e imágenes` es `b37cdcf0` de **2026-05-24 21:35 UTC**
(hace minutos cuando se escribió este doc).

El CSV remoto
`https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv`
contiene data hasta `2026-05-24 18:24:02` UTC (verificado vía `curl`). Es decir,
Mirova-v1 funciona perfecto.

**Lo que sí está roto** es el sync VRP-Chile ← Mirova-v1. El archivo
`VRP-Chile-s70/latest_consolidado.csv` quedó congelado con data hasta
2026-05-01 18:12 UTC. `git log -- latest_consolidado.csv` muestra **un solo
commit** (`65a18769`, PR #139 S73 al crearlo). Nunca se actualizó después.

Por lo tanto el dashboard de VRP Chile lleva 23 días mostrando una curva
MIROVA NRT obsoleta, aunque la fuente upstream está fresca.

## Causa raíz probable (top 3)

1. **PROBABLE — sync manual nunca documentado ni automatizado** (90%).
   El comentario en `.github/workflows/pages-deploy.yml:62-69` (S73) dice:
   > "cuando llegue un nuevo consolidado solo hay que regenerar
   > latest_consolidado.csv apuntando al archivo nuevo".
   No hay workflow GH Actions, ni cron local, ni script
   (`scripts/sync_mirova_csv.py` no existe) que haga ese paso. La copia
   inicial S73 (PR #139) se hizo a mano y nadie repitió la operación desde
   entonces. **Es un gap arquitectural, no un bug de código.**

2. **Posible — A17 mal entendido** (8%). A17 en CLAUDE.md dice
   *"`latest_consolidado.csv` hard copy"* — quizá la intención original era
   que apuntara siempre al snapshot fechado más reciente, pero la operación
   sigue siendo manual: alguien tiene que `cp NN_MM_YYYY_registro_*.csv
   latest_consolidado.csv` + commit.

3. **Improbable — bug en el scraper Mirova-v1** (<2%).
   Refutado: workflows verdes, commits cada 5 min, CSV remoto fresco hoy.

## Plan de fix recomendado (NO ejecutado)

**Paso 1 — fix inmediato (Nicolás o claude, 5 min)**

```bash
cd VRP-Chile-s70
curl -sL "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv" \
  -o latest_consolidado.csv
git add latest_consolidado.csv
git commit -m "data(mirova): sync latest_consolidado.csv from Mirova-v1 (S77 F49)"
git push
```

Esto descongela el dashboard y restaura la validación MIROVA NRT.

**Paso 2 — automatización (claude, ~30 min)**

Agregar workflow `.github/workflows/sync-mirova-csv.yml`:

- Cron cada 1 h (Mirova-v1 commitea cada 5 min; 1 h es buen trade-off
  ruido-de-commits vs. freshness, MIROVA NRT mismo tiene ~3 h de latencia).
- `curl` del CSV remoto.
- Diff vs. el committeado. Si cambió, commit + push.
- Trigger `pages-deploy.yml` automáticamente vía `workflow_run`.

ETA: 30 min implementación + 1 h observación primera corrida. Quien:
**claude** (es código de infra, no decisión científica).

**Paso 3 — sanity check periódico (claude, 10 min)**

Test `tests/test_mirova_csv_freshness.py` que falle el CI si la fecha máxima
de `latest_consolidado.csv` es >48 h vieja respecto a `datetime.now(UTC)`.
Si el sync se vuelve a romper, el CI lo detecta antes que un humano abriendo
el dashboard.

## Workaround corto plazo (mientras no esté el paso 1)

**Inmediato — banner en dashboard**: agregar al `diario.html` un banner
amarillo *"MIROVA NRT data stale — last sync 2026-05-01. Sistema sigue
operacional pero la curva de referencia MIROVA puede estar desactualizada"*.
Mostrar dinámicamente cuando el delta entre `max(Fecha_Satelite_UTC)` del CSV
y `Date.now()` >48 h. Mantenerlo aún después del fix por si recurre.

**Alternativo — ground truth secundario**: para auditorías formales
(papers, F47/F48), usar **OSF v2.5** (`data/mirova_reference/`) como
ground truth histórico. No es NRT pero es algorítmicamente equivalente y
está completo hasta 2025. Para días recientes donde OSF aún no llegó,
asumir gap y no reportar métricas hasta sync restaurado.

## Evidencia recolectada

| Item | Valor |
|---|---|
| Repo Mirova-v1 local | `C:/Users/nmend/OneDrive/Escritorio/claude/Automatizacion web/Automatizacion web/Mirova-v1` |
| Repo Mirova-v1 remoto | `MendozaVolcanic/Mirova-v1` |
| Último commit local | `131245012a` 2026-03-28 (local atrasado, no relevante) |
| Último commit remoto auto-sync | `b37cdcf0` 2026-05-24 21:35 UTC |
| Workflows activos | `main.yml`, `ocr_workflow.yml`, `graficos_completo.yml`, `validar_funcionalidades.yml` |
| `gh run list` últimas 10 | TODAS success, cron cada 5 min |
| CSV remoto max fecha | 2026-05-24 18:24:02 UTC |
| CSV en VRP-Chile-s70 max fecha | 2026-05-01 18:12:01 UTC |
| Delta freshness | **23 días, 6 horas** |
| Mecanismo sync esperado | Manual `cp` (comentario `pages-deploy.yml:62-69`) |
| Workflows en VRP-Chile que actualicen CSV | **0** |
| Commits a `latest_consolidado.csv` en VRP-Chile | **1** (creación S73 PR #139) |

## Por qué no se notó antes

A17 en CLAUDE.md (S73) documenta la convención pero asume disciplina humana
("update CSV → cp + commit"). El dashboard no expone freshness, por lo que
visualmente la curva MIROVA NRT sigue dibujándose con la data vieja sin
alarma. F47/F48 (audits Llaima/Copahue/NdC en S76) usaron probablemente OSF
o JSONs propios, no este CSV, por lo que no detectaron el stale.

## Aprendizajes meta candidatos (no aplicar todavía)

- **A46 (propuesto)**: cualquier archivo data committeado que dependa de un
  source externo requiere (a) workflow auto-sync, o (b) test de freshness en
  CI, o (c) banner visible en el dashboard. Las 3 son aceptables; ninguna no
  lo es. La disciplina humana (A17 "cp + commit") es no-replicable y se
  pierde en handoffs de sesión.
- **A47 (propuesto)**: antes de declarar *"X está caído"*, verificar el
  source upstream (no el sink local). Aquí 5 min de `gh run list` ahorraron
  horas de diagnóstico equivocado en el scraper.

## Referencias

- A17 (CSV path convention): `CLAUDE.md` S73
- PR #139: creación inicial de `latest_consolidado.csv`
- `.github/workflows/pages-deploy.yml:62-72` — comentario S73 sobre sync manual
- Skill triggers: este F49 cumple `superpowers-systematic-debugging` (hipótesis
  → evidencia → root cause, 4 fases) y `verification-before-completion`
  (no se ejecutó fix, solo se documentó).
