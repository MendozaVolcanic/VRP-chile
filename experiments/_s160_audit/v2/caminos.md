# Caminos por los que cada afirmacion de F2 podria estar mal (escrito antes de abrir archivos citados)

General (todas):
- G1. Lineas citadas de otro commit (worktree s159-pruebas en loop/activo, no d516b9d8c).
- G2. Valor leido del YAML y no de pipeline.profile (clave en otra seccion, override por volcan).
- G3. La ventana "K" del auditor no es la que dice (incluye records C0, o corta en otra fecha).
- G4. Datos del worktree y no de la instantanea D:.
- G5. Denominador distinto del que nombra el titulo (records vs cumulos vs pasadas).

201 (C1 escena bajo MIROVA):
- 201a. Conversion 3x3-con-central -> 8 vecinos mal hecha: si MIROVA resta media 3x3 que incluye el central, x - (x+8m)/9 = 8/9 (x-m); umbral 0,02 en ese espacio = 0,0225 en el nuestro. Si el .m usa otra cosa (mediana, sin central, caja 5x5) cambia.
- 201b. El .m que lee el auditor no es el de produccion (OSF dice que difiere en 10 de 13 puntos); la vara del plan es ese .m igual.
- 201c. "Umbral efectivo" = max(C1, mu+C2 sigma) bajo conectiva max (K): si mu+C2 sigma domina, C1 no importa; el % depende de sigma persistida (diag_*). Si los diag son del primer o segundo pase, cambia.
- 201d. Los 0,02/0,01 del .m pueden ser dNTI vs dETI en otra variable (NTI de MIROVA con otra normalizacion, ETI con otra regresion).
- 201e. "Bajo el de MIROVA" pero MIROVA tambien aplica mu+C2 sigma propio con sigma de otro pool: comparar solo C1 es incompleto.
- 201f. Gravedad 5 requiere que mueva lo publicado hoy; podria no cambiar el cumulo publicado (otros pixeles ya alertan).
- 201g. Para V375 y MODIS el .m de V750 no es la vara.
202: igual a 201a para 0,003 y -0,1; "muerde en 8-22 %" depende de diag persistidos.
203:
- 203a. Los cumulos con 0,0 MW pueden ser far (no publicados igual) o tener otros records de la misma pasada.
- 203b. isValidDetection puede no exigir pc.vrp_mw>0 sino otro campo (f5_core, record.vrp_mw).
- 203c. El 0 puede venir de otro camino (piso, d9, sanity) y no del recorte al fondo regional.
- 203d. "MIROVA no recorta" en el .m: puede haber un max(0,...) o un filtro VRP>0 en el .m.
- 203e. Denominador 118 vs ventana K.
204: el cambio de clase de 8 de 73 depende de que el tablero use dist_km y no final_hotspot_dist_km; el respaldo puede no ejecutarse nunca.
205: el pool del segundo pase puede reaplicar el descarte en otra funcion; el .m puede no reaplicar.
206: el anillo puede usar get_detection_anchor (crater) y no volcano_lat; caller transforma (A6).
207: orden de aplicacion: la normalizacion puede ocurrir en el processor antes de store.
208: t_bg<270 % por altitud: depende de cual t_bg (I04 / I05); "solo contextual" depende de flags efectivos.
209: el modo un pixel puede estar apagado por perfil o solo VIIRS375; MIROVA .m l.83-91 podria tomar max.
211: VRE 6 h por record: la integracion puede ser por dia (max diario) y no suma de records.
213: RECALL_MIN puede no aplicarse al flag publicado; los 66,7/77,8 pueden ser de otra ventana o tabla vs combinado.
