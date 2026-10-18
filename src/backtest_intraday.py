"""
backtest_intraday.py
Vol targeting sur QQQ en DAILY, forecasters nourris par la realized variance 5-min.
Donnees : QQQ 5-min 2020-2026 -> daily OHLC + RV (gap overnight inclus).

Forecasters : Yang-Zhang (OHLC daily), GARCH(1,1)-t (rendements daily),
              HAR-RV (realized variance intraday, Corsi 2009).
Rebalancement DAILY, horizon de prevision 1 jour (horizon = frequence). Benchmark QQQ.
"""
import numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
from arch import arch_model

PPY = 252
RF = 0.03            # cash moyen 2020-2026 (approx)
BORROW_SPREAD = 0.005
TC = 0.0002          # 2 bps par unite de turnover

daily = pd.read_parquet("/home/claude/qqq_daily_from5m.parquet")
daily = daily.sort_index()
ret = daily['ret_cc']
rv  = daily['rv_total']                 # realized variance journaliere (fraction^2)

# ----------------------------------------------------------------------
# Forecasters (vol annualisee, causals : forecast[t] -> vol pour t+1)
# ----------------------------------------------------------------------
def fc_yang_zhang(d, n=20):
    o,h,l,c = d['open'],d['high'],d['low'],d['close']; cp=c.shift(1)
    ro=np.log(o/cp); rc=np.log(c/o)
    rs=(np.log(h/c)*np.log(h/o)+np.log(l/c)*np.log(l/o))
    k=0.34/(1.34+(n+1)/(n-1))
    yz=np.sqrt(ro.rolling(n).var()+k*rc.rolling(n).var()+(1-k)*rs.rolling(n).mean())
    return yz*np.sqrt(PPY)

def fc_garch(r, refit=10, min_obs=250, dist='t'):
    x=r.values*100; idx=r.index; out=np.full(len(x),np.nan); t=min_obs
    while t < len(x):
        try:
            res=arch_model(x[:t],vol='Garch',p=1,q=1,dist=dist,mean='Constant').fit(disp='off',show_warning=False)
            h=min(refit,len(x)-t)
            f=res.forecast(horizon=h,reindex=False)
            out[t:t+h]=np.sqrt(f.variance.values[-1][:h])/100*np.sqrt(PPY)
        except Exception:
            out[t:min(t+refit,len(x))]=np.nan
        t+=refit
    return pd.Series(out,index=idx)

def fc_har(rv_series, refit=10, min_obs=250):
    """HAR-RV (Corsi) en espace volatilite : RVol[t+1] ~ RVol_d + RVol_w + RVol_m."""
    rvol=np.sqrt(rv_series.values)           # vol realisee journaliere
    idx=rv_series.index; n=len(rvol)
    d=rvol.copy()
    w=pd.Series(rvol).rolling(5).mean().values
    m=pd.Series(rvol).rolling(22).mean().values
    y=np.r_[rvol[1:],np.nan]                  # cible = RVol[t+1]
    out=np.full(n,np.nan); t=max(min_obs,22)
    while t < n:
        sl=slice(22,t)                        # echantillon causal (<= t)
        X=np.c_[np.ones(t-22),d[sl],w[sl],m[sl]]; Y=y[sl]
        msk=np.isfinite(Y)&np.isfinite(X).all(1)
        if msk.sum()>50:
            beta,*_=np.linalg.lstsq(X[msk],Y[msk],rcond=None)
            h=min(refit,n-t)
            for k in range(h):
                j=t+k
                if np.isfinite([d[j],w[j],m[j]]).all():
                    pred=beta@np.r_[1,d[j],w[j],m[j]]
                    out[j]=max(pred,1e-4)*np.sqrt(PPY)
        t+=refit
    return pd.Series(out,index=idx)

forecasts={
    'Yang-Zhang (20j)': fc_yang_zhang(daily,20),
    'GARCH(1,1)-t':     fc_garch(ret),
    'HAR-RV':           fc_har(rv),
}

# ----------------------------------------------------------------------
# Horse race : verite = realized variance FORWARD (1 jour), QLIKE + corr
# ----------------------------------------------------------------------
def scores(forecasts, rv, fwd=1):
    rv_fwd=(rv.rolling(fwd).mean().shift(-fwd))*PPY       # variance annualisee realisee a venir
    rows=[]
    for name,fc in forecasts.items():
        var_f=fc**2
        df=pd.concat([var_f.rename('f'),rv_fwd.rename('rv')],axis=1).dropna()
        df=df[(df['f']>0)&(df['rv']>0)]
        qlike=np.mean(df['rv']/df['f']-np.log(df['rv']/df['f'])-1)
        rmse=np.sqrt(np.mean((np.sqrt(df['f'])-np.sqrt(df['rv']))**2))
        corr=np.corrcoef(np.sqrt(df['f']),np.sqrt(df['rv']))[0,1]
        rows.append({'forecaster':name,'QLIKE':qlike,'RMSE_vol':rmse,'corr':corr,'n':len(df)})
    return pd.DataFrame(rows).sort_values('QLIKE').reset_index(drop=True)

