import io, json, subprocess, yaml, sys
sys.stdout.reconfigure(encoding="utf-8")
s = yaml.safe_load(io.open('.github/workflows/reproc-watchdog.yml', encoding='utf-8'))['jobs']['vigilar']['steps'][0]['with']['script']
b = s[s.index("// --- SELECCION PURA"):s.index("// --- FIN SELECCION PURA ---")]
h = r"""
const T = Date.parse('2026-10-20T12:00:00Z');
const out = {};
// 1) run waiting por aprobacion de environment, 20 h
out.waiting = evaluarCorrida({status:'waiting',created_at:'2026-10-19T16:00:00Z'},
  [{name:'j',status:'waiting',started_at:'2026-10-19T16:00:00Z'}], T, 7, 14);
// 2) run huerfano: in_progress 30 h con todos los jobs completados
out.huerfano = evaluarCorrida({status:'in_progress',created_at:'2026-10-19T06:00:00Z'},
  [{name:'j',status:'completed',conclusion:'success',started_at:'2026-10-19T06:00:05Z'}], T, 7, 14);
// 3) re-run hoy de un run creado hace 20 dias, job colgado 9 h
out.rerun_viejo = evaluarCorrida({status:'in_progress',created_at:'2026-09-30T00:00:00Z',
  run_started_at:'2026-10-20T02:00:00Z', run_attempt:2},
  [{name:'j',status:'in_progress',started_at:'2026-10-20T03:00:00Z'}], T, 7, 14);
// 4) jobs en cola 20 h (runner que nunca llega)
out.cola_eterna = evaluarCorrida({status:'queued',created_at:'2026-10-19T16:00:00Z'},
  [{name:'j',status:'queued',started_at:'2026-10-19T16:00:00Z'}], T, 7, 14);
// 5) job con started_at null pero in_progress
out.sin_started = evaluarCorrida({status:'in_progress',created_at:'2026-10-19T16:00:00Z'},
  [{name:'j',status:'in_progress',started_at:null}], T, 7, 14);
// 6) jobs = undefined (paginate devolviendo objeto)
out.objeto = evaluarCorrida({status:'in_progress',created_at:'2026-10-20T10:00:00Z'},
  {total_count: 1, jobs: []}, T, 7, 14);
// 7) dedup: issue.body null y sin comentarios
out.body_null = debeComentar('x\n'+MARCA, {body:null}, []);
// 8) comentario humano que cita la marca (copia el aviso) despues del ultimo del watchdog
out.humano_cita = debeComentar('aviso nuevo\n'+MARCA, {body:'b'}, [{body:'aviso nuevo\n'+MARCA},{body:'> citando\n> aviso viejo\n'+MARCA}]);
console.log(JSON.stringify(out));
"""
r = subprocess.run(['node','-e',b+'\n'+h],capture_output=True,text=True,encoding='utf-8')
print(r.stderr); print(json.dumps(json.loads(r.stdout), indent=1, ensure_ascii=False))
