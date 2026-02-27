# History Future Now — Agent Directives

## Editorial Voice & Position

### British English
- Spelling: -ise (not -ize), -our (not -or), -tre (not -ter), -ence (not -ense), grey, tyre, aluminium, programme
- Voice: British understatement, measured authoritative tone (Economist style), dry wit welcome
- NO American hyperbole

### Editorial Position
- Small government, strong individuals. Full responsibility is a precondition for adult flourishing.
- Subsidiarity: govern at lowest possible level (individual > family > community > nation)
- Government spending unsustainable — solution is smaller state, not higher taxes
- Diversity between nations, cohesion within. National identity worth preserving in every country.
- Mass migration doesn't fix underlying causes
- Supranational organisations undermine democracy (citizens can't vote them out)
- "Populism" delegitimizes democratic accountability — it's democracy reasserting itself
- Bureaucratic state too powerful, NGOs are extensions of state outside accountability
- Frame national governments as first obligation, personal/community responsibility as default

### Reader Experience
- Reader must finish feeling delightedly enlightened — smarter, surprised, glad
- Historical sections are primary vehicle for teaching something genuinely unknown
- At least ONE moment of unexpected clever language in first third (dry wit, sardonic aside)
- End with a quotable, shareable line
- Target 1,500-3,000 words — no topic needs 4,000
- Test: Could reader explain core argument + historical fact to a friend at dinner?

---

## Article Creation Workflow (strict order)
1. **Write article** — markdown with frontmatter, share_summary, British English, 3,000-5,000 words
2. **Fact-check** — extract verifiable claims, verify each, correct errors, flag unverifiable (NOT optional)
3. **Define charts** — add to `chart_defs.py`, min 1, target 2-5
4. **Generate hero image** — create `hfn-site-output/images/articles/{slug}/hero.png` in HFN style
5. **Build site** — run `build.py`, verify HTML
6. **Generate discussion script** — `generate_discussions.py` (needs GEMINI_API_KEY)
7. **Generate audio narration** — `generate_audio.py` (needs API key)
8. **Generate discussion audio** — `generate_discussions.py audio` (needs API key)
9. **Deploy** — `./scripts/deploy.sh`, verify live

### Essay Model Requirement
Essay writing MUST use Opus 4.6. Never delegate prose to faster/cheaper models. Covers: drafting, rewriting, debate scripts, share summaries. Does NOT cover: chart defs, build system, file searches, image prompts, deploying.

---

## Article Requirements

### Fact-Checking (CRITICAL)
- Every verifiable claim MUST be checked against authoritative source before publication
- Process: Search for claim > Compare > If confirmed proceed > If differs >10% correct > If unverifiable flag
- For claims central to thesis: cross-reference against second independent source
- Preferred sources: UN DESA, World Bank, OECD, IEA, Pew, Eurobarometer, IISS, WTO, UNESCO
- Never invent a plausible number. If you can't find it, flag it.

### Charts
- Every article MUST include at least 1 chart, target 2-5
- Charts defined in `hfn-build-system/chart_defs.py`
- Each chart: id, figure_num, title, desc, source, position, js
- Use shared COLORS theme
- Charts must cover historic-present-future arcs when possible
- Two versions: interactive (Chart.js in-article) + static PNG (for sharing)
- Per-chart share button required

### Chart Year Formatting
Years are NOT quantities — never format with thousand-separator commas.
- CORRECT: `ticks: { callback: v => String(v) }` or shared `yearTick` helper
- WRONG: No callback (Chart.js adds commas: "1,500", "2,025")

### Chart Fact-Checking
Every data point must be verifiable against a named published source.
- Data within 5% of source, title accurate, y-axis matches metric, source citation specific
- Never round aggressively or invent plausible numbers

### Hero Images
- Every article MUST have hero image in `hfn-site-output/images/articles/{slug}/`
- Style: flat geometric editorial illustration, mid-century modern poster aesthetic
- NO writing/text on images, NO photorealism, NO detailed faces
- Colours: warm muted editorial palette (terracotta, navy, sand, teal, grey, ochre)
- Test: Does it belong next to "The Robot Bargain" and "The Silence of the Scribes"?

### Library References
- At least 3 books from HFN Library referenced per article
- Every cited book must appear in `library_data.py` BOOKS list AND article's `sources` frontmatter
- At least 2 other HFN articles cross-referenced with relative links
- Check `hfn-site-output/search-index.json` for article catalogue

### Sharing
- Share buttons top and bottom of every article (X, LinkedIn, WhatsApp, Email, Copy Link)
- Frontmatter must include `share_summary` (140 chars or less, pithy thesis)
- OG/social meta tags required (og:title, og:description, og:image, twitter:card)

---

## Audio Debates (PAUSED)
Debates disabled via `ENABLE_DISCUSSIONS=False` in `build.py`. Existing scripts/audio preserved — do not generate new debates until re-enabled.

When resumed: James (centre-right analyst) and Elena (progressive analyst). Elena opens ~40% of debates, introduces own topics with evidence. Neither is caricature. British English. 25-40 turns, 1,500-2,500 words.

---

## Review Process
New articles must be added to `REVIEW_SLUGS` in `hfn-build-system/build.py`. Articles appear on `/review/` with noindex. Only move to `RELEASED_FROM_REVIEW` when user explicitly approves.

---

## Deployment
Static site on Vercel.
- **New articles:** Build locally as drafts for review. Only deploy after user explicitly approves.
- **Everything else:** auto-deploy (fixes, upgrades, layout, audio, media, site-wide changes)
- Deploy: `./scripts/deploy.sh "feat: description"`
- IMPORTANT: `git push` alone does NOT deploy — must run `vercel --prod`
- After deploying: verify https://www.historyfuturenow.com loads

---

## Chart Rendering Gotchas
- Each chart IIFE must wrap in try/catch (one error silencing subsequent charts)
- Canvas needs min-height fallback for soft-nav timing
- Geo charts: check both needs_geo flags, chart wrapper regex can break geo IIFEs
- Choropleth needs explicit dimensions (can silently fail with zero height)
