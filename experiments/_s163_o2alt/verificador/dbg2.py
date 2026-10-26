import sys
exec(open('mi_regla.py').read().split('if __name__')[0])
R,E,etq=cargar()
k=4
a,m13,ma,flat,mk=escena(R,E,k)
rr,cc=np.indices(ma.shape); ok=np.isfinite(ma)
P=[(int(r),int(c)) for r,c in zip(rr[ok],cc[ok])]
# buscar triadas sin resolver
orig=incircle_sign
cnt=0
def spy(a_,b,c,d,s):
    global cnt
    sg,e=orig(a_,b,c,d,s)
    if e and sg==0 and cnt<5:
        cnt+=1; print("sin resolver:",a_,b,c,d)
    return sg,e
incircle_sign=spy
T,info=triangular(P,1); print(info)
