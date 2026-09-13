# Borrador de correo a Diego Coppola (S139)

> **Nota para Nicolás.** Borrador en inglés para que lo revises y lo envíes tú desde tu cuenta. No se
> ha enviado nada. Las preguntas salen de `docs/audit_s139/EJE_6_recursos_no_usados_y_mision.md` (H606),
> cada una con la divergencia del catálogo que cerraría (tabla al final, sólo para uso interno: no va en
> el correo). Revisa en particular: tu cargo exacto, si quieres mencionar el repositorio público, y si
> prefieres enviarlo en dos tandas (preguntas 1 a 5 primero, que son las que bloquean el A/B).

---

**Subject:** Questions on the MIROVA detection algorithm (SP426.5) from SERNAGEOMIN, Chile

Dear Dr. Coppola,

My name is Nicolás Mendoza, a geologist at the Chilean Volcano Observatory (OVDAS, SERNAGEOMIN). MIROVA
is an essential reference in our daily monitoring of Chilean volcanoes, and we are grateful for the
openness with which your group has published the method and the VRP archive.

To support our operators with an in-house near real time product, we are implementing the algorithm
described in Coppola et al. (2016, Geol. Soc. London Spec. Publ. 426) for MODIS, VIIRS 375 m and VIIRS
750 m over eleven Chilean volcanoes, and we compare our results night by night against the values
MIROVA publishes. The agreement is good for detection, but a few steps of the method admit more than one
reading, and our magnitudes are systematically lower than MIROVA's. Before investing in large
reprocessing runs, we would be very grateful if you could clarify the following points:

1. In Tests 2 and 3, is the threshold applied as min(C1, mu + C2 sigma) or as max(C1, mu + C2 sigma)?
   The equation and the text of SP426.5 seem to read differently to us.
2. For MODIS, is band 22 still used as the primary MIR band, with band 21 only where band 22 saturates?
3. Do Tests 2 and 3 include any condition on the pixel brightness temperature (for example BT greater
   than the background plus a few kelvin), or only the dNTI and dETI conditions?
4. For the VRP (equation 6), is the background radiance the mean of the pixels surrounding each alerted
   pixel (8 neighbours), or a larger ring? And is a negative excess set to zero?
5. Are pixels with NTI above K1 declared as alerted on their own, without passing Tests 2 and 3? And are
   saturated pixels kept in the radiance sum?
6. Are VIIRS 375 m and 750 m images also resampled to a constant area grid, as described for MODIS? If
   so, how is the grid centred on each volcano, and how is the bow tie effect handled?
7. Is ROI1 still a fixed 5 by 5 km box for every volcano, or are volcano specific radii used?
8. Is the quadratic regression of the background NTI fitted iteratively with outlier rejection (for
   example at 3 sigma)?
9. What does the "class" column of the published VRP archive (OSF v2.5) mean, and is the published
   archive complete or filtered (for example by distance or intensity)?
10. We noticed that Tupungatito does not appear in the archive, and that there are relatively few VIIRS
    750 m entries for Chilean volcanoes. Is there a reason for this?
11. Is the choice between a global and a local background applied uniformly to all volcanoes?

We would of course be happy to share our comparisons with MIROVA if they are of any use to your group.

Thank you very much for your time and for MIROVA.

Kind regards,

Nicolás Mendoza
Geologist, Observatorio Volcanológico de los Andes del Sur (OVDAS)
Servicio Nacional de Geología y Minería (SERNAGEOMIN), Chile

---

## Uso interno: qué cierra cada pregunta (no enviar)

| # | cierra |
|---|---|
| 1 | conectiva de los Tests 2 y 3 (S136), D26 |
| 2 | D21 |
| 3 | D22 |
| 4 | D25 |
| 5 | D23, D24, GAP #A |
| 6 | D17, D28 |
| 7 | D18 |
| 8 | D29 |
| 9 | supuestos del cruce OSF (eje 6), D3 |
| 10 | H603, H604 del eje 6 |
| 11 | `lbg_global_compatible` (MISSION, nota S125) |
