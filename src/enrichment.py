"""
enrichment.py
Analyses complementaires :
 1. Sensibilite (cible de vol x cap de levier)
 2. Comportement en crise (levier pendant les krachs)
 3. Demonstration du signal de vol implicite (overlap options vs realise)
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from backtest import (load_weekly, fc_garch, fc_yang_zhang, run_voltarget,
                      metrics, WPY)

w = load_weekly("/home/claude/qqq_weekly.csv")
fc = fc_garch(w, vol='Garch', dist='t')   # meilleur forecaster du backtest

# ----------------------------------------------------------------------
# 1) SENSIBILITE : cible de vol x cap
# ----------------------------------------------------------------------
print("=== 1) SENSIBILITE (forecaster = GARCH) ===")
rows = []
for tgt in [0.10, 0.15, 0.20]:
    for cap in [1.0, 1.5, 2.0, 3.0]:
        bt = run_voltarget(w, fc, target_vol=tgt, cap=cap)
        m = metrics(bt['strat'], f"tgt={tgt:.0%} cap={cap:.1f}")
        m['lev'] = bt['w'].mean()
        rows.append(m)
sens = pd.DataFrame(rows)
print(sens[['strategie','CAGR','vol_ann','Sharpe','max_DD','Calmar','lev']]
      .round(3).to_string(index=False))
sens.to_csv("/home/claude/sensitivity.csv", index=False)

# ----------------------------------------------------------------------
# 2) CRISES : levier moyen & perf pendant les grands krachs
# ----------------------------------------------------------------------
print("\n=== 2) COMPORTEMENT EN CRISE (tgt=15%, cap=2) ===")
bt = run_voltarget(w, fc, target_vol=0.15, cap=2.0)
crises = {
    'Dot-com (2000-2002)':  ('2000-03-01', '2002-10-01'),
    'GFC 2008':             ('2008-09-01', '2009-03-01'),
    'COVID 2020':           ('2020-02-15', '2020-04-15'),
    'Bear 2022':            ('2022-01-01', '2022-10-15'),
}
rows = []
for name, (a, b) in crises.items():
    seg = bt.loc[a:b]
    if len(seg) == 0:
        continue
    bh_ret = (1+seg['bh']).prod() - 1
    st_ret = (1+seg['strat']).prod() - 1
    rows.append({'crise': name, 'semaines': len(seg),
                 'levier_moyen': seg['w'].mean(),
                 'levier_min': seg['w'].min(),
                 'perf_buyhold': bh_ret, 'perf_strat': st_ret})
cr = pd.DataFrame(rows)
print(cr.round(3).to_string(index=False))
cr.to_csv("/home/claude/crises.csv", index=False)

# ----------------------------------------------------------------------
# 3) SIGNAL DE VOL IMPLICITE vs REALISE (overlap options, sept-oct 2026)
# ----------------------------------------------------------------------
print("\n=== 3) SIGNAL IMPLICITE (QQQ-VIX maison) vs REALISE ===")
iv = pd.read_csv("/home/claude/qqq_iv_daily.csv", parse_dates=['date']).set_index('date')
d = pd.read_csv("/home/claude/qqq_daily_recent.csv", parse_dates=['timestamp'])
d = d.rename(columns={'timestamp':'date'}).set_index('date').sort_index()
d['ret'] = np.log(d['close']/d['close'].shift(1))
# vol realisee annualisee : EWMA court (hl=5j) et rolling 10j, en %
d['rv_ewma'] = d['ret'].ewm(halflife=5).std()*np.sqrt(252)*100
d['rv_roll10'] = d['ret'].rolling(10).std()*np.sqrt(252)*100

merged = iv.join(d[['close','rv_ewma','rv_roll10']], how='left')
# vol realisee FORWARD 5 jours (ce que l'IV est censee predire)
d['rv_fwd5'] = d['ret'][::-1].rolling(5).std()[::-1].shift(-1)*np.sqrt(252)*100
merged = merged.join(d[['rv_fwd5']], how='left')
show = merged[['close','qqq_vix_mf','qqq_iv_atm','rv_roll10','rv_fwd5']]
print(show.round(2).to_string())

# correlation IV(t) avec vol realisee forward
sub = merged.dropna(subset=['qqq_vix_mf','rv_fwd5'])
if len(sub) > 3:
    c_iv = np.corrcoef(sub['qqq_vix_mf'], sub['rv_fwd5'])[0,1]
    sub2 = merged.dropna(subset=['rv_roll10','rv_fwd5'])
    c_rv = np.corrcoef(sub2['rv_roll10'], sub2['rv_fwd5'])[0,1]
    print(f"\nCorr IV implicite(t) -> vol realisee fwd 5j : {c_iv:+.2f}")
    print(f"Corr vol realisee 10j(t) -> vol realisee fwd 5j : {c_rv:+.2f}")
merged.to_csv("/home/claude/iv_vs_realized.csv")
print("\nSaved -> sensitivity.csv, crises.csv, iv_vs_realized.csv")
