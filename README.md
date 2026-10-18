# QQQ — Volatility Targeting

Étude quantitative d'une stratégie de *volatility targeting* (dimensionnement de
position par la volatilité prévue) sur l'ETF QQQ, avec comparaison de plusieurs
estimateurs de volatilité et intégration d'un signal de **volatilité implicite**
reconstruit à partir de données d'options.

> ⚠️ Travail de recherche / backtest. Performances simulées, nettes de frais
> *hypothétiques*. Ceci n'est pas un conseil en investissement.

---

## TL;DR

- Le vol targeting **régule le risque, pas le rendement** : il transforme un
  parcours à ‑70 % de drawdown (buy & hold) en un parcours à ‑30 %, pour un
  **Sharpe quasi doublé** (0,48 → 0,62 sur 2001‑2026).
- **La prévision de vol est le seul edge.** Classement de précision (QLIKE,
  out-of-sample) : **HAR‑RV > Yang‑Zhang > EWMA > GARCH > rolling std**… mais la
  précision ne vaut rien si elle n'est pas *tradable* : HAR‑RV brut en daily
  génère **25x de turnover/an** et se fait manger par les frais. Lissé, il
  redevient compétitif.
- **Les options = une assurance ciblée.** Le signal de vol implicite ne paie
  qu'autour des chocs (COVID : drawdown ‑17 % vs ‑28 % pour le buy & hold) et
  n'apporte quasi rien en marché calme.
- **Levier & cible ne créent rien** : ils déplacent le long de la droite
  risque/rendement, Sharpe constant. Un x2 double le CAGR (11 % → 18 %) mais
  aussi le drawdown (‑32 % → ‑57 %).

---

## Structure du dépôt

```
src/
  vol_signals.py        VXN-maison (vol implicite model-free, méthode CBOE) + IV ATM
  backtest.py           Backtest hebdomadaire 1999-2026, forecasters + moteur vol targeting
  make_outputs.py       Consolidation fenêtre commune + export JSON du rapport
  enrichment.py         Sensibilité (cible × cap), comportement en crise, signal IV
  backtest_intraday.py  Backtest DAILY sur barres 5-min (HAR-RV, GARCH, Yang-Zhang)
  backtest_combined.py  Vol réalisée + implicite (blend, HAR-IV) sur 2020-2022
  build_report.py       Génère le rapport HTML interactif
data/
  qqq_weekly.csv        QQQ hebdo ajusté 1999-2026 (Alpha Vantage) — reproductible
  qqq_daily_recent.csv  QQQ daily récent (~100j)
results/
  *.csv                 Tables de résultats (backtests, scores, sensibilité, crises)
  equity_curve*.png     Courbes d'equity des 3 études
  report.html           Rapport vulgarisé interactif
```

