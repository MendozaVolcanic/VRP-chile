# -*- coding: utf-8 -*-
"""S131 - Fix mecanico del pendiente #4 de AUDIT_S128: inyeccion de comandos en workflows.

POR QUE. `${{ github.event.inputs.X }}` interpolado DENTRO de un bloque `run:` se
sustituye textualmente antes de que bash lo vea: un input con `; rm -rf` o con
backticks se ejecuta con los secrets del job. El patron seguro ya existe en el repo
(`reproc-s129-ab-fondos.yml`, `reproc-s130-d18-roi1.yml`): pasar el input por `env:`
del step y leerlo en el shell como "$VAR" - bash lo trata como dato, nunca como codigo.

Cada reemplazo es exacto y se exige que ocurra N veces; si no, el script aborta sin
tocar nada. Los `matrix.*` no se tocan: vienen del propio yml, no del usuario.
"""
import io
import os
import sys

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
W = os.path.join(ROOT, ".github", "workflows")

ENV_SE = ("          VRP_START: ${{ github.event.inputs.start }}\n"
          "          VRP_END: ${{ github.event.inputs.end }}\n")

NRT_ARGS_OLD = (
    "            ${{ github.event.inputs.date != '' && format('--date {0}', github.event.inputs.date) || '' }} \\\n"
    "            ${{ github.event.inputs.start != '' && format('--start {0}', github.event.inputs.start) || '' }} \\\n"
    "            ${{ github.event.inputs.end != '' && format('--end {0}', github.event.inputs.end) || '' }} \\\n"
    "            ${{ github.event.inputs.overwrite == 'true' && '--overwrite' || '' }} 2>&1 | tee -a pipeline.log\n")
NRT_ARGS_NEW = '            "${ARGS[@]}" 2>&1 | tee -a pipeline.log\n'
NRT_PRE = (
    "          set -o pipefail\n"
    "          # S131: los inputs del dispatch entran por env (no interpolados en el shell)\n"
    "          ARGS=()\n"
    "          if [ -n \"$VRP_DATE\" ]; then ARGS+=(--date \"$VRP_DATE\"); fi\n"
    "          if [ -n \"$VRP_START\" ]; then ARGS+=(--start \"$VRP_START\"); fi\n"
    "          if [ -n \"$VRP_END\" ]; then ARGS+=(--end \"$VRP_END\"); fi\n"
    "          if [ \"$VRP_OVERWRITE\" = \"true\" ]; then ARGS+=(--overwrite); fi\n")
NRT_ENV = (
    "          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n"
    "          VRP_DATE: ${{ github.event.inputs.date }}\n"
    + ENV_SE +
    "          VRP_OVERWRITE: ${{ github.event.inputs.overwrite }}\n")
COMMIT_HDR = ("      - name: Commit result\n        run: |\n          set +e\n"
              "          git config user.name  \"vrp-bot\"\n"
              "          git config user.email \"vrp-bot@github-actions\"\n")

