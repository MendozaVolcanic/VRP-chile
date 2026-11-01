# Estrato informativo de D25: los cúmulos de cumbre de VIIRS 750 que K deja en 0,0 MW (hallazgo 203 de la auditoría S160)

Declarado el 2026-10-22 por la sesión dueña del loop, **antes** del tag de lectura y sin haber abierto V1, V2a, V2b ni
el brazo del 17 al 19 de octubre. **No decide nada**: no entra a P1, P1b, P2, M ni a la combinación de ventanas, y no
cambia ninguna regla sellada (`PREREGISTRO.md` y las adendas D-27, D-28, D-30, D-32, D-34, D-29 y D-42). Sólo agrega
una tabla al informe del evaluador.

## Por qué

La auditoría S160 (`docs/AUDIT_S160.md` §2, hallazgo 203, gravedad 5 confirmada por su verificador V2; script
`experiments/_s160_audit/v2/v_203_cero.py` en la rama `s160-auditoria`) midió que en la ventana K, 30 de 97 cúmulos de
cumbre de VIIRS 750 quedan con `pc.vrp_mw` = 0,0 MW porque el exceso sobre el anillo regional se recorta a cero: todos
sus píxeles están a la temperatura del anillo o más fríos. El tablero no publica nada con 0 MW. Contra MIROVA, 7 tenían
alerta, 11 eran negativos limpios y ninguno era protegido. D25 cambia justo ese fondo (vecinos en vez del anillo), así
que ese conjunto es donde D25 más puede mover la publicación, **en los dos sentidos**: puede recuperar alertas y puede
encender negativos. Mezclado con el resto, ese movimiento se diluye en P2; aparte, se ve.

## Qué se informa

Por ventana y por regla (original y SN), sólo VIIRS 750: las pasadas en que el cúmulo de cumbre del control K tiene
`primary_cluster.vrp_mw` igual a 0 (o ausente con `distance_class` = `summit`), y para cada una: volcán, hora, clase de
MIROVA (alerta, protegida, negativo limpio, otra) y su VRP, si publica K, si publica D, el `pc.vrp_mw` de K y de D, y de
quién es el error de P2 si lo hay. Totales: cuántas recupera D (alerta que D publica y K no), cuántas enciende D
(negativo limpio que D publica y K no) y cuántas no cambian. Se informa también en el brazo del 17 al 19 de octubre.
