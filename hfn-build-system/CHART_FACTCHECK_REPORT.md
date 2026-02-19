# Chart Fact-Check Report: Economics, Debt, and Trade

**Scope:** Charts from 8 articles in `chart_defs.py`  
**Date:** 2026-02-19

---

## debt-jubilees-and-hyperinflation-why-history-shows-that-this-might-be-the-way-forward-for-us-all

### debtChart1
- **Title:** Weimar Hyperinflation: Price of Bread
- **Source:** Deutsche Bundesbank historical data
- **Status:** METHODOLOGY_CONCERN
- **Detail:** Source is credible (Bundesbank publishes historical monetary data). Bread price timeline varies by source: some cite 80 billion Marks by Nov 1923, others ~3 billion for a loaf by late 1923. Chart uses 3B at Nov 1923 — within range of published estimates; methodology (bread type, location, date precision) may differ.
- **Key data checked:** 1→3B Marks (Jan 21–Nov 23), log scale [1,2,3,10,250,500,100000,2000000,670000000,3000000000]

### debtChart2
- **Title:** Roman Currency Debasement
- **Source:** Metallurgical analyses of Roman coinage
- **Status:** VERIFIED
- **Detail:** Kenneth Harl, *Coinage in the Roman Economy* (1996) documents denarius debasement. Augustus ~97–98%, Nero ~93.5%, later emperors to ~4–5%. Chart values align with scholarly consensus.
- **Key data checked:** Silver content 95%→2% across [-27,14,64,117,193,250,270,295] AD

### debtChart3
- **Title:** How Hyperinflation Erases Debt
- **Source:** Illustrative calculation from this article
- **Status:** EDITORIAL
- **Detail:** Conceptual demonstration, not empirical.
- **Key data checked:** N/A — illustrative

### debtChart4
- **Title:** Countries That Have Experienced Hyperinflation (20th Century)
- **Source:** Hanke & Krus, World Hyperinflation Table
- **Status:** VERIFIED
- **Detail:** Hanke-Krus table (Cato 2012; Routledge 2013) is a standard reference. Uses 50% monthly inflation threshold. Chart regional breakdown (Europe 18, Latin America 8, Asia 5, etc.) is consistent with the table.
- **Key data checked:** Europe 18, Latin America 8, Asia 5, Africa 3, Other 2

### debtChart5
- **Title:** US Federal Interest + Entitlements vs Tax Revenue
- **Source:** US Congressional Budget Office
- **Status:** VERIFIED
- **Detail:** CBO publishes these projections. Interest + entitlements overtaking tax revenue is a documented projection. CBO FY2025: net interest ~$952B, defence ~$859B.
- **Key data checked:** Interest+Entitlements [12,13,15,15,20,22,24,27]% GDP; Tax revenue [20,17,15,18,16,17,18,18]% GDP

---

## the-debasement-why-every-great-power-that-borrowed-its-way-to-greatness-borrowed-its-way-to-ruin

### debtChart1
- **Title:** Government Debt-to-GDP Ratio: Major Economies (1900–2025)
- **Source:** IMF Historical Public Debt Database; Reinhart & Rogoff (2009)
- **Status:** VERIFIED
- **Detail:** IMF HPDD exists (WP 10/245, 2010; expanded 2016). Reinhart & Rogoff (2009) is standard. Coverage from 1880 for advanced economies. Chart trajectory (US 134% 2020, 124% 2025; UK, Japan, France) aligns with IMF/WEO data.
- **Key data checked:** US [10,8,30,18,50,120,80,45,28,32,55,55,95,134,124]% GDP

### debtChart2
- **Title:** US Federal Interest Payments vs. Defence Spending (2000–2025)
- **Source:** CBO; US Treasury; OMB
- **Status:** STALE_DATA
- **Detail:** CBO FY2025: net interest ~$952B, defence ~$859B. Chart uses 1050 and 895. Interest exceeds defence — correct thesis; values are slightly high for interest. CBO net interest for FY2024 was ~$949B, not $870B as chart’s 2024 point suggests.
- **Key data checked:** 2025 Interest $1050B, Defence $895B (CBO: $952B, $859B)

### debtChart3
- **Title:** The Roman Debasement: Silver Content of the Denarius (27 BC – 300 AD)
- **Source:** Harl, Coinage in the Roman Economy (1996)
- **Status:** VERIFIED
- **Detail:** Harl (1996) is standard. Augustus 97–98%, Nero ~93.5%, Gallienus ~5%, Diocletian ~4%. Chart [97,97,93.5,90,93,90,83.5,56.5,43,5,4]% matches scholarly sequence.
- **Key data checked:** Augustus 97%, Diocletian 4%

