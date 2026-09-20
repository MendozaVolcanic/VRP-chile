# Borrador de correo a Diego Coppola (S139, ajustado S142 y S146)

> **Ajuste S146.** Se agrega una sola pregunta, la 13 (la antigua 13 pasa a ser 14): si el NRT
> aplica algún test integrado sobre el ROI o algún test de temperatura de brillo, además de los
> Tests 1 a 3 de SP426.5. Sale de la auditoría S146 (V-06 y V-08), que abrió D30 y D31 en el
> catálogo. Sigue sin enviarse nada: el correo lo mandas tú desde tu cuenta.

> **Ajuste S142.** Nicolás decidió "ajustar y enviar". Cambios respecto de S139: la pregunta 4 se
> acota a lo que las lecturas de S141 no contestan (recorte a cero y tamaño de la vecindad,
> `docs/audit_s139/LECTURA_PDF_SEGUNDA_PASADA.md` l. 50); la 6 se acota igual (método exacto del bow tie
> y caja o disco, l. 51); la 8 se reemplaza, porque el artículo de Scientific Data 2026 ya contesta qué es
> `class` y que el archivo está filtrado (p. 7, p. 8 Tabla 1, p. 10 a 12), por la pregunta de si el
> **NRT publicado** aplica esos umbrales (decide el piso VRP, decisión 3 de S142); se agrega la 13 sobre
> el cambio de formato de los GeoTIFF del 2026-09-14. La conectiva sigue siendo la 1. El correo lo envías
> tú desde tu cuenta; yo no envío nada.
>
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
4. For the VRP (equation 6), we understand from your papers that the background radiance of each
   alerted pixel is the mean of its non-alerted neighbours. Is the neighbourhood exactly the 8
   adjacent pixels, and is a negative excess set to zero before summing?
5. Are pixels with NTI above K1 declared as alerted on their own, without passing Tests 2 and 3? And are
   saturated pixels kept in the radiance sum?
6. We understand that bow tie duplicates are removed in the original granule before resampling to the
   51 by 51 km UTM grid. Which method is used to identify them, and is the summit ROI a 5 by 5 km box
   or a disc of fixed radius?
7. Is the quadratic regression of the background NTI fitted iteratively with outlier rejection (for
   example at 3 sigma)?
8. Your 2026 Scientific Data paper describes sensor-specific minimum VRP thresholds applied when
   building the archive (Table 1). Are the same thresholds applied to the near real time values posted
   on the MIROVA website, or are those posted without a minimum VRP?
9. We noticed that Tupungatito does not appear in the archive, and that there are relatively few VIIRS
    750 m entries for Chilean volcanoes. Is there a reason for this?
10. Is the choice between a global and a local background applied uniformly to all volcanoes?
11. The distance published on the MIROVA web page for each detection: is it the distance to the
    hottest alerted pixel, or to the farthest one (as Max_Dist in the archive)?
12. The ETI is labelled NTI minus NTIbk in Figure 3 and NTI minus NTIapp in Figure 4 of the 2016
    paper. Which one is computed in the current system?
13. Besides Tests 1, 2 and 3 of SP426.5, does the operational near real time system apply any
    additional detection step, in particular a test on the radiance integrated over the summit ROI
    (rather than pixel by pixel), or a test on brightness temperature relative to the local
    background? We ask because two such steps exist in our code (the second one currently
    disabled) and we cannot trace them to your published description.
14. On 14 September 2026 the VIIRS 375 m GeoTIFFs offered on the website changed from geographic
    coordinates to a UTM grid of 375 m cells. Is this UTM grid the one on which detection and the VRP
    are computed, and did the change affect how detections are computed or only how the image is exported?

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
| 6 | D28, D18 (D17 y el centro de grilla ya los contesta Fernandina 2025 p. 9) |
| 7 | D29 |
| 8 | piso VRP del NRT (S130 lo quitó; decisión 3 de S142); la versión S139 preguntaba por `class` y el filtrado, ya contestado por Coppola et al. 2026 p. 7, 8, 10 a 12 |
| 9 | H603, H604 del eje 6 |
| 10 | `lbg_global_compatible` (MISSION, nota S125) |
| 11 | semantica de FALSO_POSITIVO y Distancia_km del scraper (banco S139) |
| 12 | ecuacion del ETI nunca escrita en SP426.5 (LECTURA_PDF S139) |
| 13 | **D30 y D31** (agregada en S146): el Test 1 integrado en el ROI y el test de temperatura de brillo con N·σ = 5 / 10 son caminos nuestros que ningún paper del grupo describe (AUDIT_S146 V-06 y V-08). Es la pregunta que más trabajo puede ahorrar del plan de paridad: si la respuesta es «no», queda resuelta la pregunta de fidelidad (los dos caminos son nuestros) sin necesidad de A/B; qué hacer con el Test 1 integrado sigue pidiendo la medición de recall de D30 |
| 14 | A106 (cambio de formato de TIF), D17 (grilla remuestreada) y el conteo de píxeles desde TIF |
