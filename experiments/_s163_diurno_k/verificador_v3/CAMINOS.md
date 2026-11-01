# Verificador v3: caminos por los que el cambio v2 -> v3 podria romper la regla

Escrito ANTES de abrir el diff, el informe del verificador v2 y el §13 del PREREGISTRO.md.
Hora del servidor (gh api -i): Mon, 26 Oct 2026 14:02:15 GMT. Commit medido: 987a760120302322b77aa333ac7712725b5d774f.

C1. Un arreglo que no llega a todos sus consumidores: se corrige una funcion (p. ej. veredicto_global, la huella, la
    clase de pasada) pero hay copias en linea de la misma logica en main() o en otra funcion (A102), o el test cubre
    solo una rama.
C2. Prueba que pasa por la razon equivocada: aserciones por subcadena (A92), datos sinteticos donde el caso no puede
    fallar, un test que arma el escenario con el mismo codigo que corrige (circular), una mutacion "atrapada" por
    excepcion y no por asercion.
C3. Umbral recalibrado mal: placebo c "8 de 40, dos colas": comprobar la cola (bilateral exacta con p=0,5 sobre 40?),
    si 8 de 40 es el limite correcto, si el sentido (>= / <=) y los empates cuadran, si 40 es el n real y no el n que
    sobrevive a un filtro; si la dos colas mide lo que el criterio pide (una cola?).
C4. Regla de VIIRS 750 en veredicto_global: puede dejar pasar un brazo que daña (no-op silencioso) o bloquear uno que
    no (un sensor sin sustrato decide); el caso "sensor sin datos" puede contar como verde.
C5. Variante "otra como negativo": reclasifica una pasada con alerta como negativo limpio, achicando o inflando el
    denominador en silencio; puede mezclar el estrato de la alerta con el de negativos; puede filtrarse la propia
    pasada del conjunto positivo.
C6. I3 solo con records nocturnos: filtrar por noche cambia el denominador de I3; si el filtro usa un campo que el
    diurno tambien llena, o si el filtro excluye la cobertura que el diurno debia aportar, I3 no puede fallar.
C7. Huella nocturna: la lista de campos volatiles y el prefijo diag_ fuera pueden dejar fuera un campo que SI cambia
    el resultado nocturno (la huella se vuelve ciega), o dejar dentro uno volatil (falsa alarma permanente).
C8. Refactor de main() en evaluar_completo / p_sup_de_vara / pasadas_de: cambios de comportamiento no declarados
    (orden, argumentos por defecto, semilla del placebo, ventanas, filtros), o que main() ya no llame lo mismo; salida
    impresa distinta; valores por defecto distintos del §.
C9. Sello objetivos_sha256.txt: omite un archivo que el evaluador lee al correr (imports, open(), json.load, rutas
    de scripts/evaluador_comun.py, ADENDA_K.md, perfiles YAML, la referencia congelada); o sella con rutas/line-endings
    que no reproducen (CRLF vs LF en Windows); o el sha de un archivo no coincide con el contenido actual.
C10. Mutaciones: mutaciones.json declara mutaciones nuevas pero la salida no las corre, o las cuenta atrapadas por
    caida; control de caida ausente.
C11. El §13 afirma V-N1..V-N9 corregidos pero el texto de §4 a §7 sigue con el valor anterior (inconsistencia
    interna, A113: la correccion no se propago).
C12. Un cambio de la v3 contradice la regla de la adenda sellada de S151 (se pierde una proteccion).
sha256 de CAMINOS.md: b4a57eeb91d5944c683dab7734055f8f7fc361bdd7ee9365b351a3674021bcce (calculado 14:02:33 UTC)
