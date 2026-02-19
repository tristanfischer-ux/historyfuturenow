# Comprehensive Chart Fact-Check Report

**Audit date:** 19 February 2026  
**Scope:** ~200 charts across 57 articles in `chart_defs.py`  
**Method:** Multi-agent thematic fact-checking with source verification and data spot-checks

---

## Executive Summary

| Status | Count | Description |
|--------|-------|-------------|
| VERIFIED | 132 | Data checks out against cited sources |
| EDITORIAL | 44 | Analysis/illustrative; not externally verifiable |
| DATA_MISMATCH | 14 | Number in chart differs from source |
| METHODOLOGY_CONCERN | 20 | Source methodology unclear or values derived |
| STALE_DATA | 7 | Newer source edition available |
| LABEL_ERROR | 2 | Title or description misrepresents data |
| SOURCE_NOT_FOUND | 1 | Cited source not located |

**Key finding:** Most charts (66%) are verified or editorial. 14 charts require data corrections; 7 should update sources to current editions.

---

## Prioritised Corrections List

### High Priority — Data Corrections

1. **pressChart2** (the-death-of-the-fourth-estate)  
   - **Issue:** Chart desc states "88 million Americans in news deserts"  
   - **Correct:** Medill 2025 reports ~50 million  
   - **Action:** Change "88 million" to "50 million" in chart `desc`

2. **mineralsChart1** (the-new-oil)  
   - **Issue:** Rare Earths China share shown as 90%  
   - **Correct:** IEA 2024 reports ~98% of rare earth refining  
   - **Action:** Update 90% to 98% in chart data

3. **renChart3** (the-renewables-and-battery-revolution)  
   - **Issue:** 2024 battery cost shown as $139/kWh  
   - **Correct:** BNEF Dec 2024 survey reports $115/kWh  
   - **Action:** Update 2024 data point to $115

4. **newLitChart1** (the-new-literacy)  
   - **Issue:** Global literacy 2020 shown as 97%  
   - **Correct:** UNESCO/Our World in Data ~87–90%  
   - **Action:** Update to ~87–90%

5. **guiltChart2** (the-invisible-judge)  
   - **Issue:** CPI scores slightly off — Finland 87 vs 88, China 45 vs 43, Pakistan 24 vs 28  
   - **Action:** Align with Transparency International CPI 2024

6. **guiltChart3** (the-invisible-judge)  
   - **Issue:** Chart says "UK 5th" in GII; UK is 6th, Singapore 5th  
   - **Action:** Correct ranking label

7. **robotBargainChart1** (the-robot-bargain)  
   - **Issue:** Japan robot density 399 vs IFR 2024/2025 419  
   - **Action:** Update to 419

8. **platChart1 / platChart3** (platform-technologies)  
   - **Issue:** Inconsistent across charts — Telephone 75 vs 50 years; AI 0.5 vs 0.2 years  
   - **Action:** Reconcile definitions and numbers

### Medium Priority — Source Updates

9. **sexChart2** (lets-talk-about-sex)  
   - **Issue:** Source cites UN WPP 2022  
   - **Action:** Update to UN WPP 2024

10. **naChart5** (the-north-african-threat-and-mediterranean-reunification)  
    - **Issue:** Source cites UN WPP 2022  
    - **Action:** Update to UN WPP 2024

11. **utilChart1** (big-european-electricity-utilities)  
    - **Issue:** Data ends 2017 (8 years old)  
    - **Action:** Add current data or note age of dataset

12. **debtChart2** (the-debasement)  
    - **Issue:** Chart shows 2025 interest $1,050B vs defence $895B; CBO has $952B and $859B  
    - **Action:** Align with CBO FY2025 projections

### Low Priority — Clarifications

13. **heroWinners** (history-is-written-by-the-winners)  
    - **Issue:** Headline "4 billion" for Africa 2100; UN WPP 2024 medium variant ~2.9B  
    - **Action:** Use "2.9 billion" or cite high variant explicitly

14. **China TFR** — Minor inconsistency between articles (1.02 vs 1.09); align if desired

---

## Per-Article Breakdown

