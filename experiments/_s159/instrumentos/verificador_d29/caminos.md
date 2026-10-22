# caminos.md: por donde podria estar mal cada afirmacion (escrito ANTES de abrir ningun archivo citado)

Verificador de D-29 (exclusion de dias en el evaluador de D25). Commit medido: 6f43ec624
(rama s159-evaluador-d25, igual a origin). Diff bajo examen: c44709e27..6f43ec624, que toca
experiments/_s157_prereg_d25/evaluar_d25.py en 30 lineas y agrega tests/test_evaluar_d25_dias_d29_s160.py.

Lo unico que se de las afirmaciones es su titulo y donde mirar. No abri el informe del auditor.

## Afirmacion 1: DIAS_EXCLUIDOS = 13, 17, 18, 19, 20 de octubre de 2026 en V1; V2 no excluye ninguno

- La constante existe pero esta escrita como string y se compara contra date, o al reves: nunca coincide (filtro inerte).
- La constante tiene las fechas pero el ano es otro (2025) o el mes es 9: inerte sobre los datos reales.
- La constante incluye el 13 pero el filtro lo aplica solo a un brazo (el que tuvo el corte parcial), no a los tres.
- "V2 no excluye ninguno" podria ser falso porque V1 y V2 comparten la funcion de carga y el filtro se aplica al cargar, no al contar: entonces V2 tambien pierde esos dias sin que nadie lo declare. O al reves: V2 deberia excluirlos tambien segun la fila D-29 y no lo hace (hay que leer la fila sellada con cuidado: dice "de V1").
- El conjunto esta duplicado (una copia en evaluar_d25.py y otra en evaluar_fk.py o en el test) y las dos copias difieren.
- El test fija el valor por igualdad de conjunto, asi que esta parte seria facil de confirmar; pero un test que pase por igualdad no prueba que el filtro se USE.

## Afirmacion 2: la exclusion llega a todos los consumidores de pasadas

Caminos por los que podria no llegar:
- El filtro se aplica a la lista de pasadas del brazo (T) pero no a la referencia de MIROVA (R): entonces una alerta protegida del 17 sigue contando como "perdida" en los tres brazos (o en P1b/P4), porque la referencia dice que hubo alerta y ningun brazo tiene pasada ese dia.
- El filtro se aplica a R pero no a T: una pasada nuestra del 17 que publica cuenta como publicacion de mas sin negativo limpio que la respalde.
- El filtro se aplica antes de P1..P5 pero DESPUES de calcular la cobertura por brazo: la cobertura compara conteos crudos y declara despareja o INDECIDIBLE justo por los dias que se querian excluir.
- Al reves: la cobertura si filtra, pero el conteo "crudo" por brazo (version, cableado) no: el veredicto declara un n distinto del que uso para decidir.
- Un segundo lector de los archivos: funciones importadas de evaluar_fk.py (o del _s151 armar_tabla.py) que vuelven a abrir los JSON de cada brazo por su cuenta y no reciben la lista filtrada. El caller transforma: pasa la ruta, no la lista.
- --repeticion y --ruido-de leen pasadas de otro sitio (un archivo de ruido o la lista de la repeticion dirigida) y no pasan por el filtro.
- La proteccion de alertas (lista de protegidas de 1 MW o mas) se construye desde la referencia sin filtrar: una protegida del 18 aparece como "perdida" o como "no decidible".
- Etiquetas por regla (SN, regla original): se calculan desde la referencia y pueden usar otra fecha (la del CSV de MIROVA, hora local de Chile) que la de la pasada.
- La fecha usada para filtrar es la del registro de la referencia y no la de la pasada (o al reves), y las dos difieren alrededor de la medianoche UTC: una pasada de las 03:00 UTC del 21 es noche del 20 en Chile; segun que fecha se use se excluye o no.
- Hora local vs UTC: si la fecha se compara en hora de Chile (UTC-3), una pasada de las 01:00 UTC del 21 cae en el 20 y se excluye de mas; si se compara en UTC pero la decision D-29 pensaba en dias de Chile, se excluye de menos. Hay que ver que convencion usan los archivos de pasadas (clave de fecha).
- Comparacion por prefijo de string ("2026-10-1" o "2026-10-2") que excluye de mas (el 10 al 19, o el 20 al 29).
- Filtro por `in` sobre una lista de strings con formato distinto ("2026-10-13" vs "20261013" vs "13-10-2026").
- Si el filtro vive en una funcion auxiliar, puede que un consumidor la llame con la lista original por un nombre de variable viejo (sombra: `pasadas` vs `pasadas_f`).
- V2: si V2 cuenta pasadas de los mismos archivos, deberia ver todas; si la carga ya filtro, V2 queda filtrado de contrabando.
- Datos sinteticos de la prueba propia: armar un brazo con pasadas el 17 y otro sin ellas, y ver si el evaluador declara cobertura despareja. Si lo declara, el filtro no llega a la cobertura.