# ----------------------------------------------------------------------
# Moteur vol targeting (daily)
# ----------------------------------------------------------------------
def run(forecast, target=0.15, cap=2.0, band=0.0):
    df=pd.DataFrame({'ret':ret,'fc':forecast})
    w_target=(target/df['fc']).clip(0,cap)
    if band>0:                      # bande de non-rebalancement : on ne bouge que si |dw|>band
        wv=w_target.values; held=np.full(len(wv),np.nan); cur=np.nan
        for i,x in enumerate(wv):
            if not np.isfinite(x): held[i]=cur; continue
            if not np.isfinite(cur) or abs(x-cur)>band: cur=x
            held[i]=cur
        w_target=pd.Series(held,index=df.index)
    df['w']=w_target.shift(1)
    df=df.dropna(subset=['w','ret'])
    rate=np.where(df['w']>1,RF+BORROW_SPREAD,RF)/PPY
    cash=(1-df['w'])*rate
    turn=df['w'].diff().abs().fillna(df['w'].abs())
    ra=np.expm1(df['ret'])
    df['strat']=df['w']*ra+cash-turn*TC
    df['bh']=ra; df['turn']=turn
    return df

def metrics(r,name):
    r=r.dropna(); eq=(1+r).cumprod(); yrs=len(r)/PPY
    cagr=eq.iloc[-1]**(1/yrs)-1; vol=r.std()*np.sqrt(PPY)
    sharpe=(r.mean()*PPY-RF)/vol; dn=r[r<0].std()*np.sqrt(PPY)
    sortino=(r.mean()*PPY-RF)/dn; dd=eq/eq.cummax()-1
    return {'strategie':name,'CAGR':cagr,'vol_ann':vol,'Sharpe':sharpe,
            'Sortino':sortino,'max_DD':dd.min(),'Calmar':cagr/abs(dd.min()),'eqfin':eq.iloc[-1]}

if __name__=='__main__':
    print(f"QQQ daily depuis 5-min : {daily.index.min().date()} -> {daily.index.max().date()} ({len(daily)}j)\n")
    # fenetre commune (apres warmup de tous les forecasters)
    start=max(fc.first_valid_index() for fc in forecasts.values())
    start=daily.index[daily.index.get_loc(start)+1]
    print("Fenetre commune:",start.date(),"-> ",daily.index[-1].date(),"\n")

    sc=scores({k:v.loc[start:] for k,v in forecasts.items()}, rv.loc[start:])
    print("=== HORSE RACE (verite = RV intraday forward 1j) ===")
    print(sc.round(4).to_string(index=False))

    print("\n=== BACKTEST VOL TARGETING DAILY (cible 15%, cap 2x, couts) ===")
    rows=[]; eqc={}
    bh=run(forecasts['HAR-RV']).loc[start:]['bh']
    rows.append({**metrics(bh,'Buy & Hold QQQ'),'turnover_an':0.0,'levier_moyen':1.0})
    eqc['Buy & Hold QQQ']=(1+bh).cumprod()
    for name,fc in forecasts.items():
        bt=run(fc).loc[start:]
        m=metrics(bt['strat'],name); m['turnover_an']=bt['turn'].mean()*PPY; m['levier_moyen']=bt['w'].mean()
        rows.append(m); eqc[name]=(1+bt['strat']).cumprod()
    # HAR-RV lisse (EWMA span 10) : le correctif anti-turnover
    har_s=forecasts['HAR-RV'].ewm(span=10).mean()
    btb=run(har_s).loc[start:]
    mb=metrics(btb['strat'],'HAR-RV lisse (s10)'); mb['turnover_an']=btb['turn'].mean()*PPY; mb['levier_moyen']=btb['w'].mean()
    rows.append(mb); eqc['HAR-RV lisse (s10)']=(1+btb['strat']).cumprod()
    res=pd.DataFrame(rows)
    print(res[['strategie','CAGR','vol_ann','Sharpe','Sortino','max_DD','Calmar','turnover_an','levier_moyen']].round(3).to_string(index=False))

    # exports
    res.to_csv("/home/claude/bt5m_results.csv",index=False)
    sc.to_csv("/home/claude/bt5m_scores.csv",index=False)
    eqdf=pd.DataFrame(eqc).reindex(eqc['Buy & Hold QQQ'].index)
    eqdf.to_csv("/home/claude/bt5m_equity.csv")
    print("\nSaved bt5m_results.csv, bt5m_scores.csv, bt5m_equity.csv")
