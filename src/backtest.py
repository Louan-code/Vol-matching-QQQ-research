"""
backtest.py
Backtest d'une strategie de volatility targeting sur QQQ (donnees hebdomadaires,
1999-2026, ajustees splits + dividendes).

- Plusieurs forecasters de volatilite (rolling, EWMA, Yang-Zhang, GARCH, EGARCH)
- Horse race out-of-sample (QLIKE / RMSE)
- Moteur de sizing : w = target_vol / forecast, cappe, applique en t+1 (causal)
- Couts de transaction + cout du levier
- Metriques : CAGR, vol, Sharpe, Sortino, max DD, Calmar, turnover, levier moyen
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from arch import arch_model

WPY = 52                 # semaines / an
RF = 0.02                # taux cash moyen ~1999-2026 (approx)
BORROW_SPREAD = 0.005    # surcout d'emprunt pour le levier
TC = 0.0002              # cout de transaction par unite de turnover (2 bps)


# ----------------------------------------------------------------------
# Donnees : close ajuste + OHLC ajuste (pour Yang-Zhang)
# ----------------------------------------------------------------------
def load_weekly(path):
    w = pd.read_csv(path, parse_dates=['timestamp']).sort_values('timestamp')
    w = w.rename(columns={'timestamp': 'date', 'adjusted close': 'adj_close'})
    w = w.set_index('date')
    factor = w['adj_close'] / w['close']          # facteur d'ajustement
    w['o'] = w['open']  * factor
    w['h'] = w['high']  * factor
    w['l'] = w['low']   * factor
    w['c'] = w['adj_close']
    w['ret'] = np.log(w['c'] / w['c'].shift(1))   # rendement log hebdo
    return w.dropna(subset=['ret'])


# ----------------------------------------------------------------------
# Forecasters de vol (annualises). TOUS causals : forecast[t] = vol predite
# pour la semaine t+1 en utilisant uniquement l'information <= t.
# ----------------------------------------------------------------------
def fc_rolling(w, n=13):
    v = w['ret'].rolling(n).std() * np.sqrt(WPY)
    return v

def fc_ewma(w, halflife=6):
    v = w['ret'].ewm(halflife=halflife).std() * np.sqrt(WPY)
    return v

def fc_yang_zhang(w, n=13):
    o, h, l, c = w['o'], w['h'], w['l'], w['c']
    cp = c.shift(1)
    ro = np.log(o / cp)          # overnight (gap)
    rc = np.log(c / o)           # open-to-close
    ru = np.log(h / o); rd = np.log(l / o); rcc = np.log(c / o)
    # Rogers-Satchell
    rs = (np.log(h/c)*np.log(h/o) + np.log(l/c)*np.log(l/o))
    k = 0.34 / (1.34 + (n+1)/(n-1))
    sig_o = ro.rolling(n).var()
    sig_c = rc.rolling(n).var()
    sig_rs = rs.rolling(n).mean()
    yz = np.sqrt(sig_o + k*sig_c + (1-k)*sig_rs) * np.sqrt(WPY)
    return yz

def fc_garch(w, refit=4, p=1, q=1, vol='Garch', dist='t', min_obs=100):
    """GARCH/EGARCH refit sur fenetre expanding tous les `refit` semaines,
    forecast 1..refit pas en avant (causal)."""
    r = w['ret'].values * 100     # en %
    idx = w.index
    out = np.full(len(r), np.nan)
    # EGARCH n'a pas de forecast analytique multi-pas -> simulation
    method = 'simulation' if vol.lower() == 'egarch' else 'analytic'
    t = min_obs
    while t < len(r):
        try:
            am = arch_model(r[:t], vol=vol, p=p, q=q, dist=dist, mean='Constant')
            res = am.fit(disp='off', show_warning=False)
            h = min(refit, len(r) - t)
            f = res.forecast(horizon=h, reindex=False, method=method,
                             simulations=1000)
            var_path = f.variance.values[-1][:h]      # variance predite (%²)
            fc = np.sqrt(var_path) / 100 * np.sqrt(WPY)
            out[t:t+h] = fc
        except Exception:
            out[t:min(t+refit, len(r))] = np.nan
        t += refit
    return pd.Series(out, index=idx)


# ----------------------------------------------------------------------
# Horse race : qualite de prevision out-of-sample
# cible = vol realisee forward 4 semaines (proxy). QLIKE + RMSE sur variance.
# ----------------------------------------------------------------------
def forecast_scores(w, forecasts, fwd=4):
    # variance realisee forward (annualisee) : moyenne des ret² sur fwd semaines
    rv_fwd = (w['ret']**2).rolling(fwd).mean().shift(-fwd) * WPY
    rows = []
    for name, fc in forecasts.items():
        var_f = (fc**2)
        df = pd.concat([var_f.rename('f'), rv_fwd.rename('rv')], axis=1).dropna()
        df = df[(df['f'] > 0) & (df['rv'] > 0)]
        qlike = np.mean(df['rv']/df['f'] - np.log(df['rv']/df['f']) - 1)
        rmse = np.sqrt(np.mean((np.sqrt(df['f']) - np.sqrt(df['rv']))**2))
        corr = np.corrcoef(np.sqrt(df['f']), np.sqrt(df['rv']))[0, 1]
        rows.append({'forecaster': name, 'QLIKE': qlike, 'RMSE_vol': rmse,
                     'corr': corr, 'n': len(df)})
    return pd.DataFrame(rows).sort_values('QLIKE').reset_index(drop=True)


# ----------------------------------------------------------------------
# Moteur de vol targeting
# ----------------------------------------------------------------------
def run_voltarget(w, forecast, target_vol=0.15, cap=2.0, rf=RF,
                  borrow_spread=BORROW_SPREAD, tc=TC):
    df = pd.DataFrame(index=w.index)
    df['ret'] = w['ret']
    df['fc'] = forecast
    # poids decide en t (info <= t), applique au rendement t+1
    w_raw = target_vol / df['fc']
    df['w'] = w_raw.clip(0, cap).shift(1)      # <-- lag 1 (causal, pas de look-ahead)
    df = df.dropna(subset=['w', 'ret'])
    # jambe cash : (1-w) place/emprunte
    rate = np.where(df['w'] > 1, rf + borrow_spread, rf) / WPY
    cash_leg = (1 - df['w']) * rate
    # turnover & couts
    turn = df['w'].diff().abs().fillna(df['w'].abs())
    cost = turn * tc
    # rendement strategie (log approx -> simple pour l'equity)
    r_asset = np.expm1(df['ret'])              # rendement simple de QQQ
    df['strat'] = df['w'] * r_asset + cash_leg - cost
    df['bh'] = r_asset                         # buy & hold
    df['turn'] = turn
    return df


def metrics(ret, name, rf=RF):
    """ret : serie de rendements SIMPLES periodiques (hebdo)."""
    ret = ret.dropna()
    if len(ret) < WPY:
        return {'strategie': name, 'CAGR': np.nan, 'vol_ann': np.nan,
                'Sharpe': np.nan, 'Sortino': np.nan, 'max_DD': np.nan,
                'Calmar': np.nan, 'equity_finale': np.nan}
    eq = (1 + ret).cumprod()
    yrs = len(ret) / WPY
    cagr = eq.iloc[-1]**(1/yrs) - 1
    vol = ret.std() * np.sqrt(WPY)
    sharpe = (ret.mean()*WPY - rf) / vol if vol > 0 else np.nan
    downside = ret[ret < 0].std() * np.sqrt(WPY)
    sortino = (ret.mean()*WPY - rf) / downside if downside > 0 else np.nan
    dd = eq / eq.cummax() - 1
    maxdd = dd.min()
    calmar = cagr / abs(maxdd) if maxdd < 0 else np.nan
    return {'strategie': name, 'CAGR': cagr, 'vol_ann': vol, 'Sharpe': sharpe,
            'Sortino': sortino, 'max_DD': maxdd, 'Calmar': calmar,
            'equity_finale': eq.iloc[-1]}


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    w = load_weekly("/home/claude/qqq_weekly.csv")
    print(f"QQQ hebdo ajuste : {w.index[0].date()} -> {w.index[-1].date()} "
          f"({len(w)} semaines)\n")

    forecasts = {
        'Rolling std (13s)':  fc_rolling(w, 13),
        'EWMA (hl=6s)':       fc_ewma(w, 6),
        'Yang-Zhang (13s)':   fc_yang_zhang(w, 13),
        'GARCH(1,1)-t':       fc_garch(w, vol='Garch', dist='t'),
        'EGARCH(1,1)-t':      fc_garch(w, vol='EGARCH', dist='t'),
    }

    print("=== HORSE RACE : qualite de prevision (out-of-sample) ===")
    scores = forecast_scores(w, forecasts)
    print(scores.round(4).to_string(index=False))
    scores.to_csv("/home/claude/forecaster_scores.csv", index=False)

    print("\n=== BACKTEST VOL TARGETING (cible 15%, cap 2x, couts inclus) ===")
    rows = []
    bh_done = False
    equity = {}
    for name, fc in forecasts.items():
        bt = run_voltarget(w, fc, target_vol=0.15, cap=2.0)
        m = metrics(bt['strat'], name)
        m['turnover_an'] = bt['turn'].mean() * WPY
        m['levier_moyen'] = bt['w'].mean()
        rows.append(m)
        equity[name] = (1 + bt['strat']).cumprod()
        if not bh_done:
            mb = metrics(bt['bh'], 'Buy & Hold QQQ')
            mb['turnover_an'] = 0.0; mb['levier_moyen'] = 1.0
            rows.append(mb)
            equity['Buy & Hold QQQ'] = (1 + bt['bh']).cumprod()
            bh_done = True

    res = pd.DataFrame(rows)
    cols = ['strategie','CAGR','vol_ann','Sharpe','Sortino','max_DD','Calmar',
            'turnover_an','levier_moyen']
    print(res[cols].round(3).to_string(index=False))
    res.to_csv("/home/claude/backtest_results.csv", index=False)

    eqdf = pd.DataFrame(equity)
    eqdf.to_csv("/home/claude/equity_curves.csv")
    print("\nSaved -> forecaster_scores.csv, backtest_results.csv, equity_curves.csv")
