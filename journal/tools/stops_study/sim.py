import json,pickle,datetime as dt,statistics as st,collections
bars=pickle.load(open('bars.pkl','rb'))
A=json.load(open('/home/claude/vep/journal/data/study_4h.json'))['alerts']
M={'Nov':11}
def ts(s):
    d,mo,hm=s.split();h,m=hm.split(':')
    return int(dt.datetime(2026,11,int(d),int(h),int(m),tzinfo=dt.timezone(dt.timedelta(hours=8))).timestamp())
def atr4h(sym,t0):
    b=bars[sym];g={}
    for s,e,h,l,c in b:
        if s<t0-14*14400 or s>=t0: continue
        k=(s-7200)//14400
        if k in g: g[k][0]=max(g[k][0],h);g[k][1]=min(g[k][1],l);g[k][2]=c
        else: g[k]=[h,l,c,None]
    ks=sorted(g);trs=[];pc=None
    for k in ks:
        h,l,c,_=g[k];tr=h-l if pc is None else max(h-l,abs(h-pc),abs(l-pc));trs.append(tr);pc=c
    return st.mean(trs[-14:]) if trs else None
rows=[]
for a in A:
    if a.get('sl') is None: continue
    sym=a['sym'];t0=ts(a['t']);b=bars[sym]
    if t0>=b[-1][0]-6*3600: continue
    w=[x for x in b if t0<=x[0]<=t0+5*86400]
    cover=(w[-1][0]-t0)/3600 if w else 0
    if cover<12: continue
    d=1 if a['dir']=='buy' else -1;E=a['entry'];R0=abs(E-a['sl'])
    rows.append(dict(a=a,w=w,d=d,E=E,R0=R0,cover=cover,atr=atr4h(sym,t0)))
print(len(A),'alerts,',len(rows),'with exact prices and 12h+ of data after entry')
def path(r):
    mfe=mae=0;out=[]
    for s,e,h,l,c in r['w']:
        fav=(h-r['E'])*r['d'] if r['d']==1 else (r['E']-l)
        adv=(r['E']-l)*1 if r['d']==1 else (h-r['E'])
        out.append((fav/r['R0'],adv/r['R0'],((c-r['E'])*r['d'])/r['R0']))
    return out
tab=[]
for r in rows:
    p=path(r);r['p']=p
    mfe=max(x[0] for x in p);mae=max(x[1] for x in p)
    # MAE before first reaching +1R / +2R
    def mae_before(th):
        m=0
        for f,ad,_ in p:
            m=max(m,ad)
            if f>=th: return m
        return None
    r['mfe']=mfe;r['mae']=mae;r['m1']=mae_before(1);r['m2']=mae_before(2)
    r['pct']=100*r['R0']/r['E'];r['stopatr']=r['R0']/r['atr'] if r['atr'] else None
    a=r['a'];tab.append((a['sym'],a['tier'],a['dir'],a['t'],round(r['pct'],2),round(r['stopatr'],2) if r['stopatr'] else None,round(mfe,2),round(mae,2),None if r['m1'] is None else round(r['m1'],2),None if r['m2'] is None else round(r['m2'],2),round(r['cover'])))
print('sym tier dir time stop% stopATR4h MFE_R MAE_R MAEbefore+1R MAEbefore+2R hrs')
for x in tab: print(*x)
pickle.dump(rows,open('rows.pkl','wb'))
