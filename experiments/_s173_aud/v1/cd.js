
const fs=require('fs'); const src=fs.readFileSync(process.argv[2],'utf8');
function extraer(n){const i=src.indexOf('function '+n+'('); let j=src.indexOf('{',i), d=0; for(let k=j;k<src.length;k++){if(src[k]==='{')d++; else if(src[k]==='}'){d--; if(d===0) return src.slice(i,k+1);}}}
eval(extraer('isoDeRecord')); eval(extraer('primeraViaModis'));
const recs=JSON.parse(process.argv[3]);
console.log('169 cambio_detector primeraViaModis(K antes, via, caida, K despues)=', primeraViaModis(recs));
console.log('169 control: solo K =', primeraViaModis(recs.filter(r=>r.via_codigo_mirova===undefined)));
