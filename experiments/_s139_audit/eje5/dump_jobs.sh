#!/bin/bash
# Vuelca jobs (nombre, inicio, fin, conclusion) de los runs de reproceso/A-B a jobs_<id>.json
# Pregunta 1 del instrumento: si un job no corrio, aparece con conclusion != success o sin started_at.
for id in 34173711390 34208191011 33872821788 33912398561 33872836355 33412422099 33370202265 33456630043 33299555453 33299553238 33286248418 33257757759 29582035729 32965363936 29437771858 34745908237 34706563697; do
  gh api "repos/MendozaVolcanic/VRP-chile/actions/runs/$id/jobs?per_page=100" --paginate --jq '.jobs[]|{run:'"$id"',name,started_at,completed_at,conclusion,steps:[.steps[]|{name,started_at,completed_at,conclusion}]}' > jobs_$id.json
done