## Afirmacion 3: primera linea del veredicto combinado y cabecera de V1 dicen "EVALUADO SIN ... (D-29)"

- El texto existe pero no es la PRIMERA linea (hay un encabezado, un titulo o una linea en blanco antes).
- El texto esta en V1 pero `combinar` arma su salida de otro modulo (o de los JSON) y no lo propaga.
- El texto se emite solo cuando hubo exclusion efectiva (si DIAS_EXCLUIDOS no corto nada, calla): entonces con datos sinteticos sin esos dias no aparece y el test pasa por otra razon. La regla sellada dice "declarados en el veredicto" sin condicion.
- El texto dice los dias pero no "(D-29)", o dice D-29 pero no enumera los dias; el test busca una subcadena y pasa por coincidencia parcial (A92: guard por subcadena).
- El texto se imprime por stdout (print) y no va al archivo del veredicto que lee Nicolas.

## Afirmacion 4: "el 13 parcial" se excluye entero en los tres brazos

- La fila D-29 dice "ni el 13 parcial": admite dos lecturas: (a) excluir el dia 13 entero; (b) excluir solo la parte del 13 que fue parcial (las horas o pasadas que CMR no sirvio). Lo que cambiaria con (b): las pasadas del 13 que si se sirvieron en los tres brazos contarian; si solo un brazo las tiene, la cobertura sigue despareja y la exclusion entera es la unica que deja los tres brazos iguales.
- Hay que leer la fila completa, no solo la frase citada, y tambien el contexto ("los dias que CMR no sirvio se excluyen de V1 en los tres brazos por igual").
- Si los tres brazos tienen distinta cobertura el 13 (uno completo, dos parciales), excluir entero es la lectura conservadora; excluir parcial exigiria saber que horas fallaron, que el evaluador no sabe.

## Afirmacion 5: pruebas 5 de 5 rojas antes y verdes despues; mutaciones 4 de 4; probar 31 de 31; suite 2.378 con arbol quieto

- "Rojas por asercion" puede ser falso si alguna fallo por ImportError o AttributeError (DIAS_EXCLUIDOS no existe antes del diff): eso es rojo por caida, no por asercion (A110, feedback S152: mutacion que cae no es atrapada). Hay que leer rojo_d29.txt y clasificar cada fallo.
- Las 4 mutaciones pueden estar "atrapadas" por caida y no por asercion; hay que leer mutaciones_d29.txt.
- Las 4 mutaciones pueden ser todas del mismo tipo (quitar un dia del conjunto) y no cubrir los caminos de la afirmacion 2 (filtrar solo T, fecha local, fecha de la referencia).
- mutar_d29.py puede mutar una copia que la prueba no importa (importa la del repo): entonces la "mutacion atrapada" es la prueba corriendo sobre el original.
- "suite 2.378 con el arbol quieto": comprobar suite_status_antes y despues (sha del arbol o git status) y que el conteo coincide; si la suite corrio en segundo plano mientras se editaba, no es linea base (A112).
- "probar 31 de 31": re-correr probar_evaluar_d25 sobre datos sinteticos y ver si da 31.
- Los tests pueden importar evaluar_d25 por ruta absoluta del repo principal (C:\Users\nmend\...) y no del worktree: entonces midieron otro arbol.

## Caminos generales

- La copia local esta atrasada: ya verifique que HEAD = origin/s159-evaluador-d25 = 6f43ec624 con arbol limpio (git status --porcelain vacio) antes de escribir esto.
- Los tests del repo se corren con cwd distinto y AQUI.parents[1] apunta a otra raiz.
- Mis propias mutaciones deben hacerse sobre una copia en experiments/<carpeta propia>/evaluar_d25.py y borrarse; si la prueba del repo importa por nombre de modulo, hay que importar mi copia explicitamente.

## Controles que me obligo a medir

- Control positivo: una mutacion que seguro rompe el filtro (vaciar DIAS_EXCLUIDOS) debe poner rojo al menos un test y cambiar la cobertura sintetica.
- Control de instrumento: mi caso sintetico debe dar cobertura DESPAREJA cuando el filtro esta vaciado y PAREJA cuando esta activo; si da lo mismo en los dos casos, el instrumento no mide el filtro.

---
sha256 (del contenido anterior a esta linea): 851796f2229923be61fb28de73ec9597e5933f671af84e1dea3c3bf11eed33f1
hora del servidor (GitHub, header Date): Thu, 22 Oct 2026 06:37:17 GMT
