import json
data = open("/home/claude/report_data.json").read()

HTML = r"""<meta name="claude:viewport-fit-sides" content="cover">
<title>Vol Targeting QQQ</title>
<style>
/* Layout: rapport technique une colonne, bandes pleine largeur, data en mono tabulaire */
:root{
  --bg:#f6f7f9; --surface:#ffffff; --surface2:#f0f2f5; --fg:#141922; --muted:#5a6676;
  --line:#e2e6ec; --accent:#0f766e; --accent-soft:#0f766e22; --bh:#b45309;
  --good:#15803d; --bad:#c2410c; --ddfill:#c2410c22;
  --grid:#141922; /* used via opacity in js */
  --f-disp:"Spectral",Georgia,serif;
  --f-body:"IBM Plex Sans",system-ui,sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0d1016; --surface:#151a22; --surface2:#1b222c; --fg:#e7eaf0; --muted:#97a2b2;
  --line:#242c38; --accent:#2dd4bf; --accent-soft:#2dd4bf1f; --bh:#f59e0b;
  --good:#4ade80; --bad:#fb923c; --ddfill:#fb923c22; --grid:#e7eaf0; color-scheme:dark;
}}
:root[data-theme="dark"]{
  --bg:#0d1016; --surface:#151a22; --surface2:#1b222c; --fg:#e7eaf0; --muted:#97a2b2;
  --line:#242c38; --accent:#2dd4bf; --accent-soft:#2dd4bf1f; --bh:#f59e0b;
  --good:#4ade80; --bad:#fb923c; --ddfill:#fb923c22; --grid:#e7eaf0; color-scheme:dark;
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--f-body);line-height:1.6;
  font-size:16px;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;
  padding-left:max(18px,env(safe-area-inset-left,0px));
  padding-right:max(18px,env(safe-area-inset-right,0px));padding-block:0}
h1,h2,h3{font-family:var(--f-disp);font-weight:600;text-wrap:balance;line-height:1.15;margin:0}
h1{font-size:clamp(2rem,5vw,3.1rem);letter-spacing:-.01em}
h2{font-size:clamp(1.5rem,3.5vw,2rem);margin-top:0}
h3{font-size:1.15rem;font-family:var(--f-body);font-weight:600}
p{margin:.6em 0}
a{color:var(--accent)}
.eyebrow{font-family:var(--f-mono);font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);margin:0 0 .5rem}
.lead{font-size:1.15rem;color:var(--muted);max-width:62ch}
.mono{font-family:var(--f-mono);font-variant-numeric:tabular-nums}
header.hero{padding-block:clamp(2.5rem,7vw,4.5rem) 2rem;border-bottom:1px solid var(--line)}
section{padding-block:2.6rem;border-bottom:1px solid var(--line)}
section:last-of-type{border-bottom:0}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:2rem}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 16px 14px}
.tile .k{font-family:var(--f-mono);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.tile .v{font-family:var(--f-disp);font-size:2rem;font-variant-numeric:tabular-nums;margin-top:4px;line-height:1}
.tile .s{font-size:.8rem;color:var(--muted);margin-top:6px}
.tile .v.good{color:var(--good)} .tile .v.bad{color:var(--bad)}
.chartbox{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 16px 12px;margin-top:1.3rem}
.chartbox h3{margin-bottom:.2rem}
.chartbox .cap{font-size:.85rem;color:var(--muted);margin:0 0 .8rem}
.cv{position:relative;width:100%;height:360px}
.cv.sm{height:300px}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:.7rem;font-size:.82rem;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.swatch{width:14px;height:3px;border-radius:2px;display:inline-block}
.tablewrap{overflow-x:auto;margin-top:1.2rem;border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:520px}
th,td{padding:10px 12px;text-align:right;border-bottom:1px solid var(--line);
  font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap}
th{font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500;
  background:var(--surface2);position:sticky;top:0}
th:first-child,td:first-child{text-align:left;font-family:var(--f-body)}
tbody tr:last-child td{border-bottom:0}
tr.best td{background:var(--accent-soft)}
tr.bh td{color:var(--muted)}
.pill{display:inline-block;font-family:var(--f-mono);font-size:.72rem;padding:2px 8px;border-radius:99px;
  border:1px solid currentColor}
.pill.g{color:var(--good)} .pill.b{color:var(--bad)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.card h3{margin-bottom:.4rem}
.note{background:var(--surface2);border-left:3px solid var(--accent);border-radius:0 10px 10px 0;
  padding:14px 18px;margin-top:1.2rem;font-size:.93rem}
.note b{font-family:var(--f-body)}
ol.steps{counter-reset:s;list-style:none;padding:0;margin:1.2rem 0 0}
ol.steps li{position:relative;padding:0 0 1rem 2.4rem;margin:0}
ol.steps li::before{counter-increment:s;content:counter(s);position:absolute;left:0;top:0;
  width:1.7rem;height:1.7rem;border-radius:50%;background:var(--accent);color:var(--bg);
  font-family:var(--f-mono);font-size:.85rem;display:flex;align-items:center;justify-content:center;font-weight:600}
ul.clean{margin:.5rem 0;padding-left:1.1rem}
ul.clean li{margin:.35rem 0}
.algo{border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-top:1rem}
.algo-row{display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center;
  padding:12px 16px;border-bottom:1px solid var(--line)}
.algo-row:last-child{border-bottom:0}
.algo-row .rank{font-family:var(--f-mono);color:var(--muted);font-size:.8rem}
.algo-row .name{font-weight:600}
.algo-row .name small{display:block;font-weight:400;color:var(--muted);font-size:.84rem;font-family:var(--f-body)}
.tag{font-family:var(--f-mono);font-size:.68rem;padding:3px 9px;border-radius:99px;white-space:nowrap}
.tag.done{background:var(--accent-soft);color:var(--accent)}
.tag.todo{background:var(--surface2);color:var(--muted)}
.themebtn{position:fixed;top:env(safe-area-inset-top,0px);right:max(14px,env(safe-area-inset-right,0px));
  margin-top:10px;z-index:20;background:var(--surface);border:1px solid var(--line);color:var(--fg);
  border-radius:99px;padding:7px 12px;font-family:var(--f-mono);font-size:.72rem;cursor:pointer}
footer{padding-block:2.4rem 3rem;color:var(--muted);font-size:.86rem}
code{font-family:var(--f-mono);font-size:.88em;background:var(--surface2);padding:1px 5px;border-radius:5px}
@media (max-width:720px){
  .tiles{grid-template-columns:repeat(2,1fr)}
  .grid2{grid-template-columns:1fr}
  .algo-row{grid-template-columns:auto 1fr;}
  .algo-row .tag{grid-column:2;justself:start;margin-top:-6px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>

<button class="themebtn" id="themebtn" aria-label="Changer de theme">clair / sombre</button>

<div class="wrap">
<header class="hero">
  <p class="eyebrow">Recherche quantitative &middot; QQQ &middot; 2001&ndash;2026</p>
  <h1>Volatility targeting sur QQQ</h1>
  <p class="lead">Dimensionner la position par la volatilit&eacute; pr&eacute;vue plut&ocirc;t que d'investir
  un montant fixe. 25 ans de backtest, 5 forecasters de vol compar&eacute;s, et un signal de vol
  implicite reconstruit &agrave; partir de tes donn&eacute;es d'options.</p>
  <div class="tiles" id="tiles"></div>
</header>

<section>
  <p class="eyebrow">L'id&eacute;e</p>
  <h2>Le principe en 30 secondes</h2>
  <p>Un buy &amp; hold garde 100&nbsp;% investi en permanence&nbsp;: ton <b>risque r&eacute;el</b> suit alors
  les humeurs du march&eacute; &mdash; faible quand c'est calme, &eacute;norme quand &ccedil;a panique. Le vol targeting
  inverse la logique&nbsp;: on fixe un niveau de risque cible (ici <b>15&nbsp;% de volatilit&eacute; annuelle</b>)
  et on ajuste la taille de la position pour s'y tenir.</p>
  <div class="note"><b>La formule tient en une ligne&nbsp;:</b>
  <span class="mono">poids = volatilit&eacute;_cible / volatilit&eacute;_pr&eacute;vue</span>, plafonn&eacute; &agrave; un levier
  maximum. Quand la vol pr&eacute;vue double, on divise l'exposition par deux. Tout le travail &mdash; et tout
  l'edge &mdash; se cache dans les trois mots <i>&laquo;&nbsp;volatilit&eacute; pr&eacute;vue&nbsp;&raquo;</i>.</p>
</section>

<section>
  <p class="eyebrow">R&eacute;sultat principal</p>
  <h2>25 ans, m&ecirc;me actif, deux g&eacute;om&eacute;tries</h2>
  <p>Chaque strat&eacute;gie rebalance chaque semaine, position d&eacute;cal&eacute;e d'une semaine (aucun
  look-ahead), co&ucirc;ts de transaction et de levier inclus. &Eacute;chelle logarithmique.</p>
  <div class="chartbox">
    <h3>Capital cumul&eacute; (base 1)</h3>
    <p class="cap">Vol targeting pilot&eacute; par Yang-Zhang vs buy &amp; hold, et deux autres forecasters.</p>
    <div class="cv"><canvas id="eqchart"></canvas></div>
    <div class="legend" id="eqlegend"></div>
  </div>
  <div class="chartbox">
    <h3>Drawdown (perte depuis le plus haut)</h3>
    <p class="cap">L&agrave; o&ugrave; le vol targeting gagne vraiment&nbsp;: il &eacute;vite les trous les plus profonds.</p>
    <div class="cv sm"><canvas id="ddchart"></canvas></div>
  </div>
  <div class="note"><b>Lecture.</b> Sur la fen&ecirc;tre 2001&ndash;2026, le buy &amp; hold encaisse
  <b>-69&nbsp;%</b> de drawdown (et m&ecirc;me <b>-83&nbsp;%</b> si l'on remonte au pic de 2000). La version
  Yang-Zhang plafonne &agrave; <b>-32&nbsp;%</b>, avec un <b>CAGR l&eacute;g&egrave;rement sup&eacute;rieur</b>
  (11,0&nbsp;% contre 10,6&nbsp;%) &mdash; &eacute;viter les trous profonds am&eacute;liore la composition.</p>
</section>

<section>
  <p class="eyebrow">Le tableau complet</p>
  <h2>Tous les forecasters, m&ecirc;me cible (15&nbsp;%, cap 2x)</h2>
  <div class="tablewrap"><table id="restable"></table></div>
  <p style="font-size:.85rem;color:var(--muted);margin-top:.8rem">
  Sharpe et Sortino calcul&eacute;s au-dessus d'un cash &agrave; 2&nbsp;%. Turnover = somme des variations de
  poids par an. Levier moyen&nbsp;: exposition moyenne (1 = 100&nbsp;% investi).</p>
</section>

<section>
  <p class="eyebrow">Quel estimateur de vol&nbsp;?</p>
  <h2>Le vrai nerf de la guerre&nbsp;: pr&eacute;voir la vol</h2>
  <p>On &eacute;value la qualit&eacute; de pr&eacute;vision de chaque mod&egrave;le contre la vol r&eacute;ellement
  r&eacute;alis&eacute;e les 4 semaines suivantes. Le <b>QLIKE</b> est la mesure de r&eacute;f&eacute;rence
  acad&eacute;mique (plus bas = meilleur)&nbsp;; la corr&eacute;lation mesure l'alignement du signal.</p>
  <div class="tablewrap"><table id="sctable"></table></div>
  <div class="note"><b>Le gagnant.</b> <b>Yang-Zhang</b> (estimateur de range OHLC) remporte &agrave; la fois
  la pr&eacute;cision pure (meilleur QLIKE) <i>et</i> le backtest (meilleur Sharpe et Calmar). Il exploite
  haut/bas/ouverture de chaque barre, pas seulement le close &mdash; d'o&ugrave; sa finesse. &Agrave; surveiller
  tout de m&ecirc;me&nbsp;: <b>GARCH</b> tourne deux fois moins (turnover&nbsp;1,1x/an contre&nbsp;1,7x), donc
  co&ucirc;te moins cher &mdash; un atout qui peut le faire repasser devant avec des co&ucirc;ts plus &eacute;lev&eacute;s
  ou un rebalancement plus fr&eacute;quent.</p>
</section>

<section>
  <p class="eyebrow">Comportement en crise</p>
  <h2>Ce qui se passe quand &ccedil;a casse</h2>
  <p>Levier moyen pris par la strat&eacute;gie Yang-Zhang pendant les quatre grands krachs, et performance
  compar&eacute;e au buy &amp; hold sur la fen&ecirc;tre.</p>
  <div class="tablewrap"><table id="crtable"></table></div>
  <div class="note"><b>La limite honn&ecirc;te.</b> Le vol targeting brille dans les baisses
  <i>progressives</i>&nbsp;: sur le dot-com (-22&nbsp;% contre -62&nbsp;%) et en 2022 (-23&nbsp;% contre
  -34&nbsp;%), il a divis&eacute; la perte par deux ou trois. Mais sur un krach <i>brutal</i> comme le COVID
  (mars&nbsp;2020), l'estimateur de vol, par nature retard&eacute;, n'a pas eu le temps de couper avant la
  chute &mdash; et a m&ecirc;me l&eacute;g&egrave;rement sous-perform&eacute; (-17&nbsp;% contre -14&nbsp;%)
  en se d&eacute;sexposant pr&egrave;s du creux. C'est exactement le probl&egrave;me que le signal de vol
  <i>implicite</i> ci-dessous cherche &agrave; r&eacute;soudre.</p>
</section>

<section>
  <p class="eyebrow">Tes donn&eacute;es d'options</p>
  <h2>Un &laquo;&nbsp;VXN maison&nbsp;&raquo; reconstruit sur QQQ</h2>
  <p>&Agrave; partir de ton fichier d'options 15-min, j'ai reconstruit un indice de volatilit&eacute;
  implicite <b>model-free</b> (la m&eacute;thodologie exacte du VIX du CBOE)&nbsp;: une variance synth&eacute;tique
  &agrave; 30 jours extraite de tout l'&eacute;ventail d'options hors de la monnaie. Contrairement &agrave; la
  vol r&eacute;alis&eacute;e qui regarde le pass&eacute;, c'est un signal <b>tourn&eacute; vers l'avenir</b>.</p>
  <div class="chartbox">
    <h3>Volatilit&eacute; implicite vs r&eacute;alis&eacute;e &middot; sept&ndash;oct 2026</h3>
    <p class="cap">QQQ-VIX model-free et IV ATM (axe gauche, %), prix QQQ (axe droit).</p>
    <div class="cv sm"><canvas id="ivchart"></canvas></div>
    <div class="legend" id="ivlegend"></div>
  </div>
  <div class="grid2" style="margin-top:1.3rem">
    <div class="card">
      <h3>&Ccedil;a se valide tout seul</h3>
      <p>Le prix spot de QQQ que je d&eacute;duis des options <b>par parit&eacute; call-put</b> colle au
      close r&eacute;el &agrave; <b>~0,2&nbsp;%</b> pr&egrave;s (703,2 vs 704,7 le 16/09&nbsp;; 709,4 vs 709,8
      le 16/10). Aucune donn&eacute;e externe n'est n&eacute;cessaire&nbsp;: les options se suffisent &agrave;
      elles-m&ecirc;mes, dividendes inclus.</p>
    </div>
    <div class="card">
      <h3>La prime de risque de volatilit&eacute;</h3>
      <p>Sur la p&eacute;riode, le QQQ-VIX moyen (<span class="mono" id="vrp-vix"></span>) d&eacute;passe la vol
      r&eacute;alis&eacute;e (<span class="mono" id="vrp-rv"></span>) d'environ <b><span id="vrp-gap"></span>&nbsp;points</b>.
      C'est la fameuse VRP&nbsp;: l'implicite <b>surestime</b> syst&eacute;matiquement le r&eacute;alis&eacute;.
      D'o&ugrave; l'ajustement <span class="mono">&times;&nbsp;0,85</span> avant de l'utiliser comme forecast.</p>
    </div>
  </div>
  <div class="note"><b>Honn&ecirc;tet&eacute; statistique.</b> 23 jours de donn&eacute;es sont beaucoup trop
  courts pour <i>mesurer</i> un pouvoir pr&eacute;dictif (ce serait du bruit). Ce que je montre ici, c'est que
  le <b>pipeline fonctionne et se valide</b>, que les niveaux sont coh&eacute;rents, et que le signal <b>a
  r&eacute;agi</b> &agrave; la tension du 14&ndash;16 octobre (implicite &agrave; 27&nbsp;% quand QQQ chute).
  La valeur pr&eacute;dictive de l'implicite est, elle, solidement &eacute;tablie dans la litt&eacute;rature&nbsp;:
  le code est pr&ecirc;t &agrave; l'exploiter d&egrave;s que tu disposes d'un historique d'options plus long.</p>
</section>

<section>
  <p class="eyebrow">Robustesse</p>
  <h2>Et si on change la cible&nbsp;?</h2>
  <p>Sensibilit&eacute; du Sharpe et du drawdown selon la cible de vol et le cap de levier (forecaster GARCH).</p>
  <div class="tablewrap"><table id="senstable"></table></div>
  <div class="note"><b>Le point cl&eacute;.</b> Le Sharpe reste <b>stable autour de 0,65</b> quelle que soit
  la cible&nbsp;: la cible ne cr&eacute;e pas la performance, elle choisit seulement <i>ton point</i> sur la
  fronti&egrave;re risque/rendement. 10&nbsp;% &rarr; d&eacute;fensif (-26&nbsp;% de DD max), 20&nbsp;% &rarr;
  agressif (-48&nbsp;%). Le cap ne mord qu'aux cibles &eacute;lev&eacute;es.</p>
</section>

<section>
  <p class="eyebrow">Pour aller plus loin</p>
  <h2>Le menu d'algos &agrave; tester</h2>
  <p>Du plus simple au plus pointu. Les signaux marqu&eacute;s <span class="tag done">impl&eacute;ment&eacute;</span>
  sont dans le code livr&eacute;&nbsp;; les autres sont les prochaines pistes, par ordre de rendement
  attendu sur l'effort.</p>
  <div class="algo" id="algolist"></div>
</section>

<section>
  <p class="eyebrow">M&eacute;thodologie &amp; limites</p>
  <h2>Ce qu'il faut savoir avant d'y croire</h2>
  <div class="grid2">
    <div class="card">
      <h3>Choix de donn&eacute;es</h3>
      <ul class="clean">
        <li>Backtest sur donn&eacute;es <b>hebdomadaires</b> (close ajust&eacute; splits+dividendes) &mdash;
        le fichier options ne couvrant qu'un mois, l'historique long vient de QQQ.</li>
        <li>Split <b>2:1 de mars 2000</b> correctement neutralis&eacute; (sinon faux -47&nbsp;% une semaine).</li>
        <li>Rebalancement hebdomadaire, cible 15&nbsp;%, cap 2x.</li>
      </ul>
    </div>
    <div class="card">
      <h3>Hypoth&egrave;ses &amp; r&eacute;serves</h3>
      <ul class="clean">
        <li>Co&ucirc;ts&nbsp;: 2&nbsp;bps par unit&eacute; de turnover, cash &agrave; 2&nbsp;%, spread
        d'emprunt 0,5&nbsp;% &mdash; constants (approximation&nbsp;: les taux ont beaucoup vari&eacute; depuis 1999).</li>
        <li>Taux sans risque de l'inversion BS fix&eacute; &agrave; 4&nbsp;%&nbsp;; faible impact &agrave; court terme.</li>
        <li>Prix d'option = close de la barre 15-min (pas de bid/ask dans les donn&eacute;es).</li>
        <li>Performances pass&eacute;es simul&eacute;es&nbsp;; aucune garantie future. Ceci n'est pas un conseil en investissement.</li>
      </ul>
    </div>
  </div>
</section>

<footer class="wrap">
  <p>Code Python fonctionnel livr&eacute; s&eacute;par&eacute;ment&nbsp;: <code>vol_signals.py</code>
  (VXN maison + IV), <code>backtest.py</code> (forecasters + moteur vol targeting),
  <code>enrichment.py</code> (sensibilit&eacute;, crises, signal IV). Donn&eacute;es&nbsp;: QQQ hebdo
  1999&ndash;2026 (Alpha Vantage) + ton fichier d'options 15-min.</p>
</footer>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('payload').textContent);
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const fmtPct = x => (x*100).toFixed(1)+'%';
const fmt2 = x => x.toFixed(2);

/* ---- tiles ---- */
const byName = {}; D.results.forEach(r=>byName[r.strategie]=r);
const g = byName['Yang-Zhang (13s)'], bh = byName['Buy & Hold QQQ'];
const tiles = [
  {k:'Sharpe (Yang-Zhang)', v:fmt2(g.Sharpe), s:'vs '+fmt2(bh.Sharpe)+' en buy & hold', cls:'good'},
  {k:'Drawdown max', v:fmtPct(g.max_DD), s:'vs '+fmtPct(bh.max_DD)+' en buy & hold', cls:'good'},
  {k:'CAGR', v:fmtPct(g.CAGR), s:'vs '+fmtPct(bh.CAGR)+' &mdash; plus haut, moins risqu&eacute;', cls:''},
  {k:'Volatilit&eacute; r&eacute;alis&eacute;e', v:fmtPct(g.vol_ann), s:'cible 15% &mdash; quasi atteinte', cls:''},
];
document.getElementById('tiles').innerHTML = tiles.map(t=>
  `<div class="tile"><div class="k">${t.k}</div><div class="v ${t.cls}">${t.v}</div><div class="s">${t.s}</div></div>`).join('');

/* ---- VRP numbers ---- */
document.getElementById('vrp-vix').textContent = D.vrp.vix_mean+'%';
document.getElementById('vrp-rv').textContent = D.vrp.rv_mean+'%';
document.getElementById('vrp-gap').textContent = (D.vrp.vix_mean-D.vrp.rv_mean).toFixed(1);

/* ---- results table ---- */
function table(el, cols, rows, rowClass){
  const thead = '<thead><tr>'+cols.map(c=>`<th>${c.h}</th>`).join('')+'</tr></thead>';
  const tb = '<tbody>'+rows.map(r=>{
    const cl = rowClass?rowClass(r):'';
    return `<tr class="${cl}">`+cols.map(c=>`<td>${c.f(r)}</td>`).join('')+'</tr>';
  }).join('')+'</tbody>';
  document.getElementById(el).innerHTML = thead+tb;
}
const order = ['Buy & Hold QQQ','Rolling std (13s)','EWMA (hl=6s)','Yang-Zhang (13s)','EGARCH(1,1)-t','GARCH(1,1)-t'];
const rrows = order.map(n=>byName[n]).filter(Boolean);
table('restable', [
  {h:'Strat&eacute;gie', f:r=>r.strategie},
  {h:'CAGR', f:r=>fmtPct(r.CAGR)},
  {h:'Vol', f:r=>fmtPct(r.vol_ann)},
  {h:'Sharpe', f:r=>fmt2(r.Sharpe)},
  {h:'Sortino', f:r=>fmt2(r.Sortino)},
  {h:'DD max', f:r=>fmtPct(r.max_DD)},
  {h:'Calmar', f:r=>fmt2(r.Calmar)},
  {h:'Turnover', f:r=>r.turnover_an.toFixed(1)+'x'},
  {h:'Levier', f:r=>r.levier_moyen.toFixed(2)},
], rrows, r=> r.strategie==='Yang-Zhang (13s)'?'best': (r.strategie==='Buy & Hold QQQ'?'bh':''));

/* ---- scores table ---- */
const scClean = D.scores.filter(s=>s.QLIKE!=null && isFinite(s.QLIKE));
table('sctable', [
  {h:'Forecaster', f:r=>r.forecaster},
  {h:'QLIKE &darr;', f:r=>fmt2(r.QLIKE)},
  {h:'RMSE vol', f:r=>r.RMSE_vol.toFixed(3)},
  {h:'Corr.', f:r=>fmt2(r.corr)},
], scClean, r=> r.forecaster==='Yang-Zhang (13s)'?'best':'');

/* ---- crises table ---- */
table('crtable', [
  {h:'Crise', f:r=>r.crise},
  {h:'Sem.', f:r=>r.semaines},
  {h:'Levier moy.', f:r=>r.levier_moyen.toFixed(2)},
  {h:'Levier min', f:r=>r.levier_min.toFixed(2)},
  {h:'Buy & hold', f:r=>fmtPct(r.perf_buyhold)},
  {h:'Strat&eacute;gie', f:r=>fmtPct(r.perf_strat)},
], D.crises, r=> r.perf_strat>r.perf_buyhold?'best':'bh');

/* ---- sensitivity table ---- */
const srows = D.sensitivity.filter(r=>r.strategie.includes('cap=1.0')||r.strategie.includes('cap=2.0'));
table('senstable', [
  {h:'Config', f:r=>r.strategie},
  {h:'CAGR', f:r=>fmtPct(r.CAGR)},
  {h:'Vol', f:r=>fmtPct(r.vol_ann)},
  {h:'Sharpe', f:r=>fmt2(r.Sharpe)},
  {h:'DD max', f:r=>fmtPct(r.max_DD)},
  {h:'Calmar', f:r=>fmt2(r.Calmar)},
  {h:'Levier', f:r=>r.lev.toFixed(2)},
], srows, r=> r.strategie==='tgt=15% cap=2.0'?'best':'');

/* ---- algo menu ---- */
const algos = [
  {r:'00', n:'Rolling std (close-to-close)', d:'Le point de d&eacute;part. &Eacute;cart-type glissant des rendements. Simple mais retard&eacute;.', t:'done'},
  {r:'01', n:'EWMA (RiskMetrics)', d:'Moyenne exponentielle&nbsp;: plus de poids au r&eacute;cent. Quasi gratuit, nettement mieux.', t:'done'},
  {r:'02', n:'Yang-Zhang (range OHLC)', d:'Exploite haut/bas/ouverture, pas juste le close. Le plus pr&eacute;cis des estimateurs historiques &mdash; vainqueur du backtest ici.', t:'done'},
  {r:'03', n:'GARCH(1,1)', d:'Mod&egrave;le de r&eacute;f&eacute;rence&nbsp;: mean-reversion + persistance + choc. Turnover le plus bas, donc le moins cher.', t:'done'},
  {r:'04', n:'EGARCH', d:'GARCH asym&eacute;trique (effet levier&nbsp;: la vol monte plus sur les baisses). Tr&egrave;s proche de GARCH ici.', t:'done'},
  {r:'05', n:'Vol implicite (VXN maison)', d:'Signal forward-looking extrait des options. Pipeline construit et valid&eacute; ; &agrave; backtester sur historique long.', t:'done'},
  {r:'06', n:'HAR-RV (realized vol intraday)', d:'Composantes multi-horizons (jour/semaine/mois). Le vrai standard institutionnel ; demande des donn&eacute;es intraday.', t:'todo'},
  {r:'07', n:'HAR-RV-J + saut', d:'S&eacute;pare la vol continue des sauts brutaux (annonces). +5 &agrave; 10% de pr&eacute;cision.', t:'todo'},
  {r:'08', n:'Blend r&eacute;alis&eacute; + implicite', d:'Combinaison 50/50 EWMA/HAR et IV ajust&eacute;e. Souvent aussi bon qu\'un GARCH complexe, plus robuste.', t:'todo'},
  {r:'09', n:'Skew & term structure d\'options', d:'Pente put/call et structure par &eacute;ch&eacute;ance comme signaux de stress anticip&eacute;. Exploite pleinement ton fichier.', t:'todo'},
  {r:'10', n:'Vol-of-vol & r&eacute;gimes (Markov)', d:'D&eacute;tection de r&eacute;gimes pour moduler cible et cap dynamiquement. Pointe de la recherche.', t:'todo'},
];
document.getElementById('algolist').innerHTML = algos.map(a=>
  `<div class="algo-row"><span class="rank">${a.r}</span>
   <span class="name">${a.n}<small>${a.d}</small></span>
   <span class="tag ${a.t}">${a.t==='done'?'impl&eacute;ment&eacute;':'&agrave; tester'}</span></div>`).join('');

/* ====================== CHARTS ====================== */
let charts=[];
function themeColors(){
  return {fg:css('--fg'),muted:css('--muted'),line:css('--line'),accent:css('--accent'),
          bh:css('--bh'),bad:css('--bad'),grid:css('--grid')};
}
function hexA(hex,a){ // accepts var color; fallback simple
  return hex; }
function buildCharts(){
  charts.forEach(c=>c.destroy()); charts=[];
  const C=themeColors();
  Chart.defaults.font.family=getComputedStyle(document.body).fontFamily;
  Chart.defaults.color=C.muted;
  const gridc = C.grid+'1a';
  const everyN=(arr,n)=>arr.map((v,i)=>i%n===0?v:'');

  /* equity (log) */
  const E=D.equity, lbl=D.dates;
  const eqSeries=[
    {k:'Buy & Hold QQQ', c:C.bh, w:2},
    {k:'Yang-Zhang (13s)', c:C.accent, w:2.4},
    {k:'GARCH(1,1)-t', c:C.muted, w:1.2},
    {k:'Rolling std (13s)', c:C.bad, w:1.2},
  ];
  charts.push(new Chart(document.getElementById('eqchart'),{
    type:'line',
    data:{labels:lbl, datasets:eqSeries.map(s=>({
      label:s.k,data:E[s.k],borderColor:s.c,borderWidth:s.w,pointRadius:0,tension:.05}))},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.dataset.label+': '+c.parsed.y.toFixed(2)+'x'}}},
      scales:{
        y:{type:'logarithmic',grid:{color:gridc},ticks:{color:C.muted,callback:v=>[0.5,1,2,5,10,20,50].includes(v)?v+'x':''}},
        x:{grid:{display:false},ticks:{color:C.muted,maxTicksLimit:9,autoSkip:true,
           callback:function(v){const d=this.getLabelForValue(v);return d?d.slice(0,4):''}}}}}}));
  document.getElementById('eqlegend').innerHTML=eqSeries.map(s=>
    `<span><i class="swatch" style="background:${s.c}"></i>${s.k.replace(' (13s)','').replace(' (hl=6s)','').replace('-t','')}</span>`).join('');

  /* drawdown */
  const DD=D.drawdown;
  const ddSeries=[{k:'Buy & Hold QQQ',c:C.bh},{k:'Yang-Zhang (13s)',c:C.accent}];
  charts.push(new Chart(document.getElementById('ddchart'),{
    type:'line',
    data:{labels:lbl,datasets:ddSeries.map(s=>({label:s.k,data:DD[s.k].map(x=>x*100),
      borderColor:s.c,borderWidth:1.6,pointRadius:0,fill:true,
      backgroundColor:s.c+'22',tension:.05}))},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{color:C.muted,boxWidth:12,boxHeight:3}},
        tooltip:{callbacks:{label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+'%'}}},
      scales:{y:{grid:{color:gridc},ticks:{color:C.muted,callback:v=>v+'%'},max:0},
        x:{grid:{display:false},ticks:{color:C.muted,maxTicksLimit:9,autoSkip:true,
           callback:function(v){const d=this.getLabelForValue(v);return d?d.slice(0,4):''}}}}}}));

  /* IV chart */
  const IV=D.iv;
  charts.push(new Chart(document.getElementById('ivchart'),{
    type:'line',
    data:{labels:IV.date,datasets:[
      {label:'QQQ-VIX (model-free)',data:IV.vix_mf,borderColor:C.accent,borderWidth:2.2,pointRadius:2,yAxisID:'y',tension:.2},
      {label:'IV ATM',data:IV.iv_atm,borderColor:C.muted,borderWidth:1.6,pointRadius:0,borderDash:[4,3],yAxisID:'y',tension:.2},
      {label:'Vol r&eacute;alis&eacute;e 10j',data:IV.rv10,borderColor:C.bad,borderWidth:1.4,pointRadius:0,yAxisID:'y',tension:.2},
      {label:'QQQ (prix)',data:IV.close,borderColor:C.bh,borderWidth:1.4,pointRadius:0,yAxisID:'y1',tension:.2}
    ]},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false}},
      scales:{
        y:{position:'left',grid:{color:gridc},ticks:{color:C.muted,callback:v=>v+'%'},title:{display:true,text:'Volatilit&eacute;',color:C.muted}},
        y1:{position:'right',grid:{display:false},ticks:{color:C.muted},title:{display:true,text:'QQQ',color:C.muted}},
        x:{grid:{display:false},ticks:{color:C.muted,maxTicksLimit:7,autoSkip:true,
           callback:function(v){const d=this.getLabelForValue(v);return d?d.slice(5):''}}}}}}));
  document.getElementById('ivlegend').innerHTML=[
    {n:'QQQ-VIX model-free',c:C.accent},{n:'IV ATM',c:C.muted},
    {n:'Vol r&eacute;alis&eacute;e 10j',c:C.bad},{n:'QQQ (prix)',c:C.bh}].map(s=>
    `<span><i class="swatch" style="background:${s.c}"></i>${s.n}</span>`).join('');
}
buildCharts();

/* ---- theme toggle ---- */
const root=document.documentElement, btn=document.getElementById('themebtn');
function cur(){const e=root.getAttribute('data-theme');if(e)return e;
  return matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}
btn.addEventListener('click',()=>{
  root.setAttribute('data-theme', cur()==='dark'?'light':'dark');
  requestAnimationFrame(buildCharts);
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{
  if(!root.getAttribute('data-theme')) buildCharts();
});
</script>
"""

html = HTML.replace("__DATA__", data)
with open("/home/claude/report.html","w") as f:
    f.write(html)
print("report.html written,", len(html), "bytes")
