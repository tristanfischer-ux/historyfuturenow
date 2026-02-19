# Chart Fact-Check Cross-Check Report

**Scope:** Data story charts, inter-article consistency, Batch 1 flags, map charts  
**Date:** 2026-02-19

---

## 1. Data Story Charts — Status

| Article / Slug | Headline | Status | Notes |
|----------------|----------|--------|-------|
| War | Nearly half of Soviet men aged 18-30 were killed in WW2 | ✅ VERIFIED | Chart data: 49%. Scholarly consensus (e.g. Ellman & Maksudov 1994) supports ~45–49% of Soviet males in 1923 birth cohort killed. |
| Renewables | Solar costs fell 99% in 40 years | ✅ VERIFIED | IRENA/BNEF: ~$106/W (1976) → ~$0.20/W (2024). 99% decline supported. |
| Revolutions | 60+ revolutions in 350 years | ✅ VERIFIED | revChart1 sums to 63 revolutions. Article catalog supports. |
| North Africa | North Africa will outnumber Southern Europe by 2030 | ✅ VERIFIED | Chart: N. Africa 245M, S. Europe 118M at 2030 (UN WPP). Article and nafChart1 align. |
| Covid | COVID accelerated deglobalisation by a decade | ⚠️ EDITORIAL | Interpretive claim; chart shows % changes (Trade -15%, Remote Work +300%, etc.). Not directly verifiable. |
| Debt Jubilees | A loaf of bread cost 3 billion Marks by 1923 | ✅ VERIFIED | Bundesbank/standard sources: Nov 1923 bread ~3B Marks. CHART_FACTCHECK_REPORT METHODOLOGY_CONCERN noted; headline accurate. |
| Rise of West | Western dominance was a 200-year anomaly | ✅ VERIFIED | Maddison/IMF data support ~1750–1950 peak. |
| Robotics | Robot costs falling below human labour | ⚠️ PROJECTION | Chart shows convergence; human labour not yet crossed. Headline forward-looking but defensible. |
| 150-Year Life | Human life expectancy: from 30 to 150 years | ⚠️ FUTURE | 150 years is speculative (2100?). Stone Age ~30, 2025 ~78 — verified. |
| Sex/Pleasure | South Korea: 0.72 children per woman | ⚠️ SLIGHTLY STALE | Statistics Korea 2023: 0.72. 2024 data (e.g. IDB) suggest ~0.68. Still lowest globally; minor staleness. |
| Tech War | Taiwan makes 63% of the world's advanced chips | ✅ VERIFIED | TSMC + others; industry estimates support ~60–70% for advanced nodes. |
| Young Continent | By 2100, Africa will have 4 billion people | ⚠️ FLAG | UN WPP 2024 medium variant: Africa ~2.9B by 2100 (revised down from 3.9B). 4B is high variant or older projection. Article text says 2.9B. **Inconsistent.** |
| Europe Rearms | €800 billion: Europe rearming at unprecedented speed | ✅ VERIFIED | NATO/EU figures for combined European defence spending support ~€800B range. |
| Fourth Estate | US newspaper jobs down 80% since 1990 | ✅ VERIFIED | BLS: ~458k (1990) → ~87k (2025). ~81% decline. |
| Great Emptying | No country has recovered from sub-1.5 fertility | ✅ VERIFIED | No nation has sustainably returned above 1.5 after falling below; demography literature supports. |
| India/Content | India made 78,500 content removal requests in 2024 | ⚠️ SOURCE CHECK | Needs verification against Meta/Google transparency reports. |
| Space | Launch costs fell from $54,500 to $200/kg | ✅ VERIFIED | SpaceX/Falcon 9 and historical NASA figures support order of magnitude. |
| Regulations | US federal regulations grew 18x since 1950 | ⚠️ METHODOLOGY | Depends on definition (CFR pages, rule count, etc.). Plausible but methodology-sensitive. |
| Factory | Manufacturing fell from 30% to 11% of US GDP | ✅ VERIFIED | BEA/World Bank: US manufacturing share declined as stated. |
| Gates | Foreign-born populations tripled since 1970 | ✅ VERIFIED | UN DESA, national census data support for US, UK, Germany, France. |
| Builders Dying | From 1 in 3 births to 1 in 15 — builder populations vanishing | ✅ VERIFIED | UN WPP share of global births for European-heritage + East Asian populations supports trajectory. |

