# caminos.md: caminos por los que cada afirmacion podria estar mal (escrito antes de abrir INFORME.md y antes de leer el codigo del delta)

## L1 una sola lectura por ventana + registro commiteado
- C1.1 El chequeo "existe lectura_sombra_corte_*" usa glob en la --dir-salida; otra carpeta vacia lo esquiva (es lo que el registro commiteado debe cerrar). Ver si el registro cubre ese caso: si el registro no se compara contra nada al releer, no cierra nada por codigo.
- C1.2 El glob puede ser relativo al cwd y no a la carpeta (cambia con cwd).
- C1.3 El rc 2 se emite antes de escribir, pero el orden puede permitir escritura parcial (archivo creado y luego falla).
- C1.4 El registro guarda N, sha256 de referencia y records, hora; puede omitir el sha de los records de la sombra (si cambia el set de la sombra, otro N).
- C1.5 Nombre del archivo con patron distinto (p.ej. lectura_sombra_corte_ vs lectura_sombra_cortes_) que el glob no ve; o archivos .tmp/.json.
- C1.6 Un symlink/carpeta vacia con otro --dir-salida es camino legitimo: el codigo no puede cerrarlo solo; si el codigo dice que lo cierra, es sobreafirmacion.
- C1.7 Hora del registro tomada del reloj local (manipulable) y no de los datos.
## L2 atrapada solo si sale 1
- C2.1 seccion() captura excepciones y las convierte en fallo (sale 1) en vez de 2: una mutacion que rompe el import o lanza se contaria ATRAPADA.
- C2.2 correr() de mutar_sombra.py mapea rc: 1->ATRAPADA, 2->CAIDA, otro rc (p.ej. 3, timeout, rc negativo) a que? Un timeout o un rc inesperado puede caer en ATRAPADA.
- C2.3 CONTROL_SECCION: un control que lanza excepcion en una seccion debe dar CAIDA; si el control no puede fallar (A110) o su nulo no se midio.
- C2.4 SystemExit con codigo 1 lanzado por una excepcion no capturada del lector (sys.exit(1) en la mutacion) contaria como atrapada.
- C2.5 assert con python -O se omite.
## L3 S8 AST, perfiles, base por codigo_sha
- C3.1 AST sin docstrings: el strip de docstrings tambien puede quitar un string-expresion que es codigo (Expr(Constant str) en medio de un cuerpo) o cambios de comentarios no se ven (correcto). Cambio de x0 numerico en .py cambia el AST: debe marcar.
- C3.2 roi_v750 y roi_modis excluidos de grillas_mirova.yaml: un cambio ahi no marca (declarado). Pero excluir por clave puede excluir mas (claves anidadas con mismo nombre) o la comparacion puede ser sobre texto en vez de parseado.
- C3.3 Solo dos perfiles: un tercer perfil que la via use por herencia (extends) no se compara.
- C3.4 codigo_sha en records: record sin codigo_sha -> como se cuenta? Si se ignora silenciosamente, la coherencia pasa. Si la base sale de la primera noche y la primera noche tiene records sin sha, base vacia.
- C3.5 "todas las noches coinciden con la base": ordenar por noche vs por fecha de proceso; la primera noche puede no ser la mas antigua.
- C3.6 Hueco declarado: cambio entre c42ee0eb7 y la base; el lector informa sin marcar. Verificar que no calla.
- C3.7 sha del codigo_sha del record es hash de que? Si hashea el arbol del repo y el lector compara contra el calculado localmente con otro algoritmo (CRLF vs LF), siempre marca o nunca marca.
- C3.8 volcanoes.yaml, run_pipeline.py y workflow: comparados por bytes (sensibles a CRLF) vs AST.
## L4 merge origin/main y S0
- C4.1 Los sha de S0 pueden corresponder a bytes CRLF del checkout de Windows (autocrlf) y no a LF del arbol.
- C4.2 Merge dcec35a8c puede haber cambiado otro archivo de la via ademas de auto_audit_weekly.py (el S0 listaria solo uno).
- C4.3 c42ee0eb7 puede no ser ancestro real.
## L5 perfil forzado, S0 suma store/profile/f5_core, S9 fila mas nueva, contadores antes de parada
- C5.1 Forzar perfil: si VRP_PROFILE ajeno esta puesto y se fuerza igualmente, el lector lee un perfil que no es el que corrio la sombra.
- C5.2 S9 "fila mas nueva" por orden de lista y no por fecha; o un record sin fecha.
- C5.3 Los contadores se imprimen antes de la parada pero si un control cae (excepcion) la parada se salta los contadores (try/finally ausente).
## L6 bateria, nulo
- C6.1 "227 de 227" puede incluir tests que se saltan (skip) sin git; con git presente.. verificar que realmente son 227 y que no hay secciones vacias.
- C6.2 138 mutaciones + identidad + 2 controles de caida = 141; comprobar_unicas() podria ser trivialmente vacio (por no evaluar nada).
- C6.3 V04 marcada equivalente: si no es realmente equivalente, el nulo la reporta como no atrapada o se oculta una brecha.
- C6.4 Mutaciones "unicas": dos mutaciones con el mismo texto resultante; o mutacion que no cambia el archivo (no-op) contada como atrapada.

---
sha256 (sin esta linea): 10e2504f339241cc47e9de8d283d96d3cdf21f4e8e6a693fc117aeb922fc1ba2
hora: Fri Oct 30 07:04:32 UTC 2026