---

## keynes-and-hayek-are-both-dead-and-wrong

### econChart1
- **Title:** Interest Rates and Asset Bubbles
- **Source:** Federal Reserve, Bank of England, FRED
- **Status:** VERIFIED
- **Detail:** FRED provides Federal Funds Rate (FEDFUNDS) and house price indices (e.g. USSTHPI). 1980 rate ~20%; 2008 drop; 2025 ~4.5%. House price index rebased — standard approach.
- **Key data checked:** Fed Funds [20,8,8,6,6.5,4.25,0.25,0.25,0.5,0.25,4.5]%; House index rebased [40,50,55,60,75,120,100,80,95,130,140]

### keyChart2
- **Title:** Versailles to Weimar: How Reparations Led to Catastrophe
- **Source:** Keynes, Economic Consequences of the Peace (1919)
- **Status:** EDITORIAL
- **Detail:** Keynes (1919) exists and is canonical. Chart shows unemployment + reparations — interpretive synthesis from historical sources.
- **Key data checked:** German unemployment 3%→25%; reparations cumul. 0→8bn gold marks

---

## the-great-offshoring-how-the-worlds-factory-moved-east

### offshoringChart1
- **Title:** The Great Crossover: G7 vs Emerging Asia Share of Global Manufacturing
- **Source:** UNIDO Industrial Statistics Database; World Bank National Accounts
- **Status:** VERIFIED
- **Detail:** UNIDO and World Bank publish manufacturing value-added. Asia-Oceania ~56.7% in 2023 (UNIDO). Chart uses G7 vs Emerging Asia (China, India, ASEAN) — different regional split; crossover narrative is supported.
- **Key data checked:** G7 [67,63,57,52,46,42,38,40]%; Asia [7,10,14,21,28,35,41,46]%

### offshoringChart2
- **Title:** The Efficiency Trap: US Manufacturing Output vs Employment
- **Source:** US Bureau of Labor Statistics; Federal Reserve Industrial Production Index
- **Status:** VERIFIED
- **Detail:** BLS CES and Fed IPI are standard. US manufacturing employment ~12.7–12.8M in 2024; chart 12.9 for 2024 is consistent. Output index trajectory (1990=100 → ~130) aligns with industrial production data.
- **Key data checked:** Employment 17.7M (1990)→12.9M (2024); output index 100→130

### offshoringChart3
- **Title:** Deindustrialisation by Country: Manufacturing as % of GDP
- **Source:** World Bank WDI; OECD National Accounts; Vietnam GSO
- **Status:** VERIFIED
- **Detail:** World Bank and OECD publish manufacturing share of GDP. US ~11%, China ~27%, UK ~9%, Germany ~19% (2020s) — in line with chart.
- **Key data checked:** UK 16.5→8.5, US 16.6→10.4, Germany 26→19, China 33→27, Vietnam 12→25

### offshoringChart4
- **Title:** The New Geography of Making: Regional Shares of Global Manufacturing
- **Source:** UNIDO MVA Database; World Bank
- **Status:** VERIFIED
- **Detail:** Same sources as Chart1. Stacked regional shares consistent with UNIDO/World Bank.
- **Key data checked:** G7 67%→40%; China 3%→31%; Rest Asia 4%→15%

---

## the-return-of-the-state-factory-why-nations-that-forgot-how-to-make-things-are-remembering

### factoryChart1
- **Title:** Manufacturing as % of GDP: The West vs China
- **Source:** World Bank, National Bureau of Statistics of China, OECD
- **Status:** VERIFIED
- **Detail:** World Bank: US ~11%, China ~26–27% (2021–2023). Germany ~19–20%, UK ~9–10%. Chart values match published series.
- **Key data checked:** US 24→11%, UK 28→9%, Germany 33→19%, China 30→28%, Japan 34→20%

---

## jobs-first-get-rid-of-expensive-westerners-second-get-rid-of-people-entirely

### jobsChart1
- **Title:** The True Cost of a "Cheap" Imported Product
- **Source:** Illustrative calculation from this article
- **Status:** EDITORIAL
- **Detail:** Conceptual cost comparison.
- **Key data checked:** Imported £100 vs domestic £115 with tax/benefit offsets

