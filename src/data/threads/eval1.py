import json,sys,re; sys.path.insert(0,'.'); sys.path.insert(0,r"C:/Users/willi/AppData/Local/Temp/claude/C--Users-willi-Documents-ues-especializacion-proyecto/b7ab0b24-5862-4513-a64c-b0eb7d750d77/scratchpad")
import pandas as pd, numpy as np
from sklearn.metrics import f1_score, confusion_matrix
from lab1 import L
from app.api.main import predecir
o=json.load(open(r"C:/Users/willi/AppData/Local/Temp/claude/C--Users-willi-Documents-ues-especializacion-proyecto/b7ab0b24-5862-4513-a64c-b0eb7d750d77/scratchpad/lote1.json",encoding='utf-8'))
rows=[dict(hilo='repatriados' if i<134 else 'canje',texto=t,label=L[i]) for i,(h,t) in enumerate(o) if L.get(i,-1)>=0]
df=pd.DataFrame(rows); df['pred']=[predecir(t)['label'] for t in df.texto]
df.to_csv(r"C:/Users/willi/AppData/Local/Temp/claude/C--Users-willi-Documents-ues-especializacion-proyecto/b7ab0b24-5862-4513-a64c-b0eb7d750d77/scratchpad/lote1_eval.csv",index=False,encoding='utf-8-sig')
print(len(df),"etiquetadas claras de",len(o)); print(df.label.value_counts().sort_index().to_dict())
print("acierto %.3f | F1-macro %.4f"%((df.label==df.pred).mean(),f1_score(df.label,df.pred,average='macro',labels=[0,1,2,3])))
print(pd.DataFrame(confusion_matrix(df.label,df.pred,labels=[0,1,2,3]),index=['esp0','esp1','esp2','esp3'],columns=['p0','p1','p2','p3']))
for h,g in df.groupby('hilo'): print(h,len(g),"acierto %.3f"%((g.label==g.pred).mean()))