Les données volumineuses / propriétaires (options parquet, QQQ 5-min brut, flux
d'options) sont **git-ignorées** — voir `data/README.md` pour les régénérer.

---

## Les trois études

### 1. Backtest long — hebdomadaire, 2001‑2026 (`backtest.py`, `make_outputs.py`)

Rebalancement hebdomadaire, cible 15 %, cap 2x, position décalée d'une semaine
(causale). 5 forecasters comparés.

| Stratégie | CAGR | Vol | Sharpe | DD max | Calmar | Turnover |
|---|---|---|---|---|---|---|
| Buy & Hold QQQ | 10,6 % | 22,4 % | 0,47 | ‑69,3 % | 0,15 | — |
| Rolling std | 10,2 % | 17,0 % | 0,54 | ‑37,0 % | 0,28 | 3,1x |
| EWMA | 10,4 % | 16,0 % | 0,58 | ‑34,8 % | 0,30 | 2,5x |
| **Yang‑Zhang** | **11,0 %** | 15,7 % | **0,62** | **‑32,4 %** | **0,34** | 1,7x |
| GARCH(1,1) | 10,4 % | 15,2 % | 0,59 | ‑37,4 % | 0,28 | 1,1x |
| EGARCH | 10,4 % | 15,1 % | 0,60 | ‑36,3 % | 0,29 | 1,4x |

Horse race (QLIKE, plus bas = mieux) : Yang‑Zhang (0,46) > EWMA > GARCH > rolling.

### 2. Backtest intraday — DAILY sur barres 5‑min, 2020‑2026 (`backtest_intraday.py`)

L'intraday permet de calculer la *realized variance* (gap overnight inclus) et de
rebalancer en daily (horizon de prévision = fréquence de rebalancement).

| Stratégie | CAGR | Vol | Sharpe | DD max | Calmar | Turnover |
|---|---|---|---|---|---|---|
| Buy & Hold QQQ | 15,2 % | 22,3 % | 0,61 | ‑35,6 % | 0,43 | — |
| Yang‑Zhang | 12,6 % | 15,9 % | **0,64** | ‑25,4 % | 0,50 | 5,3x |
| GARCH(1,1) | 11,5 % | 13,8 % | **0,64** | **‑19,1 %** | **0,60** | 6,2x |
| HAR‑RV (brut) | 10,3 % | 16,4 % | 0,50 | ‑27,4 % | 0,38 | **25,7x** |
| HAR‑RV lissé | 12,2 % | 16,3 % | 0,61 | ‑27,0 % | 0,45 | 5,9x |

Horse race : **HAR‑RV gagne nettement** (QLIKE 0,30 vs 0,35 YZ vs 0,41 GARCH) —
mais son turnover brut (25,7x) détruit sa performance. Le lissage (EWMA span 10)
divise le turnover par ~4 et le rend compétitif. *Le meilleur prédicteur n'est pas
la meilleure stratégie.*

### 3. Réalisée + implicite — 2020‑2022, inclut le COVID (`backtest_combined.py`)

Signal de vol implicite (VXN‑maison) reconstruit depuis les options 4h, intégré
de 3 façons : IV pur, blend (60 % HAR + 40 % IV×0,85), et HAR‑IV (régression).

**Pendant le krach COVID**, seul le signal implicite pouvait agir (HAR/GARCH
encore en warmup) :

| | Perf | Drawdown max | Levier moyen |
|---|---|---|---|
| Buy & Hold QQQ | ‑6,6 % | ‑28,4 % | 1,00 |
| **IV pur** | ‑7,7 % | **‑17,3 %** | 0,45 |

L'implicite s'est désexposé **tôt** (il a flairé 40‑75 % de vol avant les gros
mouvements de prix) et a quasiment divisé le drawdown par deux. Sur le reste de la
période (bull), son apport est marginal.

---

## Méthodologie — points clés

- **Causalité stricte** : le poids décidé en `t` s'applique au rendement `t+1`.
  Aucun look-ahead.
- **Frais déduits** : 2 bps par unité de turnover (proxy spread+commission) +
  coût du levier (emprunt au taux cash + 0,5 % quand poids > 1).
- **Split QQQ 2:1 de mars 2000** neutralisé (close ajusté), sinon faux ‑47 %.
- **Vol implicite** : méthode model-free du CBOE (variance synthétique 30j sur
  tout le strip d'OTM). Le forward est déduit par **parité call-put** → aucune
  série spot externe requise, dividendes inclus. Validé : le spot implicite colle
  au close réel à ~0,2‑0,4 %. Ajustement `×0,85` pour retirer la prime de risque
  de volatilité (~6 pts mesurés).
- **Les options ne sont jamais tradées** : elles servent de *capteur* de vol
  anticipée ; seul QQQ est acheté.

## Limites

- Données hebdo pour le backtest long (daily/intraday long = premium Alpha Vantage).
- La conclusion **dépend du régime** : le vol targeting gagne en absolu quand il y
  a de vrais krachs (dot-com, 2008) ; sur un bull (2020‑2026) le buy & hold gagne
  en rendement brut, le vol targeting en risque ajusté.
- Un seul COVID dans l'échantillon d'options ≠ preuve statistique de l'edge implicite.
- Coûts de transaction = hypothèse à calibrer sur les coûts réels ; slippage,
  impact de marché et taxes non modélisés.

---

## Reproduire

```bash
pip install -r requirements.txt

python src/backtest.py          # backtest hebdo + horse race
python src/make_outputs.py      # consolidation fenêtre commune + report_data.json
python src/enrichment.py        # sensibilité, crises, signal IV
python src/backtest_intraday.py # backtest daily 5-min (nécessite les données 5-min)
python src/backtest_combined.py # réalisée + implicite (nécessite options + IV)
python src/build_report.py      # rapport HTML
```

> **Note chemins** : les scripts utilisent des chemins absolus de la session
> d'origine (`/home/claude/...`). À adapter en chemins relatifs du dépôt avant
> exécution.

### Sources de données
- **QQQ hebdo/daily** : Alpha Vantage (`TIME_SERIES_WEEKLY_ADJUSTED`,
  `TIME_SERIES_DAILY`). `qqq_weekly.csv` est fourni.
- **QQQ 5-min & options** (non commitées) : à fournir séparément
  (Polygon, Databento, ou équivalent). Voir `data/README.md`.
