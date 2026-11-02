# Caminos por los que cada afirmacion de esta auditoria podria estar mal (VS34)

Nota de procedimiento: este archivo se escribio DESPUES de una primera pasada de lectura del diff (grillas, perfil,
workflows, vigilancia, tests y la via mirova_v750_codigo.py), porque la tarea es una auditoria con medicion propia y no
la verificacion ciega de hallazgos de otro; no recibi hallazgos ajenos. Lo que aprenda despues va al informe, no aqui.

1. V-1 grillas. (a) La comparacion "11 intactas" mide solo un prefijo de bytes: si el archivo nuevo reordenara claves
   duplicadas, yaml.safe_load se quedaria con la ultima sin avisar. (b) Los 34 pueden "seguir la regla de las 11" solo en
   X0,Y0 pero no en centro_lat/lon ni en la zona UTM cerca de la frontera de zona (-72 grados). (c) La regla de 8 de los
   11 solo fue medida contra el yaml de HOY; si volcanoes.yaml cambia de coordenadas la grilla queda vieja sin aviso.
2. V-2 produccion y sombra de los 11. (a) Un consumidor de grillas_mirova.yaml que decide por "tiene grilla" (no solo por
   nombre) y que yo no encuentre por grep (nombre distinto: _referencias, grilla_del_volcan, volcan_por_coordenadas). (b)
   volcan_por_coordenadas con tolerancia 1e-6 podria devolver otro nombre si dos volcanes comparten coordenadas. (c) El
   lector sellado compara un conjunto de rutas; yo lo ejecute con sus funciones extraidas por ast, no el lector entero.
3. V-3 perfil/workflow/vigilancia. (a) La vigilancia lee records con `regimen.perfil`; si el productor real no escribe
   esa clave, la vigilancia seria ciega siempre (los tests fabrican el record). (b) Un cron que GitHub retrasa horas. (c)
   El workflow que vigila puede quedar ciego sin que nadie lo vigile.
4. V-4 vecinos. (a) Mi gránulo sintetico no tiene el ruido ni la interpolacion de uno real: el foco del vecino podria
   diluirse y no alertar. (b) Los umbrales dependen de mu y sd de TODA la grilla, que en un gránulo real incluyen el
   calor del vecino. (c) Que MIROVA excluya vecinos en Chile es SIN DATO. (d) Los datos K de los 11 miden el cráter con
   otra geometria que la grilla interpolada.
5. V-5 pruebas. (a) Una prueba parametrizada por 34 puede pasar por la misma razon en todos. (b) "Rojo visto" es una
   declaracion del autor; la re-mido con mutaciones propias en una copia.
6. Todo. La copia local del repo esta atrasada respecto a origin/main (medi contra 14fb62030 = base de la rama).
