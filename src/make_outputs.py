"""
make_outputs.py
Consolidation finale : tout recalcule sur une FENETRE COMMUNE (date ou tous les
forecasters sont disponibles), rebase a 1, et exporte un JSON propre (NaN -> null).
"""
import numpy as np, pandas as pd, json, math
import warnings; warnings.filterwarnings('ignore')
from backtest import (load_weekly, fc_rolling, fc_ewma, fc_yang_zhang, fc_garch,
                      forecast_scores, run_voltarget, metrics, WPY)

w = load_weekly("/home/claude/qqq_weekly.csv")

forecasts = {
    'Rolling std (13s)': fc_rolling(w, 13),
    'EWMA (hl=6s)':      fc_ewma(w, 6),
    'Yang-Zhang (13s)':  fc_yang_zhang(w, 13),
    'GARCH(1,1)-t':      fc_garch(w, vol='Garch', dist='t', min_obs=60),
    'EGARCH(1,1)-t':     fc_garch(w, vol='EGARCH', dist='t', min_obs=60),
}

# Fenetre commune : premiere date ou TOUS les forecasts existent (apres le lag 1)
first_valid = max(fc.first_valid_index() for fc in forecasts.values())
common_start = w.index[w.index.get_loc(first_valid) + 1]   # +1 pour le lag
print("Fenetre commune:", common_start.date(), "->", w.index[-1].date())

# Buy & hold rebase sur la meme fenetre
r_asset = np.expm1(w['ret'])
bh = r_asset.loc[common_start:]
bh_eq = (1+bh).cumprod()

results, equity, drawdown = [], {}, {}
equity['Buy & Hold QQQ'] = bh_eq
mb = metrics(bh, 'Buy & Hold QQQ'); mb['turnover_an']=0.0; mb['levier_moyen']=1.0
results.append(mb)

for name, fc in forecasts.items():
    bt = run_voltarget(w, fc, target_vol=0.15, cap=2.0)
    bt = bt.loc[common_start:]
    m = metrics(bt['strat'], name)
    m['turnover_an'] = bt['turn'].mean()*WPY
    m['levier_moyen'] = bt['w'].mean()
    results.append(m)
    equity[name] = (1+bt['strat']).cumprod()

eq = pd.DataFrame(equity).reindex(bh_eq.index)
dd = pd.DataFrame({c: eq[c]/eq[c].cummax()-1 for c in eq.columns})

# Buy & hold drawdown max sur la fenetre commune (pour le texte)
print(f"Buy&Hold DD max (fenetre commune): {dd['Buy & Hold QQQ'].min():.1%}")
print(f"GARCH DD max: {dd['GARCH(1,1)-t'].min():.1%}")

# Horse race sur la fenetre commune
wc = w.loc[common_start:]
fcc = {k: v.loc[common_start:] for k, v in forecasts.items()}
scores = forecast_scores(wc, fcc)
print("\nHorse race (fenetre commune):")
print(scores.round(4).to_string(index=False))

HERO = 'Yang-Zhang (13s)'   # vainqueur du backtest sur la fenetre commune

# Sensibilite (HERO) sur fenetre commune
sens = []
for tgt in [0.10, 0.15, 0.20]:
    for cap in [1.0, 2.0]:
        bt = run_voltarget(w, forecasts[HERO], target_vol=tgt, cap=cap).loc[common_start:]
        m = metrics(bt['strat'], f"tgt={tgt:.0%} cap={cap:.1f}")
        m['lev'] = bt['w'].mean()
        sens.append(m)

# Crises (HERO) - fenetre d'origine, clip au common_start
btg = run_voltarget(w, forecasts[HERO], target_vol=0.15, cap=2.0)
crises_def = {
    'Dot-com (2001-2002)': ('2001-01-01','2002-10-15'),
    'GFC 2008':            ('2008-09-01','2009-03-01'),
    'COVID 2020':          ('2020-02-15','2020-04-15'),
    'Bear 2022':           ('2022-01-01','2022-10-15'),
}
crises = []
for nm,(a,b) in crises_def.items():
    seg = btg.loc[a:b]
    if len(seg)==0: continue
    crises.append({'crise':nm,'semaines':int(len(seg)),
        'levier_moyen':float(seg['w'].mean()),'levier_min':float(seg['w'].min()),
        'perf_buyhold':float((1+seg['bh']).prod()-1),
        'perf_strat':float((1+seg['strat']).prod()-1)})

# ---- IV (inchange) ----
iv = pd.read_csv("qqq_iv_daily.csv", parse_dates=['date']).set_index('date')
d = pd.read_csv("qqq_daily_recent.csv", parse_dates=['timestamp']).rename(
    columns={'timestamp':'date'}).set_index('date').sort_index()
d['ret']=np.log(d['close']/d['close'].shift(1))
d['rv10']=d['ret'].rolling(10).std()*np.sqrt(252)*100
m_iv = iv.join(d[['close','rv10']])

def clean(x):
    if isinstance(x,float) and (math.isnan(x) or math.isinf(x)): return None
    return x
def cl_list(a): return [clean(float(v)) if v is not None else None for v in a]

bundle = {}
bundle['dates'] = [t.strftime('%Y-%m-%d') for t in eq.index]
bundle['equity'] = {c: cl_list(eq[c].values) for c in eq.columns}
bundle['drawdown'] = {c: cl_list(dd[c].values) for c in dd.columns}
bundle['results'] = [{k:clean(v) for k,v in r.items()} for r in results]
bundle['scores'] = [{k:clean(v) for k,v in r.items()} for r in scores.to_dict('records')]
bundle['sensitivity'] = [{k:clean(v) for k,v in r.items()} for r in sens]
bundle['crises'] = crises
bundle['iv'] = {
  'date': [t.strftime('%Y-%m-%d') for t in iv.index],
  'vix_mf': cl_list(iv['qqq_vix_mf'].values),
  'iv_atm': cl_list(iv['qqq_iv_atm'].values),
  'rv10': cl_list(m_iv['rv10'].values),
  'close': cl_list(m_iv['close'].values),
}
bundle['vrp'] = {'vix_mean':round(float(iv['qqq_vix_mf'].mean()),1),
                 'atm_mean':round(float(iv['qqq_iv_atm'].mean()),1),
                 'rv_mean':round(float(m_iv['rv10'].mean()),1)}
bundle['meta'] = {'start': common_start.strftime('%Y-%m-%d'),
                  'end': w.index[-1].strftime('%Y-%m-%d'),
                  'bh_dd_full': -0.827}   # DD plein echantillon 1999-2026 (no-warmup)

with open("report_data.json","w") as f:
    json.dump(bundle, f, allow_nan=False)   # <- echoue si NaN/inf reste
print("\nJSON propre ecrit. Resultats finaux:")
print(pd.DataFrame(results)[['strategie','CAGR','vol_ann','Sharpe','Sortino','max_DD','Calmar','turnover_an','levier_moyen']].round(3).to_string(index=False))
