// V1 170: los filtros de artefacto del tablero (isCirrusArtifact, isDiffuseFieldArtifact) sobre un record de la via
// (pc.vrp_mw = suma de TODOS los alertados de la escena, pc.n_pixels = solo el cumulo mayor, mirova_v750_codigo.py:734-742)
// frente a su equivalente K (pc.vrp_mw = suma del cumulo). Direccion del efecto, no magnitud real: records sinteticos.
const fs = require('fs'); const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(n){const i=src.indexOf('function '+n+'('); if(i<0) throw new Error(n); let j=src.indexOf('{',i), d=0; for(let k=j;k<src.length;k++){if(src[k]==='{')d++; else if(src[k]==='}'){d--; if(d===0) return src.slice(i,k+1);}}}
for (const n of ['mirovaEqVrp','isCirrusArtifact','isDiffuseFieldArtifact']) eval(extraer(n));
function r(vrp, npx, tmax){ return {t_max_k: tmax, distance_class: "summit", primary_cluster: {vrp_mw: vrp, n_pixels: npx, centroid_dist_km: 0.5}}; }
// escena: cumulo mayor 120 px, 60 MW; mas 300 px tibios lejanos que suman 240 MW (la via los suma, K no)
const K_cumulo   = r(60, 120, 276.0);     // K: pc = cumulo
const VIA_union  = r(300, 120, 276.0);    // via: pc.vrp_mw = union (300), n_pixels = cumulo (120)
console.log('170 difuso  K(60MW/120px,t_max 276K) =', isDiffuseFieldArtifact(K_cumulo), '| via(300MW union/120px) =', isDiffuseFieldArtifact(VIA_union));
const K_frio   = r(8, 3, 270.0);  const VIA_frio = r(12, 3, 270.0);
console.log('170 cirrus  K(8MW,t_max 270K) =', isCirrusArtifact(K_frio), '| via(12MW union, mismo cumulo) =', isCirrusArtifact(VIA_frio));
console.log('170 control: via con t_max 300K difuso=', isDiffuseFieldArtifact(r(300,120,300)), 'cirrus=', isCirrusArtifact(r(12,3,300)));
