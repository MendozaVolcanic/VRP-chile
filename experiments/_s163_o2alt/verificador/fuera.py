exec(open('mi_cgal.py').read().split('if __name__')[0])
MODO["m"]="cgal"
R,E,etq=cargar(); tot=0; esc=0; alert_fuera=0; conbk=0
for k in range(R["VRP"].shape[0]):
    e=escena(R,E,k)
    if e is None: continue
    a,m13,ma,flat,mk=e
    B,info=rellenar(ma,1,(0,1,1))
    f=info.get('fuera_envolvente',0)
    if f: esc+=1; tot+=f
    # alertas fuera de envolvente: celdas de alerta en borde
    if f and R["BK"][k,0].size: conbk+=1
    # cuantas alertas cercanas al borde
    rr,cc=np.unravel_index(a-1,m13.shape,order="F")
    if ((rr<=2)|(cc<=2)|(rr>=64)|(cc>=64)).any(): alert_fuera+=1
print("escenas con celdas rellenadas fuera de la envolvente:",esc,"; con BK de MATLAB (comparadas):",conbk,"; escenas con alerta a <=2 px del borde:",alert_fuera)