### Batch 1: Demographics and Fertility

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| the-great-emptying | 12 | 10 | emptyChart3 (Malta), emptyChart4 (methodology), emptyChart5 (marriage age) |
| lets-talk-about-sex | 3 | 2 | sexChart2 STALE_DATA |
| the-empty-cradle-bargain | 7 | 5 | cradleChart4 (methodology), cradleChart6 (data) |
| the-builders-are-dying | 11 | 10 | buildersChart4b (methodology) |
| a-nation-transformed | 6 | 5 | nationChart6 (methodology) |
| the-locked-gate | 3 | 2 | housingChart1 (methodology) |

### Batch 1: Geopolitics, Military, Migration

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| europe-rearms | 5 | 3 | rearmChart3 (Poland 4.7 vs 4.48), heroRearm EDITORIAL |
| why-china-could-invade-taiwan | 3 | 2 | twChart2 METHODOLOGY_CONCERN |
| the-gates-of-nations | 4 | 4 | — |
| what-the-history-of-immigration | 3 | 2 | immChart3 EDITORIAL |
| the-north-african-threat | 7 | 5 | naChart5 STALE_DATA, nafChart4 EDITORIAL |
| the-severed-circuit | 3 | 1 | techwarChart2, techwarMapChart EDITORIAL |
| the-great-divergence | 3 | 3 | — |
| why-do-we-need-the-military | 2 | 1 | milChart2 (Hormuz 21 vs ~20.3) |

### Batch 1: Economics, Debt, Trade

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| the-debasement | 3 | 2 | debtChart2 STALE_DATA |
| debt-jubilees-and-hyperinflation | 6 | 5 | debtChart1 METHODOLOGY_CONCERN (Weimar bread) |
| keynes-and-hayek | 2 | 1 | EDITORIAL |
| the-great-offshoring | 5 | 4 | EDITORIAL |
| the-return-of-the-state-factory | 2 | 1 | heroFactory EDITORIAL |
| jobs-first | 3 | 2 | EDITORIAL |
| why-buying-cheap-imported-products | 2 | 1 | EDITORIAL |
| the-death-of-the-fourth-estate | 5 | 4 | **pressChart2 DATA_MISMATCH (88 vs 50 million)** |

### Batch 1: Energy, Climate, Resources

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| the-renewables-and-battery-revolution | 9 | 7 | renChart3 STALE_DATA, renChart5 EDITORIAL |
| the-atom-returns | 3 | 3 | — |
| the-new-oil | 3 | 2 | **mineralsChart1 DATA_MISMATCH (Rare Earths 90 vs 98%)** |
| the-last-drop | 4 | 2 | waterChart1, waterChart2 METHODOLOGY_CONCERN |
| dealing-with-the-consequences-of-climate-chance-inaction | 5 | 2 | foodChart1, foodChart2 METHODOLOGY_CONCERN, foodChart4 EDITORIAL |
| establishing-a-price-floor | 2 | 0 | Both EDITORIAL |
| vertical-farming | 2 | 1 | vfChart1 METHODOLOGY_CONCERN |
| who-are-the-losers | 2 | 1 | losersChart1 EDITORIAL |
| the-scramble-for-the-solar-system | 2 | 2 | — |

### Batch 2: History, War, Civilisation

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| the-unintended-consequences-of-war | 8 | 6 | warChart2 METHODOLOGY_CONCERN, warChart3 EDITORIAL |
| the-rise-of-the-west | 4 | 2 | luckChart2 EDITORIAL |
| what-does-it-take-to-get-europeans-to-have-a-revolution | 7 | 1 | revChart1–4, revChart6 EDITORIAL |
| china-colonial-power | 3 | 2 | chinaColChart1 EDITORIAL |
| the-silence-of-the-scribes | 2 | 0 | scribesChart1 METHODOLOGY_CONCERN |
| who-guards-the-guards | 2 | 1 | heroGuards EDITORIAL |
| history-is-written-by-the-winners | 3 | 2 | heroWinners (4B vs 2.9B) |

### Batch 2: Technology, AI, Automation

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| robotics-and-slavery | 4 | 1 | robotChart1 STALE_DATA, robotChart2/3 EDITORIAL |
| where-are-all-the-jobs-going | 3 | 2 | indChart1 METHODOLOGY_CONCERN |
| the-150-year-life | 4 | 1 | longChart1 METHODOLOGY_CONCERN, longChart2/3 EDITORIAL |
| the-robot-bargain | 1 | 0 | **robotBargainChart1 DATA_MISMATCH (Japan 399 vs 419)** |
| when-the-servants-are-silicon | 4 | 1 | siliconChart1–3 METHODOLOGY_CONCERN/EDITORIAL |
| platform-technologies | 3 | 0 | **platChart1/3 DATA_MISMATCH**, platChart2 EDITORIAL |
| the-new-literacy | 5 | 2 | **newLitChart1 DATA_MISMATCH (97% vs 87–90%)**, newLitChart2/4 EDITORIAL/LABEL |

