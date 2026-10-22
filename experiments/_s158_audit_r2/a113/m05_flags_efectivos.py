# M05: flags y umbrales efectivos de mirova_equivalent leidos de pipeline.profile (A89), no del YAML.
# Pregunta 1/2: si el perfil no se cargara, VRP_PROFILE_NAME o los valores saldrian por defecto; se imprime el nombre
#   del perfil cargado como control.
import os, sys
os.environ["VRP_PROFILE"]="mirova_equivalent"
sys.path.insert(0, r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2")
import pipeline.profile as P
names = [n for n in dir(P) if n.isupper()]
print("perfil:", getattr(P,"PROFILE_NAME",None) or getattr(P,"ACTIVE_PROFILE",None))
keys = ["K1","C1","C2","SECOND_PASS","EXCLUDE","LOCAL_KERNEL","UNSUITABLE","CLIP","CAP","DAYTIME","TEST1","PROSE","ROI1","DUAL","NTI_K1","VIIRS_C2"]
for n in sorted(names):
    if any(k in n for k in keys): print(n, "=", getattr(P,n))
