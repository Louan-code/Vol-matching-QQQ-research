"""
vol_signals.py
Construction d'un indice de volatilite implicite "model-free" facon CBOE (VIX/VXN)
a partir des options QQQ, + inversion Black-Scholes pour l'IV ATM.

Le forward est deduit par PARITE CALL-PUT -> aucune serie spot externe requise,
et les dividendes sont automatiquement incorpores.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq

R_FREE = 0.04  # taux sans risque approx (Fed funds ~4% en 2026)


# ----------------------------------------------------------------------
# 1) Chargement + snapshot quotidien (dernier prix traite de chaque contrat)
# ----------------------------------------------------------------------
def load_options(path):
    opt = pd.read_parquet(path)
    opt['expiry'] = pd.to_datetime(opt['expiry'])
    opt['date'] = opt['ts'].dt.normalize().dt.tz_localize(None)
    return opt


def daily_snapshot(opt, day):
    """Dernier close de chaque contrat sur la journee `day` (Timestamp)."""
    sub = opt[opt['date'] == day]
    if len(sub) == 0:
        return None
    last = sub.sort_values('ts').groupby('osi').tail(1).copy()
    last['dte'] = (last['expiry'] - day).dt.days
    return last


# ----------------------------------------------------------------------
# 2) Variance implicite model-free pour UNE expiry (formule CBOE)
# ----------------------------------------------------------------------
def implied_forward(chain):
    """F deduit par parite call-put au strike ou |C-P| est minimal."""
    piv = chain.pivot_table(index='strike', columns='opt_type',
                            values='close', aggfunc='last')
    if 'C' not in piv.columns or 'P' not in piv.columns:
        return None, None, None
    piv = piv.dropna(subset=['C', 'P'])
    if len(piv) == 0:
        return None, None, None
    diff = (piv['C'] - piv['P']).abs()
    k0 = diff.idxmin()
    T = chain['dte'].iloc[0] / 365.0
    F = k0 + np.exp(R_FREE * T) * (piv.loc[k0, 'C'] - piv.loc[k0, 'P'])
    return F, k0, piv


def mf_variance_one_expiry(chain):
    """Variance implicite annualisee (model-free) pour une expiry."""
    T = chain['dte'].iloc[0] / 365.0
    if T <= 0:
        return None
    F, _, piv = implied_forward(chain)
    if F is None or len(piv) < 5:
        return None

    strikes = piv.index.values
    # K0 = premier strike sous le forward
    below = strikes[strikes <= F]
    if len(below) == 0:
        return None
    K0 = below.max()

    # Construire le strip OTM : puts sous K0, calls au-dessus, moyenne a K0
    rows = []
    for K in strikes:
        if K < K0:
            q = piv.loc[K, 'P']
        elif K > K0:
            q = piv.loc[K, 'C']
        else:
            q = 0.5 * (piv.loc[K, 'C'] + piv.loc[K, 'P'])
        if np.isfinite(q) and q > 0:
            rows.append((K, q))
    if len(rows) < 5:
        return None
    ks = np.array([r[0] for r in rows])
    qs = np.array([r[1] for r in rows])

    # dK (differences centrees)
    dK = np.empty_like(ks)
    dK[1:-1] = (ks[2:] - ks[:-2]) / 2.0
    dK[0] = ks[1] - ks[0]
    dK[-1] = ks[-1] - ks[-2]

    contrib = np.sum(dK / ks**2 * np.exp(R_FREE * T) * qs)
    var = (2.0 / T) * contrib - (1.0 / T) * (F / K0 - 1.0)**2
    return var if var > 0 else None


# ----------------------------------------------------------------------
# 3) Indice 30 jours a maturite constante (interpolation near/next term)
# ----------------------------------------------------------------------
def vix_style_index(last, target_days=30, dte_min=7, dte_max=90):
    """Indice de vol implicite constant-maturity `target_days` (en %)."""
    exps = sorted(last['expiry'].unique())
    # calc variance par expiry eligible
    varmap = {}
    for exp in exps:
        chain = last[last['expiry'] == exp]
        dte = chain['dte'].iloc[0]
        if dte < dte_min or dte > dte_max:
            continue
        v = mf_variance_one_expiry(chain)
        if v is not None:
            varmap[dte] = v
    if len(varmap) == 0:
        return None
    dtes = np.array(sorted(varmap.keys()))
    # near = plus grand dte <= target, next = plus petit dte > target
    near_c = dtes[dtes <= target_days]
    next_c = dtes[dtes > target_days]
    if len(near_c) and len(next_c):
        d1, d2 = near_c.max(), next_c.min()
        v1, v2 = varmap[d1], varmap[d2]
        T1, T2 = d1/365.0, d2/365.0
        w1 = (d2 - target_days) / (d2 - d1)
        w2 = (target_days - d1) / (d2 - d1)
        var30 = (T1*v1*w1 + T2*v2*w2) * (365.0/target_days)
    else:
        # fallback: expiry la plus proche de target
        d = dtes[np.argmin(np.abs(dtes - target_days))]
        var30 = varmap[d]
    return 100.0 * np.sqrt(max(var30, 0))


# ----------------------------------------------------------------------
# 4) IV ATM par inversion Black-Scholes (signal plus simple/robuste)
# ----------------------------------------------------------------------
def bs_price(S, K, T, r, sigma, cp):
    if T <= 0 or sigma <= 0:
        return max(0.0, (S-K) if cp == 'C' else (K-S))
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if cp == 'C':
        return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
    return K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)


def implied_vol(price, S, K, T, r, cp):
    try:
        f = lambda s: bs_price(S, K, T, r, s, cp) - price
        if f(1e-4) * f(5.0) > 0:
            return np.nan
        return brentq(f, 1e-4, 5.0, maxiter=100)
    except Exception:
        return np.nan


def atm_iv_index(last, target_days=30, dte_min=7, dte_max=90):
    """IV ATM (BS) interpolee a `target_days`, en %."""
    exps = sorted(last['expiry'].unique())
    ivmap = {}
    for exp in exps:
        chain = last[last['expiry'] == exp]
        dte = chain['dte'].iloc[0]
        if dte < dte_min or dte > dte_max:
            continue
        F, k0, piv = implied_forward(chain)
        if F is None:
            continue
        T = dte/365.0
        S = F*np.exp(-R_FREE*T)  # spot ~ forward actualise
        # strike le plus proche de la monnaie, cote OTM
        strikes = piv.index.values
        Katm = strikes[np.argmin(np.abs(strikes - F))]
        cp = 'C' if Katm >= F else 'P'
        price = piv.loc[Katm, cp]
        iv = implied_vol(price, S, Katm, T, R_FREE, cp)
        if np.isfinite(iv):
            ivmap[dte] = iv
    if len(ivmap) == 0:
        return None
    dtes = np.array(sorted(ivmap.keys()))
    near_c = dtes[dtes <= target_days]; next_c = dtes[dtes > target_days]
    if len(near_c) and len(next_c):
        d1, d2 = near_c.max(), next_c.min()
        w1 = (d2-target_days)/(d2-d1); w2 = (target_days-d1)/(d2-d1)
        iv30 = ivmap[d1]*w1 + ivmap[d2]*w2
    else:
        d = dtes[np.argmin(np.abs(dtes-target_days))]
        iv30 = ivmap[d]
    return 100.0*iv30


# ----------------------------------------------------------------------
# 5) Pipeline : indice quotidien sur toute la periode
# ----------------------------------------------------------------------
def build_daily_iv(path):
    opt = load_options(path)
    days = sorted(opt['date'].unique())
    recs = []
    for day in days:
        last = daily_snapshot(opt, day)
        if last is None:
            continue
        F30 = None
        # forward ~30j pour validation
        near = last[(last['dte'] >= 20) & (last['dte'] <= 40)]
        if len(near):
            exp_near = near['expiry'].iloc[(near['dte']-30).abs().argmin()]
            Fd, _, _ = implied_forward(last[last['expiry'] == exp_near])
            T = (exp_near - day).days/365.0
            F30 = Fd*np.exp(-R_FREE*T) if Fd else None
        recs.append({
            'date': day,
            'qqq_vix_mf': vix_style_index(last),
            'qqq_iv_atm': atm_iv_index(last),
            'implied_spot_30d': F30,
        })
    return pd.DataFrame(recs).set_index('date')


if __name__ == '__main__':
    PATH = "/root/.claude/uploads/48c2869f-c186-50ec-b999-ce7ea916b72d/aea826c7-1792348732076_options_QQQ_15m.parquet"
    df = build_daily_iv(PATH)
    pd.set_option('display.width', 120)
    print(df.round(2).to_string())
    df.to_csv("/home/claude/qqq_iv_daily.csv")
    print("\nSaved -> qqq_iv_daily.csv")