---

## 2. Inter-Article Consistency

### Fertility and Population Metrics

| Metric | Article/Chart | Value | Consistency |
|--------|---------------|-------|-------------|
| South Korea TFR | Great Divergence, Locked Gate, heroFertility, sexChart2 | 0.72 | ✅ Consistent across all |
| China TFR | heroFertility / sexChart2 | 1.09 | ⚠️ emptyingMap/cradleMap use 1.02 | Minor inter-chart difference (same source vintage can vary). |
| Italy TFR | Locked Gate, emptyChart3, heroFertility | 1.20–1.24 | ✅ Consistent |
| Africa 2100 | Young Continent (text) | 2.9 billion | ⚠️ heroWinners (data story) | 4 billion — **inconsistent**. Text uses UN WPP 2024 medium; chart uses high/older projection. |

### Shared Sources (UN WPP)

- **naChart5** (North Africa): Source "UN World Population Prospects 2022" — **STALE**. Should cite WPP 2024.
- **sexChart2** (Fertility): Source "UN WPP 2022" — **STALE**. Should cite WPP 2024.
- **cradleChart4, cradleChart5, emptyingMap, cradleMap**: UN WPP 2024 — current.

**Recommendation:** Update naChart5 and sexChart2 sources to UN WPP 2024 and refresh data if needed.

---

## 3. Refined Assessment of Batch 1 Flags

### DATA_MISMATCH

| Chart | Original Flag | Web Check | Refined Assessment |
|-------|---------------|-----------|--------------------|
| **emptyChart3** (Malta) | Empty chart / Malta data | Eurostat 2023: Malta TFR 1.06. Chart: 1.08. | **RESOLVED** — 1.08 within rounding. Eurostat 2024 not yet published. No action. |
| **emptyChart5** (Marriage age) | Marriage age | ONS: England & Wales mean age first marriage 2020 — Males 32.1, Females 30.7. Chart: 32.1, 30.7. | **RESOLVED** — Data matches ONS. |
| **cradleChart6** (Pro-natalist) | Pro-natalist policy outcomes | Hungary 1.23→1.53, France 1.73→1.68 (decline), Sweden 1.85→1.45 (decline), Israel 2.95→2.90. Chart shows before/after. | **NOTE** — France and Sweden *declined* despite policy. Chart accurately shows "ambitious policy moves the needle" is mixed; Hungary up, others flat/down. Methodology fine; narrative could clarify. |
| **pressChart2** (88 vs 50 million) | Desc: "88 million Americans now live in news deserts" | Medill 2025: **50 million** have limited or no access to local news. | **CONFIRMED** — Correct "88 million" to "50 million" in chart desc. |

### STALE_DATA

| Chart | Original Flag | Web Check | Refined Assessment |
|-------|---------------|-----------|--------------------|
| **sexChart2** | UN WPP 2022 | UN WPP 2024 available. South Korea 2024 may be 0.68. | **CONFIRMED** — Update source to UN WPP 2024; consider refreshing TFR values. |
| **naChart5** | UN WPP 2022 | UN WPP 2024 available. Algeria/Italy age pyramids likely similar. | **CONFIRMED** — Update source to UN WPP 2024. |

### METHODOLOGY_CONCERN

| Chart | Original Flag | Web Check | Refined Assessment |
|-------|---------------|-----------|--------------------|
| **emptyChart4** | BLS CPI: hospital +230%, tuition +180%, childcare +142%, wages +85% | BLS CPI categories: Medical Care, College Tuition, Childcare, Wages. Order of magnitude consistent. | **ACCEPTABLE** — Methodology (CPI categories, baseline year) may vary; values plausible. Add footnote if desired. |
| **cradleChart4** | Heritage-adjusted European/East Asian birth share | Source cites UN WPP, CDC, Eurostat, ONS, heritage-adjusted. | **ACCEPTABLE** — Heritage adjustment is interpretive; methodology disclosed. |
| **housingChart1** | OECD/ONS price-to-income | OECD affordability data supports general trajectory. | **ACCEPTABLE** — Values in line with published series. |

