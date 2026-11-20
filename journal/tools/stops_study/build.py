import json,glob,datetime as dt,collections,pickle
TR='/root/.claude/projects/-home-claude/970db365-39a1-5e6f-b6bf-bd1bbbf4e8ae/tool-results/'
def load(f):
    d=json.loads(open(f).read())
    if isinstance(d,list): d=json.loads(d[0]['text'])
    return d
src=collections.defaultdict(list)  # sym -> [(prio,step,t,h,l,c)]
for f in glob.glob(TR+'*ohlcv*'):
    d=load(f);b=d['bars'];t=b['t'];step=int((t[1]-t[0])/60)
    sym=d['description'] if False else None
    ex=[k for k in d if k in('symbol','description','exchange')]
    name=None
    for k in ('symbol','description'):
        pass
    s=str(d.get('symbol') or d.get('description'))
    sym=s.split(':')[-1][:6]
    ven='PEPPERSTONE' if 'PEPPERSTONE' in s else 'OANDA'
    src[sym].append((ven,step,t,b['h'],b['l'],b['c']))
out={}
for sym,L in src.items():
    # prefer Pepperstone, finest step; fill gaps with OANDA 15m
    pts={}
    for ven,step,t,h,l,c in sorted(L,key=lambda x:(x[0]!='PEPPERSTONE',-x[1])):
        pass
    segs=[]
    pep=[x for x in L if x[0]=='PEPPERSTONE']; oan=[x for x in L if x[0]=='OANDA' and x[1]==15]
    # build time-ordered bars: take Pepperstone segs (all steps), then OANDA 15m only where no Pepperstone coverage
    covered=[(min(x[2]),max(x[2])) for x in pep]
    bars=[]
    for ven,step,t,h,l,c in pep:
        for i in range(len(t)): bars.append((t[i],t[i]+step*60,h[i],l[i],c[i]))
    if oan:
        ven,step,t,h,l,c=max(oan,key=lambda x:len(x[2]))
        for i in range(len(t)):
            if not any(a<=t[i]<=b for a,b in covered): bars.append((t[i],t[i]+900,h[i],l[i],c[i]))
    # dedupe overlapping: prefer finer bars: sort by start, drop bars fully inside an already-kept finer bar span
    bars.sort(key=lambda x:(x[0],x[1]-x[0]))
    out[sym]=bars
    print(sym,len(bars),dt.datetime.fromtimestamp(bars[0][0],dt.UTC),dt.datetime.fromtimestamp(bars[-1][0],dt.UTC))
pickle.dump(out,open('bars.pkl','wb'))
