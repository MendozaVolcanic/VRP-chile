# caminos.md: por donde cada afirmacion podria estar mal (escrito ANTES de abrir archivos citados)

Comunes a todas: (a) el archivo del arbol no es el que se usara el 2026-11-03 (otra rama, otro tag); (b) la linea citada no dice lo que se afirma (A101, deriva); (c) el defecto lo cubre otro mecanismo (otro script, un procedimiento escrito en R4, una adenda); (d) la vara es otra (el pre-registro sellado no promete lo que se dice); (e) el arreglo ya existe en main o en la rama ROI.

P1-01 worktree atrasado / tablero de ese worktree:
- el analizador puede leer el tablero desde una ruta configurable o desde main via git show, no del worktree;
- el pre-registro puede fijar que el tablero es el del commit sellado (entonces no es defecto, es diseno);
- R4 puede ordenar correr desde main; el tablero de main y de la rama pueden ser identicos en el predicado (diff vacio = sin efecto);
- puede existir un hash del tablero comprobado contra un valor sellado.

P1-02 --leer-con-faltantes abre la compuerta con censo FALLADO:
- la linea 414 puede distinguir "no corrio" de "fallo" y el auditor lo leyo mal;
- el pre-registro 212-214 puede permitir justamente eso (entonces no hay texto contra codigo);
- la bandera puede requerir ademas un argumento que exige el resultado del censo;
- el caller (R4 / procedimiento) puede no pasar nunca la bandera.

P1-03 VRP_PROFILE del shell cambia la poblacion:
- banco_paridad puede no leer pipeline.profile, o el generador puede fijar el perfil antes de importar;
- auto_audit_weekly puede no ser llamado por el generador;
- el perfil _s154 puede no cambiar nada de lo que usa el generador; el import de diurno puede ser independiente del perfil;
- R4 puede fijarlo en otro paso.

P1-04 --data viejo/incompleto sin aviso:
- el generador puede comprobar fecha maxima en otra funcion; puede fallar ruidosamente si falta un volcan;
- R4 puede tener paso de comprobacion.

P1-05 veredicto sin identidad de insumos, reelegible, se pisa:
- el analizador puede imprimir sha de insumos en otra linea; puede negarse a escribir si existe la salida;
- el pre-registro 211 puede no exigir identidad;
- leer_n3 puede escribir con nombre fechado.

P1-06 corte N-3 por fecha vs hora del arreglo OCR:
- la regla puede usar >= con datetime y no fecha; la adenda puede declarar el corte por fecha a sabiendas;
- la hora 14:01 UTC puede no estar respaldada; pasadas de Suomi NPP del 2026-10-09 antes de 14:01 pueden no existir (efecto nulo).

P1-07 tramos #535 y K prometidos, solo cenit:
- el pre-registro puede decir "si aplica" o la ventana puede no cruzar #535 (entonces no aplica); otro script puede informarlo.

P1-08 con y sin FALSO_POSITIVO:
- clase_mirova puede informarlo y el analizador llamarlo; el pre-registro puede no prometerlo en esa forma.

P1-09 sha crudo vs CRLF:
- la copia puede venir por git show (LF) y el sha sellado ser sobre LF: entonces solo falla con checkout autocrlf;
- el analizador puede normalizar antes en otra funcion.

P1-10 protegida fuera de granulo sale de P1 sin frenar:
- el probe puede registrar esos casos en un contador que el analizador revisa; el pre-registro puede decir que se excluyen.

P1-11 V750-A local leido de texto sin atar:
- evaluar_v750a puede verificar sha del texto o el commit en otra parte.

P1-12 medidor de mutaciones nunca completo:
- puede haber salida de corrida completa en otra carpeta; el conteo 77/M1-M85 puede ser otro.
- No puedo correrlo (prohibido): medir por lectura de salidas existentes.

P1-13 prueba ROI no cubre main(), mutaciones no atrapadas:
- otra prueba puede invocar main via subprocess; las mutaciones del auditor pueden caer (contar caida como atrapada, P-D).

P1-14 dos generadores bajan referencia viva por separado:
- pueden usar una referencia en cache/compartida o un sha fijado; el control puede comparar.

---
sha256 del contenido anterior a esta linea: 5de49aa2f2923c3d56beb5114530a38a928cdb6a195cd4b04255763c53e612be ; hora (reloj del sistema, sin red): 2026-10-30T04:07:59Z
