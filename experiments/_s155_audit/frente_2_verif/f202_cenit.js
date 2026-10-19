// razon mostrada/MIROVA por cenit del sensor, pares de f202_pares_NevadosDeChillan.json (ventana 2026-09-18 en adelante)
const fs=require('fs');const p=require('./f202_pares_NevadosDeChillan.json');
const recs=JSON.parse(fs.readFileSync('../../../data/mirova_equivalent/NevadosDeChillan.json','utf8')).records;
const okB=(b,s)=>b==='MODIS'?s.startsWith('MODIS'):b==='VIIRS750'?s.endsWith('_750'):(s.startsWith('VIIRS')&&!s.endsWith('_750'));
const by={};console.log('pares',p.length);
for(const x of p){const r=recs.find(r=>r.datetime_utc===x[8]&&okB(x[1],r.sensor));const z=r.sensor_zenith_deg;const bin=z<25?'z<25':z<45?'25-45':'>=45';(by[x[1]+' '+bin]=by[x[1]+' '+bin]||[]).push(x[5]/x[4]);}
for(const [k,a] of Object.entries(by).sort()){a.sort((x,y)=>x-y);console.log(k,'n',a.length,'razon_med',a[a.length>>1].toFixed(3));}
