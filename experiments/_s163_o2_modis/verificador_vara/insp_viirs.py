import numpy as np, json
from scipy.io import loadmat
E=loadmat('viirs_matlab/entradas_o2.mat'); R=loadmat('viirs_matlab/resultado_o2.mat')
print({k:(v.shape,v.dtype) for k,v in E.items() if not k.startswith('__')})
print({k:(getattr(v,'shape',None),getattr(v,'dtype',None)) for k,v in R.items() if not k.startswith('__')})
et=json.load(open('viirs_matlab/entradas_o2_etiquetas.json',encoding='utf-8'))
print(len(et), et[0])
