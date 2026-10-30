# Caminos por los que cada afirmación podría estar mal (escrito antes de abrir los archivos citados)

Verificador F2 (MOD-D f4), S169. Árbol: D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/ (commit 743e89c48).

## P2-01 Breaker de descarga pegado (probe_f4.py:413-442,549-550; fetch.py:950,1076)
- El breaker podría ser por corrida de proceso y el probe podría lanzar un proceso por gránulo (estado se reinicia solo).
- bajar_por_nombre podría no pasar por download_granules ni por el breaker (otro camino de descarga).
- Los 400 s podrían ser timeout de otra cosa (CMR, auth) y no del breaker; o el breaker podría devolver al instante (lo contrario de gastar 400 s).
- ~70 pasadas: número podría no salir de ninguna medición (extrapolación); la población por tanda podría ser otra.
- El probe podría registrar una fila "caída" (sin record) por gránulo, de modo que no quedan "sin fila" sino con fila de caída.
- Las líneas citadas podrían no corresponder (corrimiento entre commits).
- Arreglo en probe_f4.py: el estado del breaker podría ser variable de módulo accesible (fetch._HOSTS_CAIDOS o similar) y reseteable desde el arnés; o podría ser local dentro de una función (no reseteable sin tocar fetch.py).

## P2-02 Evaluador no ata población, identidad ni externos
- evaluar_f4.py podría leer y verificar sha256 de esos insumos en otro lugar (otra función, un import).
- El "ataje" podría hacerlo otro script del candado (manifiesto, verificar) y el pre-registro podría asignarlo a ese otro.
- La salida podría incluir procedencia por otra vía (git describe, nombre de carpeta).
- La vara: el pre-registro podría no exigir atarlos.

## P2-03 Manifiesto y procedencia no atan la lectura al commit del tag
- El manifiesto podría registrar el commit vía otra función o vía el workflow (GITHUB_SHA).
- El workflow despacha desde el tag y podría escribir el sha en la salida.
- externos_f4.py:112-118 podría sí atar al commit con git rev-parse.

## P2-04 Identidad compara clase recalculada en local; 8 indicadores no deciden
- La clase recalculada podría ser determinista desde datos atados (no depende de estado local).
- Los 8 indicadores podrían decidir por otro camino (sumados a un veredicto aguas abajo).
- El pre-registro podría declararlos informativos (no defecto, sino diseño).

## P2-05 Ensayo en seco con JSON compacto no ve P-A de CRLF
- El ensayo podría escribir con newline explícito y comparar bytes; o el sha podría calcularse sobre objeto parseado (inmune a CRLF).
- Si los sha se calculan sobre contenido canónico, CRLF no importa y no hay P-A.
- reetiquetado_f4.py:171 podría normalizar.

## P2-06 pub_runner de V, V-cercano y V-pico nunca se compara
- Podría compararse en otra función (no en l.635) o en identidad_f4.py.
- El pre-registro podría no pedir compararlo.

## P2-07 Manifiesto omite run_pipeline.py, fetch.py, volcanic_features.yaml, externos_referencia.json
- Podría incluirlos por glob (pipeline/*.py) o por directorio.
- run_pipeline.py podría no ser usado por el probe (no importa omitirlo).
- externos_referencia.json podría estar atado por otro script.

## P2-08 Dependencias sin fijar y versiones no comparadas entre tandas
- El workflow podría usar requirements con versiones fijas o lockfile.
- Las versiones podrían registrarse y compararse en evaluar_f4.

## P2-09 VRP_PROFILE y F4_RAIZ cambian la lectura sin rastro
- El probe podría fijar VRP_PROFILE explícitamente antes de importar pipeline.profile.
- Las salidas podrían registrar el perfil leído.
- run_pipeline.py podría no estar en el camino del probe.

## P2-10 «Sin record guardado en data/» se lee como «K no difiere»
- El probe podría distinguir "sin record" de "igual" con otro campo.
- La vara del pre-registro podría excluir esas filas.

## P2-11 MxD03 ilegible se lee como «volcán fuera del gránulo»
- mirova_v750_codigo.py podría lanzar excepción ante MxD03 ilegible (y no devolver fuera).
- El probe podría capturar la excepción con motivo distinto.

## P2-12 P2 con 21 bloques o más depende del flujo de numpy
- evaluar_d25 podría usar semilla fija con Generator PCG64 estable (estable entre versiones de numpy).
- Para <21 bloques podría ser enumeración exacta; ¿la población real de f4 tiene >=21 bloques?
- La versión de numpy podría registrarse.

## Generales
- La copia del árbol (743e89c48) podría no ser el commit del tag del candado; la rama podría haber avanzado.
- La vara es el pre-registro sellado (3768e9431); un hallazgo contra otra vara no cuenta.

---
sha256 del contenido anterior a esta línea: c2d0982bef50496d2d3884279c8b927c36e434e13a8ee93413585a2595782693 ; hora (reloj local del sistema, UTC, sin red permitida): 2026-10-30 04:04:16 UTC. No se vuelve a editar.