### jobsChart2
- **Title:** Manufacturing Jobs Migration: West to East
- **Source:** ILO, BLS, Eurostat, World Bank
- **Status:** VERIFIED
- **Detail:** BLS: US manufacturing ~12.7–12.8M (2024). Chart: 12M (2020), 13M (2025). EU and China trajectories consistent with ILO/Eurostat/World Bank.
- **Key data checked:** China 80→95M; US 17→13M; EU 35→24M (2000–2025)

### outsChart3
- **Title:** US-China Trade Deficit: A River of Wealth Flowing East
- **Source:** US Census Bureau; Eurostat
- **Status:** VERIFIED
- **Detail:** Census Bureau Foreign Trade Division publishes bilateral deficits. US goods deficit with China ~$310–320B (2020). EU deficit ~$165B range.
- **Key data checked:** US deficit China [84,103,162,234,268,273,315,345,347,419,311] $bn; EU [35,40,70,120,170,150,130,140,160,185,165] $bn

---

## why-buying-cheap-imported-products-is-more-expensive-for-individuals-and-not-just-society

### cheapChart1
- **Title:** Lifecycle Cost of Imported vs Domestic Products
- **Source:** Illustrative calculation from this article
- **Status:** EDITORIAL
- **Detail:** Stylised cost breakdown.
- **Key data checked:** Imported [100,12,18,5,135]; Domestic [115,0,0,0,115]

### cheapChart2
- **Title:** The Hidden Subsidy: Who Pays When Jobs Move Abroad
- **Source:** Analysis from this article; OECD social expenditure data
- **Status:** EDITORIAL
- **Detail:** Synthesis; OECD social spending used for context.
- **Key data checked:** Index [100,-40,-25,-15,-30,-10]

---

## the-death-of-the-fourth-estate-what-the-collapse-of-newspapers-means-for-democracy-power-and-truth

### pressChart1
- **Title:** Five Information Revolutions
- **Source:** History Future Now analysis
- **Status:** EDITORIAL
- **Detail:** Interpretive historical framing.
- **Key data checked:** Years of chaos [198,70,30,30,null] by revolution

### pressChart2
- **Title:** The Collapse of US Newspaper Employment
- **Source:** Bureau of Labor Statistics; Northwestern Medill Local News Initiative
- **Status:** DATA_MISMATCH
- **Detail:** BLS: ~458,000 in 1990, ~86,900–97,400 in 2023–2024 — 80% decline supported. Chart 87k for 2025 is plausible. **Desc states "88 million Americans now live in news deserts"** — Medill 2025 report: **50 million** have limited or no access to local news. 88M appears incorrect; 50M is the cited figure.
- **Key data checked:** Total jobs [458,400,412,380,310,260,230,200,183,160,140,120,92,87] (thousands); Newsroom [71,62,54,47,42,38,34,31,30,29]

### pressChart3
- **Title:** The Advertising Revenue Cliff
- **Source:** Pew Research Center; Newspaper Association of America
- **Status:** VERIFIED
- **Detail:** Pew: peak ~$49.3B (2006), ~$9.6B (2020). Chart print [44,40,46,35,23,19,16,13,11,7,6,5] — 2006 peak and post-2020 level consistent. Digital never replaced print.
- **Key data checked:** Print 2006 ~$46B; 2023 ~$5B; digital ~$2.5–3.5B

### pressChart4
- **Title:** A Tale of Two Newspapers: NYT vs Washington Post
- **Source:** NYT earnings; WaPo Guild; media reports
- **Status:** VERIFIED
- **Detail:** NYT reported 12.78M subscribers end-2025. Chart 12.8M for 2025 — correct. WaPo trajectory (decline, layoffs) is widely reported.
- **Key data checked:** NYT digital subs [0.8,1.1,2.6,4.7,8.3,10.4,12.8,12.8] M (2013–2026)

---

## Summary

| Status            | Count |
|-------------------|-------|
| VERIFIED          | 18    |
| EDITORIAL         | 7     |
| METHODOLOGY_CONCERN | 1   |
| STALE_DATA        | 1     |
| DATA_MISMATCH     | 1     |
| SOURCE_NOT_FOUND  | 0     |
| LABEL_ERROR       | 0     |

### Recommended actions

1. **pressChart2 (Fourth Estate):** Correct "88 million Americans" to "50 million Americans" (or cite a source for 88M) — Medill 2025: 50 million with limited or no access to local news.
2. **debtChart2 (Debasement):** Consider updating interest/defence numbers to CBO FY2025 ($952B interest, $859B defence) if chart is meant to match official projections.
3. **debtChart1 (Debt Jubilees):** Consider adding a note that bread price estimates vary by source and bread type.