FIXES = {
 "nrt.yml": [
  ("      - name: Filter volcano match\n        id: filter\n        run: |\n"
   "          if [ \"${{ github.event.inputs.volcano }}\" != \"\" ] && [ \"${{ github.event.inputs.volcano }}\" != \"${{ matrix.volcano }}\" ]; then\n"
   "            echo \"skip=true\" >> $GITHUB_OUTPUT\n"
   "            echo \"Skipping ${{ matrix.volcano }} (dispatch filter=${{ github.event.inputs.volcano }})\"\n",
   "      - name: Filter volcano match\n        id: filter\n"
   "        env:\n          DISPATCH_VOLCANO: ${{ github.event.inputs.volcano }}\n"
   "        run: |\n"
   "          if [ \"$DISPATCH_VOLCANO\" != \"\" ] && [ \"$DISPATCH_VOLCANO\" != \"${{ matrix.volcano }}\" ]; then\n"
   "            echo \"skip=true\" >> $GITHUB_OUTPUT\n"
   "            echo \"Skipping ${{ matrix.volcano }} (dispatch filter=$DISPATCH_VOLCANO)\"\n", 1),
  ("          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n        timeout-minutes: 50\n",
   NRT_ENV + "        timeout-minutes: 50\n", 2),
  ("          set -o pipefail\n          python scripts/run_pipeline.py --profile mirova_equivalent \\\n",
   NRT_PRE + "          python scripts/run_pipeline.py --profile mirova_equivalent \\\n", 1),
  ("          set -o pipefail\n          python scripts/run_pipeline.py --profile experimental \\\n",
   NRT_PRE + "          python scripts/run_pipeline.py --profile experimental \\\n", 1),
  (NRT_ARGS_OLD, NRT_ARGS_NEW, 2),
 ],
 "backfill-geometry.yml": [
  ("          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n        timeout-minutes: 330\n",
   "          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n" + ENV_SE + "        timeout-minutes: 330\n", 1),
  ("            --start ${{ github.event.inputs.start }} \\\n            --end ${{ github.event.inputs.end }}\n",
   "            --start \"$VRP_START\" \\\n            --end \"$VRP_END\"\n", 1),
  ("      - name: Commit result (solo el archivo de este volcan — anti-race A47)\n        run: |\n",
   "      - name: Commit result (solo el archivo de este volcan — anti-race A47)\n        env:\n" + ENV_SE + "        run: |\n", 1),
  ("${{ matrix.volcano }} ${{ github.event.inputs.start }}..${{ github.event.inputs.end }} (S122)",
   "${{ matrix.volcano }} $VRP_START..$VRP_END (S122)", 1),
 ],
 "backfill-tier-a.yml": [
  ("          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n        timeout-minutes: 330\n",
   "          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n" + ENV_SE +
   "          VRP_OVERWRITE: ${{ github.event.inputs.overwrite }}\n        timeout-minutes: 330\n", 1),
  ("          if [ \"${{ github.event.inputs.overwrite }}\" = \"true\" ]; then\n",
   "          if [ \"$VRP_OVERWRITE\" = \"true\" ]; then\n", 1),
  ("            --start ${{ github.event.inputs.start }} \\\n            --end ${{ github.event.inputs.end }} \\\n            $OVERWRITE_FLAG\n",
   "            --start \"$VRP_START\" \\\n            --end \"$VRP_END\" \\\n            $OVERWRITE_FLAG\n", 1),
  ("      - name: Commit result (solo el archivo de este volcán — anti-race S22)\n        run: |\n",
   "      - name: Commit result (solo el archivo de este volcán — anti-race S22)\n        env:\n" + ENV_SE + "        run: |\n", 1),
  ("${{ matrix.volcano }} ${{ github.event.inputs.start }}..${{ github.event.inputs.end }} (S120)",
   "${{ matrix.volcano }} $VRP_START..$VRP_END (S120)", 1),
 ],
 "reproc-chunked.yml": [
  ("          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n        timeout-minutes: 170\n",
   "          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n"
   "          VRP_PROFILE_IN: ${{ github.event.inputs.profile }}\n        timeout-minutes: 170\n", 1),
  ("            --profile ${{ github.event.inputs.profile }} \\\n            --volcano ${{ matrix.job.vol }} \\\n",
   "            --profile \"$VRP_PROFILE_IN\" \\\n            --volcano ${{ matrix.job.vol }} \\\n", 1),
  ("$PROFILE ${{ github.event.inputs.start }}..${{ github.event.inputs.end }} (${{ github.event.inputs.volcanoes }})",
   "$PROFILE $VRP_START..$VRP_END ($VRP_VOLCANOES)", 1),
 ],
 "reproc-s120-eq16-villarrica.yml": [
  ("          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n        timeout-minutes: 330\n",
   "          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n"
   "          VRP_VOLCANO: ${{ github.event.inputs.volcano }}\n" + ENV_SE + "        timeout-minutes: 330\n", 1),
  ("            --volcano \"${{ github.event.inputs.volcano }}\" \\\n            --start ${{ github.event.inputs.start }} \\\n            --end ${{ github.event.inputs.end }} \\\n",
   "            --volcano \"$VRP_VOLCANO\" \\\n            --start \"$VRP_START\" \\\n            --end \"$VRP_END\" \\\n", 1),
  (COMMIT_HDR + "          git add \"data/_s99_test1_eq16/${{ github.event.inputs.volcano }}.json\"\n",
   "      - name: Commit result\n        env:\n          VRP_VOLCANO: ${{ github.event.inputs.volcano }}\n" + ENV_SE
   + "        run: |\n          set +e\n          git config user.name  \"vrp-bot\"\n"
   "          git config user.email \"vrp-bot@github-actions\"\n"
   "          git add \"data/_s99_test1_eq16/$VRP_VOLCANO.json\"\n", 1),
  ("reproc Eq.16 ${{ github.event.inputs.volcano }} ${{ github.event.inputs.start }}..${{ github.event.inputs.end }} (Panel 2b)",
   "reproc Eq.16 $VRP_VOLCANO $VRP_START..$VRP_END (Panel 2b)", 1),
 ],
 "reproc-s124-ndc-focus.yml": [
  ("          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n        timeout-minutes: 330\n",
   "          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}\n" + ENV_SE + "        timeout-minutes: 330\n", 1),
  ("            --start ${{ github.event.inputs.start }} \\\n            --end ${{ github.event.inputs.end }} \\\n            --overwrite\n",
   "            --start \"$VRP_START\" \\\n            --end \"$VRP_END\" \\\n            --overwrite\n", 1),
  (COMMIT_HDR + "          git add \"data/experimental_ndc_focus/NevadosDeChillan.json\"\n",
   "      - name: Commit result\n        env:\n" + ENV_SE
   + "        run: |\n          set +e\n          git config user.name  \"vrp-bot\"\n"
   "          git config user.email \"vrp-bot@github-actions\"\n"
   "          git add \"data/experimental_ndc_focus/NevadosDeChillan.json\"\n", 1),
  ("foco Nicanor NdC ${{ github.event.inputs.start }}..${{ github.event.inputs.end }} (experimental_ndc_focus)",
   "foco Nicanor NdC $VRP_START..$VRP_END (experimental_ndc_focus)", 1),
 ],
 "reproc-s124-villarrica-op-ab.yml": [
  ("      - name: Partir la ventana en trozos\n        id: split\n        run: |\n"
   "          CHUNKS=$(python scripts/split_date_window.py \\\n"
   "            --start \"${{ github.event.inputs.start }}\" \\\n"
   "            --end \"${{ github.event.inputs.end }}\" \\\n"
   "            --max-days \"${{ github.event.inputs.max_days }}\")\n",
   "      - name: Partir la ventana en trozos\n        id: split\n        env:\n" + ENV_SE
   + "          VRP_MAX_DAYS: ${{ github.event.inputs.max_days }}\n        run: |\n"
   "          CHUNKS=$(python scripts/split_date_window.py \\\n"
   "            --start \"$VRP_START\" \\\n"
   "            --end \"$VRP_END\" \\\n"
   "            --max-days \"$VRP_MAX_DAYS\")\n", 1),
  ("A/B Villarrica operacional ${{ github.event.inputs.start }}..${{ github.event.inputs.end }} (issue 513)",
   "A/B Villarrica operacional $VRP_START..$VRP_END (issue 513)", 1),
 ],
}


def main():
    cambios = 0
    for f, reps in FIXES.items():
        p = os.path.join(W, f)
        s = open(p, encoding="utf-8").read()
        for old, new, n in reps:
            c = s.count(old)
            if c != n:
                print(f"ABORT {f}: esperaba {n} ocurrencia(s), hay {c} de:\n{old[:160]!r}")
                return 1
            s = s.replace(old, new)
            cambios += n
        yaml.safe_load(s)   # sigue siendo YAML valido
        open(p, "w", encoding="utf-8", newline="\n").write(s)
        print(f"ok {f}: {len(reps)} reemplazos")
    print(f"total reemplazos: {cambios}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
