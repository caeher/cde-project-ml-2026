import json,re,sys
def cargar(path):
    raw=open(path,encoding='utf-8').read()
    d,_=json.JSONDecoder().raw_decode(raw[raw.index('\n[')+1:])
    return [x for x in d if isinstance(x,str)]
def limpio(t):
    t=re.sub(r'https?://\S+','',t); t=re.sub(r'(^|\s)@\w+','',t); return re.sub(r'\s+',' ',t).strip()
EN=set("the and you your are for this that with have not but they what from will just has was".split())
def es(t):
    w=re.findall(r"[a-záéíóúñ]+",t.lower()); 
    return len(w)>=2 and sum(x in EN for x in w)/len(w)<0.15
if __name__=="__main__":
    seen=set(); out=[]
    for f in sys.argv[2:]:
        for t in cargar(f):
            c=limpio(t)
            if len(re.sub(r'[^\wáéíóúñ]','',c))<6 or not es(c): continue
            k=re.sub(r'\W+',' ',c.lower())
            if k in seen: continue
            seen.add(k); out.append((f.split('/')[-1].split('.')[0],c))
    json.dump(out,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False)
    print(len(out))
