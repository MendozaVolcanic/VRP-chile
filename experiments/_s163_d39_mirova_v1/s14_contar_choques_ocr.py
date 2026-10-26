"""S163 D-39: cuenta, en las lineas del paso de push de las corridas exitosas de ocr_workflow.yml (s14_ocr_push_lineas.txt,
bajadas con `gh run view <id> --log`), cuantos rebases tuvieron que mezclar un archivo. Si el instrumento estuviera muerto
(no leyera los registros) daria 0 corridas con lineas; control: cuenta tambien los 'Successfully rebased'."""
import collections, re, sys
sys.stdout.reconfigure(encoding='utf-8')
ids = [l.strip() for l in open('ocr_ids_lf.txt') if l.strip()]
lin = [l.rstrip('\n') for l in open('s14_ocr_push_lineas.txt', encoding='utf-8')]
por = collections.defaultdict(list)
for l in lin: por[l.split(' ', 1)[0]].append(l)
print('corridas exitosas', len(ids), '; con lineas del paso de push', len(por))
pat = {k: re.compile(v, re.I) for k, v in {'rebase ok': 'Successfully rebased', 'push primer intento': 'Push exitoso en intento 1$',
       'push en reintento': 'Push exitoso en intento [2-9]', 'CONFLICT': 'CONFLICT', 'Auto-merging': 'Auto-merging',
       'binario': 'Cannot merge binary', 'could not apply': 'could not apply'}.items()}
for k, p in pat.items(): print(f'  {k}: {sum(1 for l in lin if p.search(l))}')