### Batch 2: Culture, Institutions, Society

| Article | Charts | Verified | Flagged |
|---------|--------|----------|---------|
| the-invisible-judge | 3 | 1 | **guiltChart2, guiltChart3 DATA_MISMATCH** |
| the-empty-throne | 4 | 1 | trustChart1/2 METHODOLOGY_CONCERN, trustChart3 EDITORIAL |
| the-young-continent | 4 | 3 | africaChart4 SOURCE_NOT_FOUND |
| the-elephant-awakens | 5 | 4 | indiaChart3 EDITORIAL |
| green-is-not-red-but-blue | 2 | 0 | Both EDITORIAL |
| roots | 2 | 1 | rootsChart2 EDITORIAL |
| big-european-electricity-utilities | 2 | 0 | utilChart1 STALE_DATA, utilChart2 EDITORIAL |

---

## Data Story (Hero) Charts Summary

| Headline | Status |
|----------|--------|
| Nearly half of Soviet men aged 18-30 were killed in WW2 | VERIFIED |
| Solar costs fell 99% in 40 years | VERIFIED |
| 60+ revolutions in 350 years | VERIFIED |
| North Africa will outnumber Southern Europe by 2030 | VERIFIED |
| COVID accelerated deglobalisation by a decade | EDITORIAL |
| A loaf of bread cost 3 billion Marks by 1923 | VERIFIED |
| Western dominance was a 200-year anomaly | VERIFIED |
| Robot costs falling below human labour | PROJECTION |
| Human life expectancy: from 30 to 150 years | FUTURE (150 speculative) |
| South Korea: 0.72 children per woman | SLIGHTLY STALE (2024 ~0.68) |
| Taiwan makes 63% of the world's advanced chips | VERIFIED |
| By 2100, Africa will have 4 billion people | **FLAG** — Use 2.9B (UN WPP medium) |
| €800 billion: Europe rearming | VERIFIED |
| US newspaper jobs down 80% since 1990 | VERIFIED |
| No country has recovered from sub-1.5 fertility | VERIFIED |
| India made 78,500 content removal requests in 2024 | SOURCE CHECK |
| Launch costs fell from $54,500 to $200/kg | VERIFIED |
| US federal regulations grew 18x since 1950 | METHODOLOGY |
| Manufacturing fell from 30% to 11% of US GDP | VERIFIED |
| Foreign-born populations tripled since 1970 | VERIFIED |
| From 1 in 3 births to 1 in 15 — builder populations vanishing | VERIFIED |

---

## Map Chart Verification

All appended map charts (emptyingMap, cradleMap, buildersMap, rearmsMap, gatesMap, renewablesMap, offshoringMap, northAfricaMap, covidMap, foodMap, chinaColonialMap, landDealsMap) were checked against UN WPP, SIPRI, UN DESA, IEA, Ember, Land Matrix, and related sources. Values are plausible; no major discrepancies.

---

## Recommendations

1. **Implement high-priority corrections** — 8 charts with clear data mismatches should be updated in `chart_defs.py`.
2. **Update stale sources** — 7 charts cite WPP 2022 or older; switch to WPP 2024 where applicable.
3. **Add source notes for EDITORIAL charts** — Ensure "Analysis from this article" is visible so readers understand limits of verifiability.
4. **Fix heroWinners headline** — Use UN WPP 2024 medium variant (2.9B) or cite high variant explicitly.
5. **Reconcile platform-technology charts** — platChart1 and platChart3 use different definitions; align or clarify.

---

## Verification Protocol Used

Each chart was assessed on:

1. **Source existence** — Does the cited source exist and is it correctly attributed?
2. **Data accuracy** — Do 3–5 key data points match the source?
3. **Currency** — Is a newer edition of the source available?
4. **Label correctness** — Do title and description match the data?
5. **Methodological soundness** — Are calculations and projections reasonable?

Flags: `VERIFIED`, `DATA_MISMATCH`, `SOURCE_NOT_FOUND`, `STALE_DATA`, `LABEL_ERROR`, `METHODOLOGY_CONCERN`, `EDITORIAL`.
