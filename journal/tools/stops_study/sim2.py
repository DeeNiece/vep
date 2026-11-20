import json,pickle,datetime as dt,statistics as st,itertools,collections
exec(open('sim.py').read().split("rows=[]")[0])   # bars, A, ts, atr4h
HK=dt.timezone(dt.timedelta(hours=8))
L=json.load(open('/home/claude/vep/journal/data/study_edge.json'))['labels']
mon={'Sep':9,'Oct':10,'Nov':11}
trades=[]
def mk(sym,d,E,sl,t0,src,tag):
    b=bars[sym]
    if t0>=b[-1][0]-6*3600: return
    w=[x for x in b if t0<=x[0]<=t0+5*86400]
    if not w or (w[-1][0]-t0)<12*3600: return
    R0=abs(E-sl);atr=atr4h(sym,t0)
    if not atr or not(1.0<=R0/atr<=4.5): return
    trades.append(dict(sym=sym,d=d,E=E,R0=R0,atr=atr,w=w,src=src,tag=tag,t0=t0))
for a in A:
    if a.get('sl') is None: continue
    mk(a['sym'],1 if a['dir']=='buy' else -1,a['entry'],a['sl'],ts(a['t']),'alert',a['tier'])
nl=0
for x in L:
    day,m=x['d'].split();d0=dt.datetime(2026,mon[m],int(day),tzinfo=HK);t1=int(d0.timestamp());t2=t1+86400
    E=x['entry'];hit=None
    for s,e,h,l,c in bars[x['sym']]:
        if t1<=s<t2 and l<=E<=h: hit=s;break
    if hit is None: continue
    # skip labels already represented by an alert on the same symbol within 8h
    mk(x['sym'],1 if x['dir']=='buy' else -1,E,x['sl'],hit,'label','L');nl+=1
print('trades',len(trades),collections.Counter(t['src'] for t in trades),collections.Counter((t['src'],t['d']) for t in trades))
def run(t,k,b=None,tr=None):
    E,R0,d=t['E'],t['R0'],t['d'];stop=E-d*k*R0;peak=E;last=None
    for s,e,h,l,c in t['w']:
        if d==1:
            if l<=stop: return (stop-E)*d/(k*R0)
            peak=max(peak,h)
        else:
            if h>=stop: return (stop-E)*d/(k*R0)
            peak=min(peak,l)
        fav=(peak-E)*d/R0
        if b is not None and fav>=b:
            stop=max(stop,E) if d==1 else min(stop,E)
            if tr is not None:
                ns=peak-d*tr*R0
                stop=max(stop,ns) if d==1 else min(stop,ns)
        last=c
    return (last-E)*d/(k*R0)
rules=[('no BE/trail',None,None),('BE at +1R',1,None),('BE at +2R',2,None),('trail 1R after +1.5R',1.5,1.0),('trail 1.5R after +2R',2,1.5),('trail 2R after +3R',3,2.0)]
def table(sub,name):
    print('\n',name,len(sub),'trades')
    print('rule'.ljust(24),*[f'stop {k}x'.rjust(16) for k in (1,1.5,2,3)])
    for nm,b,tr in rules:
        row=[]
        for k in (1,1.5,2,3):
            rs=[run(t,k,b,tr) for t in sub];row.append(f'{st.mean(rs):+.2f} ({100*sum(r>0 for r in rs)//len(rs)}%w)'.rjust(16))
        print(nm.ljust(24),*row)
table(trades,'ALL alerts + labels')
table([t for t in trades if t['src']=='label'],'labels only')
table([t for t in trades if t['src']=='alert'],'alerts only')
# MAE of runners: trades whose MFE reached 3R0 (full window, original risk units)
def mfe_mae(t):
    pk=0;m=0;pre=None
    best=0;mae_b4={}
    for s,e,h,l,c in t['w']:
        adv=((t['E']-l) if t['d']==1 else (h-t['E']))/t['R0'];m=max(m,adv)
        fav=((h-t['E']) if t['d']==1 else (t['E']-l))/t['R0']
        for th in (1,2,3):
            if fav>=th and th not in mae_b4: mae_b4[th]=m
        best=max(best,fav)
    return best,m,mae_b4
winners=[];losers=[]
for t in trades:
    best,m,b4=mfe_mae(t);t['mfe']=best;t['mae']=m;t['b4']=b4
    (winners if best>=3 else losers).append(t)
print('\nreached +3R at some point:',len(winners),'of',len(trades))
def pct(v,p): v=sorted(v);return v[min(len(v)-1,int(p*len(v)))]
for th in (1,2,3):
    v=[t['b4'][th] for t in trades if th in t['b4']]
    print(f'MAE before first reaching +{th}R:  n={len(v)}  median {st.median(v):.2f}R  75th {pct(v,.75):.2f}R  90th {pct(v,.9):.2f}R  max {max(v):.2f}R')
# giveback: after reaching +2R, max pullback from running peak, in R0
gb=[]
for t in trades:
    pk=None;mx=0;E,R0,d=t['E'],t['R0'],t['d']
    for s,e,h,l,c in t['w']:
        f=((h-E) if d==1 else (E-l))/R0
        if pk is None and f>=2: pk=f
        if pk is not None:
            pk=max(pk,f);cur=((l-E) if d==1 else (E-h))/R0
            mx=max(mx,pk-cur)
    if pk is not None: gb.append((t['sym'],t['src'],round(pk,1),round(mx,2)))
print('\nafter reaching +2R: peak R and the largest pullback from the running peak (R0)'); 
for g in gb: print(*g)
v=[g[3] for g in gb]
print('n',len(v),'median',round(st.median(v),2),'75th',round(pct(v,.75),2),'90th',round(pct(v,.9),2),'max',max(v))
# stop size context
print('\nstop size in %% of price and in 4H ATR: median %.2f%%  %.2f ATR'%(st.median(100*t['R0']/t['E'] for t in trades),st.median(t['R0']/t['atr'] for t in trades)))
print('by symbol median stop %:',{s:round(st.median([100*t['R0']/t['E'] for t in trades if t['sym']==s]),2) for s in sorted(set(t['sym'] for t in trades))})
pickle.dump(trades,open('trades.pkl','wb'))
