import json,sys; sys.path.insert(0,'.'); sys.path.insert(0,r"C:/Users/willi/AppData/Local/Temp/claude/C--Users-willi-Documents-ues-especializacion-proyecto/b7ab0b24-5862-4513-a64c-b0eb7d750d77/scratchpad")
import numpy as np,pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, confusion_matrix
from lab4 import L
import app.api.main as M
from src.evaluation.comparar_modelos import mcnemar
from src.evaluation.comparar_v4 import f1m, ic_delta
o=json.load(open(r"C:/Users/willi/AppData/Local/Temp/claude/C--Users-willi-Documents-ues-especializacion-proyecto/b7ab0b24-5862-4513-a64c-b0eb7d750d77/scratchpad/lote4.json",encoding='utf-8'))
rows=[(i,t,L[i]) for i,(h,t) in enumerate(o) if L.get(i,-1)>=0]
df=pd.DataFrame(rows,columns=['i','texto','label'])
def pred(ruta):
    M._modelos.clear(); M.MODELOS=Path(ruta); return np.array([M.predecir(t)['label'] for t in df.texto])
df['base']=pred('models/final5'); df['nuevo']=pred('models/final_v5')
df.to_csv(r"C:/Users/willi/AppData/Local/Temp/claude/C--Users-willi-Documents-ues-especializacion-proyecto/b7ab0b24-5862-4513-a64c-b0eb7d750d77/scratchpad/lote4_eval.csv",index=False,encoding='utf-8-sig')
y=df.label.values; print("hilo CECOT nuevo, n =",len(df),"| clases:",np.bincount(y,minlength=4).tolist())
for n in ['base','nuevo']:
    p=df[n].values; print(f"{n:6} acierto {(p==y).mean():.3f}  F1-macro {f1m(y,p):.4f}")
    print(pd.DataFrame(confusion_matrix(y,p,labels=[0,1,2,3]),index=['esp0','esp1','esp2','esp3'],columns=['p0','p1','p2','p3']))
m=mcnemar(df.base.values==y,df.nuevo.values==y); lo,hi,_=ic_delta(y,df.base.values,df.nuevo.values)
print(f"Δ F1 {f1m(y,df.nuevo.values)-f1m(y,df.base.values):+.4f} IC pareado [{lo:+.4f},{hi:+.4f}] McNemar b/c {m['b']}/{m['c']} p={m['p_exacta']:.4f}")
for c,nm in enumerate(['No Tóxico','Ofensivo','Odio','Amenazas']):
    s=y==c; print(f"  recall {nm:<10} n={int(s.sum()):<3} base {(df.base[s]==c).mean():.3f}  nuevo {(df.nuevo[s]==c).mean():.3f}")
