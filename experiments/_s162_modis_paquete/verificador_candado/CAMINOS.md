# Caminos por los que el candado MOD-D podria dar un veredicto equivocado sin acusarse

Escrito ANTES de abrir ningun archivo del candado (solo vi el listado de la carpeta, el prompt
y el log de git). Hora del servidor de GitHub al escribir: Mon, 26 Oct 2026 04:31:27 GMT.
Worktree C:\vrp-trabajo\s162-modd, rama s162-modd-candado, HEAD b423316c2, arbol limpio.

## A. Reglas selladas vs evaluador
A1. Una regla del §4/§5/§6/§8 del PREREGISTRO que el evaluador implementa con otro umbral, otra
    desigualdad (>= vs >), otro redondeo o en otra unidad (record vs pasada vs noche).
A2. Una regla sellada que ningun codigo implementa (queda escrita y nadie la aplica).
A3. La adenda 3 "no cambia ninguna regla sellada" pero introduce una excepcion, un estrato nuevo,
    un orden de precedencia o un recorte de poblacion que si mueve el veredicto.
A4. Las adendas 1 y 2 posteriores al sello contradicen el §2 a §8 y el evaluador toma la version
    posterior (o la anterior) sin que el documento diga cual manda.
A5. Las reglas de proteccion (alertas protegidas de MIROVA, 1 MW o mas) se implementan con la
    etiqueta equivocada: CONS solo vs CONS+OCR, o con la regla SN/SE de las minimas (0,05 MW)
    invertida o ausente.
A6. El predicado "publica" se reconstruye a mano en Python en vez de ejecutar el del tablero con
    node (A97), o se ejecuta un index.html de otro commit.
A7. El veredicto compuesto (CANDIDATO / NO / INDECIDIBLE) se arma con AND/OR distintos a los
    del pre-registro, o el orden de evaluacion hace que una condicion tape a otra.
A8. Empates y bordes: pasadas con exactamente el umbral, NaN, None, cero; la regla dice una cosa
    y el codigo las deja caer o las cuenta.

## B. Poblacion, ventana, denominador
B1. La ventana temporal del censo no es la sellada (dias de mas o de menos, limite UTC/local).
B2. "Nocturna" se define distinto en el arnes que en el pre-registro (hora local, cenit solar,
    flag del gránulo) y la poblacion de 5.465 no es la que se declara.
B3. El denominador excluye pasadas sin dato (gránulo no bajado, HDF roto, fuera de cobertura)
    y las cuenta como "callar", o las cuenta como negativos limpios.
B4. Negativos limpios: la definicion (MIROVA miro y todas sus filas son RUTINA) se implementa
    como "no hay alerta" sin exigir que MIROVA haya mirado.
B5. La referencia de MIROVA congelada en D:\...\ref no es la misma que uso el sello, o se lee
    con un loader que filtra (A119: canal CONS vs OCR, variantes de nombres A14).
B6. Pasadas duplicadas (misma pasada en dos brazos, o dos gránulos de la misma pasada) infladas
    o deduplicadas de forma distinta entre brazos.
B7. Cobertura desigual entre brazos (A108): un brazo procesa menos pasadas por timeouts y el
    evaluador compara sin exigir paridad de cobertura.
B8. Mezcla de regimenes (A104): la ventana cruza #535 o el flip de K sin estratificar.

## C. Arnes (probe_paquete.py) y brazos
C1. El brazo "K" del arnes no es produccion: flags leidos del YAML y no de pipeline.profile
    (A89), o perfil distinto a mirova_equivalent, o version del codigo de otro commit.
C2. El brazo "PM" no corre el port de S159 tal como se valido (probe_portes.py modificado,
    parametros distintos, grillas.json con otra grilla).
C3. Los dos brazos no reciben el mismo gránulo / misma geolocalizacion (MxD03 vs _interp_geo),
    asi que la comparacion mide geolocalizacion y no detector.
C4. Un flag o umbral que el arnes fija no llega a todos sus consumidores (A118): primer pase
    si, segundo pase no.
C5. El arnes atrapa excepciones y escribe "sin deteccion" (silencio) en vez de "sin dato".
C6. La salida del arnes (JSON/CSV) tiene un esquema que el evaluador lee con claves distintas
    (A89: nombre en definicion vs nombre en uso), asi que un campo cae a default.
C7. Diagnostico S-1: su "OK" no distingue "corrio" de "no corrio" (A110).

## D. Controles y pruebas
D1. Un control (positivo o negativo) que no puede fallar: su asercion es tautologica o compara
    el evaluador contra si mismo.
D2. La bateria pasa por la razon equivocada: prueba sobre datos sinteticos cuyo camino no es
    el que recorren los datos reales (claves, tipos, sensores).
D3. El evaluador vacio: si no hay datos, debe decir SIN DATO y no "CUMPLE"; si da un veredicto,
    el instrumento no distingue vacio de limpio.
D4. Mutaciones "atrapadas" por excepcion y no por asercion (S156): se cuentan como atrapadas.
D5. Mutaciones vivas de la v1 "reemplazadas" por una nueva que no cubre lo mismo.
D6. Falta una mutacion evidente: invertir la desigualdad de proteccion, cambiar el umbral de
    1 MW, ignorar el estrato SE, contar records en vez de pasadas, cambiar la ventana, ignorar
    la paridad de cobertura, intercambiar brazos K/PM.
D7. La bateria se corrio con un archivo editado a medias (A112): salida guardada no corresponde
    al codigo commiteado.
D8. Ensayo en seco sobre referencia_s159: la referencia no tiene la estructura del censo real
    (sin negativos limpios, sin estrato SE), asi que el ensayo no ejercita ramas del evaluador.

## E. Importaciones y procedencia
E1. evaluar_d25_ded217af4.py no es el blob 1dbabf65 de ded217af4 (editado localmente).
E2. Las funciones importadas de 04_analizar.py y evaluar_mxd03.py cambiaron de semantica
    respecto a cuando se validaron (otro commit en el worktree).
E3. El workflow corre otro arbol (ref distinta a b423316c2 o a la rama), o no comprueba los
    sha de los blobs antes de correr, asi que el censo puede correr sobre codigo distinto al
    verificado.
E4. El workflow no fija versiones de dependencias y el runner resuelve distinto.
E5. El workflow escribe resultados a un lugar que el evaluador no lee, o pisa salidas entre
    jobs de la matriz (race A47).
E6. Credenciales: usa el par usuario/clave vencido en vez de EARTHDATA_TOKEN (CLAUDE.md).
E7. Timeouts: 17 h de runner contra el limite de 6 h por job; si parte en chunks, el evaluador
    debe exigir que todos llegaron.

## F. Lectura del veredicto
F1. El informe final se escribe aunque falte un chunk: veredicto "limpio" sobre poblacion parcial.
F2. Las salidas *_salida.txt guardadas se citan como evidencia sin re-correr.
F3. Numeros sin denominador ni ventana (A90).

sha256 de todo lo anterior (antes de esta linea): 922fff5d7a5ce1969441f899eec2a6f1d59da95d5921f7b9f4430cc28f89ce50
