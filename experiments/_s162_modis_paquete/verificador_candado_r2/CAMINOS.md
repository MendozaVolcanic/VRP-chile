# Caminos por los que la adenda 4 podria estar mal (segunda vuelta, contexto limpio)

Escrito ANTES de abrir el codigo. Hora del servidor de GitHub: Mon, 26 Oct 2026 05:52:34 GMT.
Worktree C:\vrp-trabajo\s162-modd, rama s162-modd-candado, HEAD ff2ced5319e1e40e665e3acda60ca0a4ab041cc5.
Lei solo documentos: verificador_candado/INFORME.md (primera vuelta), PREREGISTRO.md (adendas 1 a 4),
los tres _grupo_mut_N.txt y las salidas v1/v2 de mutaciones. Ningun .py ni el yml todavia.

## Punto 1: VCM-01, el denominador del §8.5 y la regla nueva (b)

1. evaluable() sigue sacando en silencio estados "error: ..." o "port" vacio (la adenda dice que eso pone el control 5 en rojo).
2. "grilla_incompleta" sigue sacando la pasada, o la saca cuando viene junto con otro estado.
3. El control 5 se pone rojo por falla del port, pero no por falla de K (estado del arnes distinto de ok) o al reves.
4. La regla (b) mira "protegida" sin exigir que K publique (mas estricta que lo aprobado), o mira "K publica" por la publicacion del runner y no por el predicado del evaluador.
5. La regla (b) se aplica tambien a bajo 1 MW, o a los brazos informativos (PM-geo5, PM-sens), o no se aplica al PM.
6. Precedencia: la fila nueva se evalua antes de las filas 2 a 4 del §6 (un P1 veto + protegida fuera deberia dar NO CANDIDATO, no DECIDE NICOLAS), o despues de la fila 6.
7. Las dos pruebas prometidas (t12 fuera del granulo, t33 escena invalida) no tienen K publicando, o pasan contra el vacio (prueba en negativo), o exigen solo "no CANDIDATO" sin exigir DECIDE NICOLAS.
8. "escena invalida" se detecta por un campo distinto al que escribe probe_portes (motivo_vacio), o la cadena no coincide.
9. La lista protegidas_fuera_del_denominador se arma con un criterio distinto al de la regla (b).

## Punto 2: que la adenda 4 no cambie otra regla sellada

10. El diff b423316c2..ff2ced531 de evaluar_paquete.py toca P1b, P2, M, Chillan o el orden del §6 ademas de lo declarado.
11. El diff de PREREGISTRO.md toca texto sellado (§2 a §8) y no solo agrega la adenda 4.
12. M con la regla de MATLAB (punto 5) entra al veredicto o cambia el d sellado; o el evaluador importa un script de otra rama que no esta en este arbol.
13. K33 con predicado del evaluador: el cambio altera la tabla de los otros brazos (por ejemplo, el orden de columnas o un campo compartido).
14. La procedencia con --commit cambia el comportamiento sin --commit de un modo que rompe el ensayo en seco guardado.

## Punto 3: el manifiesto

15. Se arma "importandolos" con sys.modules: los imports perezosos (dentro de funciones) no quedan; o quedan modulos de terceros que cambian por version.
16. No incluye evaluar_paquete.py, probe_paquete.py, grillas.json, poblacion.json, el yml, frontend/index.html, evaluar_d25_ded217af4.py, los modulos de MOD-B/S159 que reutiliza, o pipeline/*.py que K ejecuta.
17. Normalizacion LF: en este worktree los archivos estan en CRLF; si el hash no normaliza, aqui falla; si normaliza solo en un lado, el runner falla.
18. El manifiesto se comprueba en el runner contra el arbol del runner, pero el evaluador local lo comprueba contra el arbol local y no contra lo que viajo en la cabecera de los artefactos (entonces no prueba nada del runner).
19. Un cambio de un archivo cubierto NO se ve (hash calculado sobre otro path, o el chequeo compara contra si mismo).
20. El manifiesto no esta fijado por nada fuera de si mismo (se edita el archivo y el manifiesto a la vez); la unica defensa es el commit del tag, y el tag no existe.
21. --commit: compara prefijo abreviado, o acepta cualquier commit de la lista, o el workflow no escribe github.sha en la cabecera, o sin --commit no da INDECIDIBLE.
22. El workflow comprueba el manifiesto en un solo job, o lo hace sin set -e / pipefail de modo que un fallo no corta.

## Punto 4: las 31 mutaciones

23. Alguna "atrapada" lo es por excepcion (cae) y no por asercion; o la identidad no da 33 de 33.
24. Alguna mutacion no se aplica (el patron no existe en el texto y el mutador no lo detecta) y queda "atrapada" por otra razon o "viva".
25. Faltan mutaciones evidentes: (a) procedencia que ignora --commit; (b) manifiesto ignorado o comparado contra si mismo; (c) regla (b) evaluada antes del P1 veto; (d) regla (b) aplicada a bajo1; (e) regla (b) que no distingue el motivo (una falla del port tambien manda a DECIDE en vez de rojo); (f) npix sin comparar en el control 2 (dicen que entro: s159_sin_npix).
26. Las tres tandas corren en paralelo sobre copias temporales que comparten el mismo nombre de modulo o __pycache__, y una contamina a otra.

## Punto 5: ensayo en seco

27. ensayo_en_seco.py cambio a las 02:31 pero su salida guardada es de la 01:23: la salida guardada es de ANTES de la adenda 4 y puede no reproducirse.
28. El ensayo necesita --commit y la referencia de D:\vrp-trabajo\temporales\s162_mxd03\ref; si le falta, da INDECIDIBLE por procedencia y eso se lee como OK.
29. Sus exigencias (que asserts tiene) no cubren lo nuevo: procedencia con commit, manifiesto, protegidas fuera.

## Transversales

30. La bateria nueva (33) pasa contra el real pero varias de las nuevas tambien pasan contra el vacio (negativas sin mutacion pareada).
31. El job "prueba" del workflow corre la bateria dos veces (6 min cada una aqui) pero no las mutaciones; o el job no falla si la bateria falla (tee sin pipefail).
32. Disco: C 25 GB y D 9,6 GB al empezar; las copias temporales de las mutaciones estan en C.

sha256 de todo lo anterior (sin esta linea): 136c14efe4e76b99640b1a1c86530affd6798982b6951f21e05636decaa592fe
