#!/bin/bash
# Para cada run, baja el log de UN job de reproceso y extrae la primera y ultima fecha procesada
# (lineas ">>> Volcan | YYYY-MM-DD") y el conteo de dias. Si el job no proceso nada, sale vacio (SIN DATO).
for f in jobs_*.json; do
  id=${f#jobs_}; id=${id%.json}
  jid=$(gh api "repos/MendozaVolcanic/VRP-chile/actions/runs/$id/jobs?per_page=100" --jq '[.jobs[]|select(.conclusion=="success")][0].id')
  [ -z "$jid" ] || [ "$jid" = "null" ] && { echo "$id SIN_JOB_OK"; continue; }
  gh api "repos/MendozaVolcanic/VRP-chile/actions/jobs/$jid/logs" > log_$id.txt 2>/dev/null
  n=$(grep -c ">>> " log_$id.txt)
  first=$(grep -o ">>> .*| [0-9-]*" log_$id.txt | head -1)
  last=$(grep -o ">>> .*| [0-9-]*" log_$id.txt | tail -1)
  ndays=$(grep -o ">>> .*| [0-9-]*" log_$id.txt | sort -u | wc -l)
  echo -e "$id\tjob=$jid\tlineas=$n\tdias_unicos=$ndays\t$first\t$last"
done
