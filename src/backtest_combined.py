"""
backtest_combined.py
Vol targeting sur QQQ combinant vol REALISEE (HAR-RV) et vol IMPLICITE (options 4h).
Fenetre 2020-2022 (inclut le krach COVID). Rebalancement daily.

Strategies comparees :
  - Buy & Hold QQQ (benchmark)
  - HAR-RV lisse        (pure realisee, retardee)
  - IV pur              (pure implicite, forward-looking, zero warmup)
  - Blend HAR+IV        (60% HAR + 40% IV*0.85)
  - HAR-IV (regression) (IV comme regresseur dans HAR)
"""
import numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
from backtest_intraday import fc_har, fc_yang_zhang, fc_garch, run, metrics, PPY

IV_ADJ = 0.85   # retrait de la prime de risque de vol

daily = pd.read_parquet("/home/claude/qqq_daily_from5m.parquet").sort_index()
iv = pd.read_csv("/home/claude/qqq_iv_daily_2020_2022.csv", parse_dates=['date']).set_index('date')
iv.index = iv.index.tz_localize(None) if iv.index.tz else iv.index

# fenetre overlap options
a, b = iv.index.min(), iv.index.max()
daily = daily.loc[a:b]
ret, rv = daily['ret_cc'], daily['rv_total']

# --- forecasters ---
har = fc_har(rv, refit=10, min_obs=35).reindex(daily.index)
har_s = har.ewm(span=10).mean()
yz = fc_yang_zhang(daily, 20)
iv_f = (iv['qqq_vix_mf']/100.0 * IV_ADJ).reindex(daily.index)   # vol implicite ajustee
iv_f = iv_f.ffill(limit=2)

# blend (necessite HAR -> demarre apres warmup)
blend = 0.6*har_s + 0.4*iv_f

# HAR-IV : regression HAR augmentee de l'IV (causale, refit periodique)
def fc_har_iv(rv_series, iv_series, refit=10, min_obs=35):
    rvol = np.sqrt(rv_series.values); ivv = iv_series.values
    n=len(rvol); d=rvol.copy()
    w=pd.Series(rvol).rolling(5).mean().values; m=pd.Series(rvol).rolling(22).mean().values
    y=np.r_[rvol[1:],np.nan]; out=np.full(n,np.nan); t=max(min_obs,22)
    while t<n:
        sl=slice(22,t)
        X=np.c_[np.ones(t-22),d[sl],w[sl],m[sl],ivv[sl]]; Y=y[sl]
        msk=np.isfinite(Y)&np.isfinite(X).all(1)
        if msk.sum()>40:
            beta,*_=np.linalg.lstsq(X[msk],Y[msk],rcond=None)
            h=min(refit,n-t)
            for k in range(h):
                j=t+k
                if np.isfinite([d[j],w[j],m[j],ivv[j]]).all():
                    out[j]=max(beta@np.r_[1,d[j],w[j],m[j],ivv[j]],1e-4)
        t+=refit
    return pd.Series(out*np.sqrt(PPY),index=rv_series.index)

har_iv = fc_har_iv(rv, iv['qqq_vix_mf'].reindex(daily.index).ffill(limit=2)/100.0).ewm(span=10).mean()

strategies = {
    'HAR-RV lisse': har_s,
    'IV pur':       iv_f,
    'Blend HAR+IV': blend,
    'HAR-IV reg.':  har_iv,
}

if __name__=='__main__':
    print(f"Fenetre : {daily.index.min().date()} -> {daily.index.max().date()} ({len(daily)}j)")
    print(f"IV valide : {iv_f.notna().sum()} j | HAR valide : {har_s.notna().sum()} j\n")

    # fenetre commune pour comparaison equitable (toutes strategies dispo)
    start = max(s.first_valid_index() for s in strategies.values())
    start = daily.index[daily.index.get_loc(start)+1]
    print("Fenetre commune backtest:", start.date(), "->", daily.index[-1].date())

    rows=[]; eqc={}
    bh = run(iv_f).loc[start:]['bh']   # bh identique quel que soit le forecast
    rows.append({**metrics(bh,'Buy & Hold QQQ'),'turnover_an':0.0,'lev':1.0})
    eqc['Buy & Hold QQQ']=(1+bh).cumprod()
    for name,fc in strategies.items():
        bt=run(fc).loc[start:]
        m=metrics(bt['strat'],name); m['turnover_an']=bt['turn'].mean()*PPY; m['lev']=bt['w'].mean()
        rows.append(m); eqc[name]=(1+bt['strat']).cumprod()
    res=pd.DataFrame(rows)
    print("\n=== BACKTEST COMBINE (cible 15%, cap 2x, couts) ===")
    print(res[['strategie','CAGR','vol_ann','Sharpe','Sortino','max_DD','Calmar','turnover_an','lev']].round(3).to_string(index=False))

    # focus COVID : drawdown max sur fev-avr 2020 si couvert
    cov_a,cov_b='2020-02-19','2020-04-30'
    print(f"\n=== Comportement COVID ({cov_a} -> {cov_b}) ===")
    for name in ['Buy & Hold QQQ']+list(strategies.keys()):
        if name=='Buy & Hold QQQ':
            seg=run(iv_f).loc[cov_a:cov_b]; r=seg['bh']; lev=1.0
        else:
            seg=run(strategies[name]).loc[cov_a:cov_b]; r=seg['strat']; lev=seg['w'].mean()
        if len(r)==0:
            print(f"  {name:16s}: hors fenetre"); continue
        eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
        print(f"  {name:16s}: perf {eq.iloc[-1]-1:+6.1%}  DDmax {dd:+6.1%}  levier_moy {lev:.2f}")

    res.to_csv("/home/claude/bt_combined_results.csv",index=False)
    pd.DataFrame(eqc).reindex(eqc['Buy & Hold QQQ'].index).to_csv("/home/claude/bt_combined_equity.csv")
    print("\nSaved bt_combined_results.csv, bt_combined_equity.csv")