### Additional Flags (User-Specified)

| Chart | Flag | Web Check | Refined Assessment |
|-------|------|-----------|--------------------|
| **mineralsChart1** | Rare Earths 90 vs 98% | IEA 2024: China **98%** of rare earth *refining*. Chart: 90%. | **UPDATE RECOMMENDED** — Raise Rare Earths from 90% to 98% to match IEA. Chart title says "Processing" which aligns with refining. |
| **renChart3** | Battery $139 vs $115 | BNEF: 2023 $139/kWh; 2024 **$115/kWh** (Dec 2024 survey). | **STALE_DATA CONFIRMED** — Chart 2024 point is $139 (2023 figure). Update to $115 for 2024. |

---

## 4. Map Chart Verification Summary

| Map | Article | Source | Spot Check | Assessment |
|-----|---------|--------|------------|------------|
| **emptyingMap** | Great Emptying | UN WPP 2024 | South Korea 0.72, China 1.02, Italy 1.24, Japan 1.20, Germany 1.35, Nigeria 5.10 | ✅ Plausible vs UN WPP 2024 |
| **cradleMap** | Empty Cradle | UN WPP 2024 | Same TFR dataset as emptyingMap | ✅ Plausible |
| **buildersMap** | Builders Dying | UN WPP 2024 | Japan -17%, China -13%, India +12%, Nigeria +54% (2025–2050) | ✅ Aligns with UN WPP medium variant |
| **rearmsMap** | Europe Rearms | SIPRI 2025; NATO | Poland 4.2%, Estonia 3.4%, US 3.4%, Ukraine 26% | ✅ In line with SIPRI/NATO (2024/2025) |
| **gatesMap** | Gates of Nations | UN DESA 2024; OECD | UAE 88%, Qatar 77%, Kuwait 72%, UK 14%, Germany 18% | ✅ Plausible vs UN migrant stock |
| **renewablesMap** | Renewables | Ember 2024; IEA | Norway 98%, Brazil 85%, UK 43%, US 22% | ✅ Plausible |
| **offshoringMap** | Great Offshoring | World Bank; UNIDO 2024 | China 28%, Vietnam 25%, Germany 19%, US 11% | ✅ Plausible |
| **northAfricaMap** | North African Threat | UN WPP | North Africa population/fertility | ✅ Consistent with nafChart data |
| **covidMap** | Covid Long-Term | Economist/WHO excess mortality | Russia ~800, US ~350, UK ~280, Japan ~150 | ✅ Order of magnitude consistent |
| **foodMap** | Climate/Food | Global Food Security Index 2024 | Finland 85, UK 82, US 80, Yemen ~20 | ✅ Plausible |
| **chinaColonialMap** | China Colonial | AidData; CARI; Refinitiv | Pakistan 62, Malaysia 25, Indonesia 15 | ✅ Plausible for BRI investment |
| **landDealsMap** | Land Deals Africa | Land Matrix; Grain | Sudan 4.0, Ethiopia 3.5, Mozambique 2.8 Mha | ✅ Plausible |

**Summary:** Map values are plausible against UN WPP, SIPRI, UN DESA, IEA, and similar datasets. No major discrepancies found.

---

## 5. Recommended Actions (Prioritised)

1. **pressChart2** — Change "88 million" to "50 million" in chart `desc` (Medill 2025).
2. **renChart3** — Update 2024 battery cost from $139 to $115/kWh (BNEF Dec 2024).
3. **mineralsChart1** — Update Rare Earths China share from 90% to 98% (IEA 2024).
4. **heroWinners** — Align "4 billion" with article text: use "2.9 billion" (UN WPP 2024 medium) or cite high variant explicitly.
5. **naChart5, sexChart2** — Update source to UN WPP 2024; refresh data if needed.
6. **China TFR** — Consider aligning heroFertility/sexChart2 (1.09) with map (1.02) for consistency; both within UN range.
