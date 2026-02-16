"""
Library data for the History Future Now reading map.
Curated selection of ~300+ titles from 470+ total, excluding children's books,
language learning materials, erotica, and other titles not relevant to the
intellectual map.
"""

# ── Theme definitions ──
THEMES = {
    "civilisation": {
        "name": "Civilisational Fragility",
        "color": "#0d9a5a",
        "color_soft": "#effaf4",
        "icon": "🏛️",
        "order": 1,
        "desc": "History driven by logistics, energy, geography, institutions, demography, and incentives — not moral arcs or heroic individuals. The instinct for root causes and second-order consequences.",
    },
    "empire": {
        "name": "Empire Lifecycle &amp; Failure Modes",
        "color": "#2563eb",
        "color_soft": "#eff4ff",
        "icon": "⚔️",
        "order": 2,
        "desc": "Repeated deep dives into Rome, Byzantium, early modern Europe, and modern great powers. Collapse treated as a recurring problem of political economy, security dilemmas, and legitimacy crises.",
    },
    "geopolitics": {
        "name": "Structural Realism",
        "color": "#1e3a5f",
        "color_soft": "#eef2f7",
        "icon": "🌐",
        "order": 3,
        "desc": "Great-power competition is inevitable because the system compels it. Geography, technology, and anarchy matter more than ideals. The default question: what are states forced to do?",
    },
    "economics": {
        "name": "Economic Incentives &amp; Institutions",
        "color": "#b8751a",
        "color_soft": "#fef8ee",
        "icon": "📊",
        "order": 4,
        "desc": "Both market-sceptical and market-fundamentalist authors, plus state-capacity realists. A deliberate tension between markets, incentives, and price signals on one side, and institutions, industrial policy, and state capacity on the other.",
    },
    "ideology": {
        "name": "Ideology &amp; Narrative Capture",
        "color": "#c43425",
        "color_soft": "#fef3f1",
        "icon": "📢",
        "order": 5,
        "desc": "Societies run on stories — and stories can become weapons. Acute sensitivity to moral panics, status games, institutional capture, and sacred concepts that cannot be questioned.",
    },
    "religion": {
        "name": "Religion as Social Technology",
        "color": "#7c3aed",
        "color_soft": "#f5f0ff",
        "icon": "✝️",
        "order": 6,
        "desc": "Not devotional reading — analytical. Christianity's role in cohesion, legitimacy, time preference, and moral structure. Secular modernity often replicates religious forms without acknowledging it.",
    },
    "technology": {
        "name": "Hard Constraints on Technology",
        "color": "#0c8f8f",
        "color_soft": "#effafa",
        "icon": "⚡",
        "order": 7,
        "desc": "Energy, materials, supply chains, and physics trump wishful thinking. Progress depends on supply chains and physics, not vibes. Existential risk is procedural and systemic, not villain-driven.",
    },
    "cognition": {
        "name": "Cognitive &amp; Rhetorical Upgrades",
        "color": "#0284c7",
        "color_soft": "#eff8ff",
        "icon": "🧠",
        "order": 8,
        "desc": "Explicit investment in better reasoning, argumentation, strategy, and decision-making. Not just consuming content — upgrading the operating system that processes it.",
    },
    "biology": {
        "name": "Biology &amp; Human Nature",
        "color": "#b85c5c",
        "color_soft": "#fef5f5",
        "icon": "🧬",
        "order": 9,
        "desc": "Evolutionary psychology, sex differences, ageing, epigenetics, mitochondria. The bedrock beneath institutions and ideologies: human nature itself.",
    },
    "fiction": {
        "name": "Fiction as Civilisational Simulation",
        "color": "#4a4a4a",
        "color_soft": "#f5f5f5",
        "icon": "📖",
        "order": 10,
        "desc": "Not escapism — chosen for institutional depth, decay scenarios, and power dynamics. Science fiction as sociology; historical fiction as ground-level perspective on the forces studied in non-fiction.",
    },
}

# ── Timeline phases ──
PHASES = [
    {"start": 2012, "end": 2018, "label": "Broad Exploration", "desc": "Wide-ranging curiosity across history, science, and classics. Building foundations."},
    {"start": 2018, "end": 2021, "label": "Ancient &amp; Medieval Deep Dive", "desc": "Sustained immersion in Rome, Carthage, Vikings, Normans, and the medieval world."},
    {"start": 2021, "end": 2023, "label": "Geopolitics &amp; Culture", "desc": "Sharpening focus on great-power competition, ideology critique, and institutional analysis."},
    {"start": 2023, "end": 2025, "label": "Hard Limits &amp; Biology", "desc": "Technology constraints, nuclear risk, evolutionary biology, and the material foundations of progress."},
]

# ── Intellectual fingerprint ──
FINGERPRINT = {
    "default_questions": [
        "What are the hidden constraints — energy, geography, institutions, demography?",
        "What are the failure modes — elite miscalculation, legitimacy collapse, narrative capture?",
        "What are the control systems — religion, ideology, media, institutions?",
        "Which actors are forced by structure, and which have genuine agency?",
    ],
    "tensions": [
        {"name": "Progress optimism vs. constraint realism", "desc": "Deutsch and Kurzweil on one shelf; Heinberg, Smil, and nuclear risk on the other."},
        {"name": "Markets-first vs. state-capacity-first", "desc": "Hayek, Friedman, and Mises alongside Acemoglu, Mazzucato, and Chinese industrial reality."},
        {"name": "Universalism vs. particularism", "desc": "Strong critiques of identity politics sit next to evolutionary psychology and group-differences research."},
        {"name": "Great men vs. systems", "desc": "Biography and narrative history alongside systems thinking and structural analysis. The synthesis: structures create the stage, individuals decide the play."},
    ],
    "underrepresented": [
        "Public administration — how to run complex institutions well, not only how they fail",
        "Demography as a primary driver — touched but not yet a core pillar",
        "Non-Western primary sources beyond secondary syntheses",
        "Monetary economics and central-banking regimes",
        "Positive-deviance case studies of flourishing societies",
    ],
}

# ── Editorial intro ──
INTRO_ESSAY = """You are what you read, in much the same way that you are what you eat. The books that pass through your mind over a decade reshape the questions you ask, the patterns you recognise, and the assumptions you carry into every argument. A library is not a trophy case — it is a map of the intellectual inputs that produced a particular way of seeing the world.

This page is an act of radical transparency. Every article on History Future Now emerges from a specific set of readings, and here they are — not curated to flatter, but listed honestly. Some of these books are brilliant. Some are wrong. Some are both. A serious reader must engage with arguments they find uncomfortable, because understanding a position is not the same as endorsing it. You cannot critique what you have not read.

What follows is a curated selection from a larger library of over 1,300 titles acquired between 2012 and 2025. They are organised by the intellectual themes they collectively reinforce — the recurring questions, tensions, and frameworks that shape the analysis on this site."""

# ── Book data ──
# Each book: {"title", "author", "year", "source": "audible"|"kindle"|"physical", "themes": [list]}
# year = year of purchase/download (not publication)

BOOKS = [
    # ═══════════════════════════════════════════════════════════════
    # CIVILISATIONAL FRAGILITY
    # ═══════════════════════════════════════════════════════════════
    {"title": "The Earth Transformed", "author": "Peter Frankopan", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "The Rise of the West", "author": "William H. McNeill", "year": 2024, "source": "audible", "themes": ["civilisation", "empire"]},
    {"title": "How the World Made the West", "author": "Josephine Quinn", "year": 2024, "source": "audible", "themes": ["civilisation"]},
    {"title": "Global Crisis", "author": "Geoffrey Parker", "year": 2024, "source": "kindle", "themes": ["civilisation", "empire"]},
    {"title": "Thinking in Systems", "author": "Donella H. Meadows", "year": 2025, "source": "audible", "themes": ["civilisation", "cognition"]},
    {"title": "Algorithms to Live By", "author": "Brian Christian & Tom Griffiths", "year": 2025, "source": "audible", "themes": ["cognition", "civilisation"]},
    {"title": "A History of the World", "author": "Andrew Marr", "year": 2012, "source": "audible", "themes": ["civilisation"]},
    {"title": "A History of Britain, Vol. 1", "author": "Simon Schama", "year": 2016, "source": "audible", "themes": ["civilisation"]},
    {"title": "A Short History of Nearly Everything", "author": "Bill Bryson", "year": 2012, "source": "kindle", "themes": ["civilisation"]},
    {"title": "A Million Years in a Day", "author": "Greg Jenner", "year": 2015, "source": "audible", "themes": ["civilisation"]},
    {"title": "Europe: A History", "author": "Norman Davies", "year": 2014, "source": "kindle", "themes": ["civilisation", "empire"]},
    {"title": "The World", "author": "Simon Sebag Montefiore", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "The Invention of Yesterday", "author": "Tamim Ansary", "year": 2024, "source": "audible", "themes": ["civilisation"]},
    {"title": "A History of the World in 47 Borders", "author": "Jonn Elledge", "year": 2024, "source": "audible", "themes": ["civilisation", "geopolitics"]},
    {"title": "Sapiens", "author": "Yuval Noah Harari", "year": 2017, "source": "audible", "themes": ["civilisation", "biology"]},
    {"title": "Homo Deus", "author": "Yuval Noah Harari", "year": 2017, "source": "audible", "themes": ["civilisation", "technology"]},
    {"title": "The Dawn of Everything", "author": "David Graeber & David Wengrow", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "Against the Grain", "author": "James C. Scott", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "The WEIRDest People in the World", "author": "Joseph Henrich", "year": 2024, "source": "audible", "themes": ["civilisation", "biology"]},
    {"title": "A Theory of Everyone", "author": "Michael Muthukrishna", "year": 2023, "source": "audible", "themes": ["civilisation", "biology"]},
    {"title": "How We Got to Now", "author": "Steven Johnson", "year": 2022, "source": "kindle", "themes": ["civilisation", "technology"]},
    {"title": "Making the Modern World", "author": "Vaclav Smil", "year": 2014, "source": "kindle", "themes": ["civilisation", "technology"]},
    {"title": "How the World Really Works", "author": "Vaclav Smil", "year": 2022, "source": "audible", "themes": ["civilisation", "technology"]},
    {"title": "Centuries of Change", "author": "Ian Mortimer", "year": 2022, "source": "audible", "themes": ["civilisation"]},
    {"title": "The Foundations of Western Civilization", "author": "Thomas F. X. Noble", "year": 2022, "source": "audible", "themes": ["civilisation"]},
    {"title": "The Big History of Civilizations", "author": "Craig G. Benjamin", "year": 2017, "source": "audible", "themes": ["civilisation"]},
    {"title": "Foundations of Eastern Civilization", "author": "Craig G. Benjamin", "year": 2020, "source": "audible", "themes": ["civilisation"]},
    {"title": "Turning Points in Modern History", "author": "Vejas Gabriel Liulevicius", "year": 2015, "source": "audible", "themes": ["civilisation"]},
    {"title": "An Economic History of the World since 1400", "author": "Donald J. Harreld", "year": 2016, "source": "audible", "themes": ["civilisation", "economics"]},
    {"title": "The Horse, the Wheel, and Language", "author": "David W. Anthony", "year": 2022, "source": "audible", "themes": ["civilisation"]},
    {"title": "The World Before Us", "author": "Tom Higham", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "Across Atlantic Ice", "author": "Bruce A. Bradley & Denis J. Stanford", "year": 2025, "source": "audible", "themes": ["civilisation"]},
    {"title": "Proto: How One Ancient Language Went Global", "author": "Laura Spinney", "year": 2025, "source": "audible", "themes": ["civilisation"]},
    {"title": "Children of Ash and Elm", "author": "Neil Price", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "Buried", "author": "Alice Roberts", "year": 2023, "source": "audible", "themes": ["civilisation"]},
    {"title": "A Brief History of Everyone Who Ever Lived", "author": "Adam Rutherford", "year": 2018, "source": "audible", "themes": ["civilisation", "biology"]},
    {"title": "Knowledge", "author": "Lewis Dartnell", "year": 2015, "source": "audible", "themes": ["civilisation", "technology"]},
    {"title": "How to Invent Everything", "author": "Ryan North", "year": 2019, "source": "audible", "themes": ["civilisation", "technology"]},

    # ═══════════════════════════════════════════════════════════════
    # EMPIRE LIFECYCLE & FAILURE MODES
    # ═══════════════════════════════════════════════════════════════
    {"title": "SPQR", "author": "Mary Beard", "year": 2015, "source": "audible", "themes": ["empire"]},
    {"title": "The Fall of Rome", "author": "Bryan Ward-Perkins", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "The Fall of the Roman Empire", "author": "Peter Heather", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Decline and Fall of the Roman Empire", "author": "Edward Gibbon", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Escape from Rome", "author": "Walter Scheidel", "year": 2025, "source": "audible", "themes": ["empire"]},
    {"title": "Rome: An Empire's Story", "author": "Greg Woolf", "year": 2012, "source": "kindle", "themes": ["empire"]},
    {"title": "Pax: War and Peace in Rome's Golden Age", "author": "Tom Holland", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Theodoric the Great", "author": "Hans-Ulrich Wiemer", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Carthage Must Be Destroyed", "author": "Richard Miles", "year": 2018, "source": "audible", "themes": ["empire"]},
    {"title": "1177 B.C.", "author": "Eric H. Cline", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "After 1177 B.C.", "author": "Eric H. Cline", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "The Peloponnesian War", "author": "Kenneth W. Harl", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The End of Everything", "author": "Victor Davis Hanson", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "The Fate of Empires", "author": "Arthur John Hubbard", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "Why Empires Fall", "author": "John Rapley", "year": 2024, "source": "kindle", "themes": ["empire"]},
    {"title": "The Thirty Years War", "author": "C. V. Wedgwood", "year": 2014, "source": "audible", "themes": ["empire"]},
    {"title": "The Thirty Years War", "author": "Peter H. Wilson", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Heart of Europe", "author": "Peter H. Wilson", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Iron and Blood", "author": "Peter H. Wilson", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Iron Kingdom", "author": "Christopher Clark", "year": 2015, "source": "physical", "themes": ["empire"]},
    {"title": "The Sleepwalkers", "author": "Christopher Clark", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The War That Ended Peace", "author": "Margaret MacMillan", "year": 2014, "source": "audible", "themes": ["empire"]},
    {"title": "Catastrophe: Europe Goes to War 1914", "author": "Max Hastings", "year": 2013, "source": "kindle", "themes": ["empire"]},
    {"title": "July 1914: Countdown to War", "author": "Sean McMeekin", "year": 2025, "source": "audible", "themes": ["empire"]},
    {"title": "The Proud Tower", "author": "Barbara W. Tuchman", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "Doom", "author": "Niall Ferguson", "year": 2022, "source": "audible", "themes": ["empire", "civilisation"]},
    {"title": "The War of the World", "author": "Niall Ferguson", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Virtual History", "author": "Niall Ferguson (ed.)", "year": 2012, "source": "kindle", "themes": ["empire"]},
    {"title": "The Rise and Fall of the Third Reich", "author": "William L. Shirer", "year": 2018, "source": "audible", "themes": ["empire"]},
    {"title": "The Wages of Destruction", "author": "Adam Tooze", "year": 2023, "source": "audible", "themes": ["empire", "economics"]},
    {"title": "Stalin's War", "author": "Sean McMeekin", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Holocaust", "author": "Laurence Rees", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "Aftermath", "author": "Harald Jähner", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Vanquished", "author": "Robert Gerwarth", "year": 2017, "source": "audible", "themes": ["empire"]},
    {"title": "Savage Continent", "author": "Keith Lowe", "year": 2021, "source": "physical", "themes": ["empire"]},
    {"title": "Post War", "author": "Tony Judt", "year": 2021, "source": "physical", "themes": ["empire"]},
    {"title": "To Hell and Back", "author": "Ian Kershaw", "year": 2015, "source": "audible", "themes": ["empire"]},
    {"title": "Fateful Choices", "author": "Ian Kershaw", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "The Habsburgs", "author": "Martyn Rady", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Metternich", "author": "Wolfram Siemann", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Bismarck's War", "author": "Rachel Chrastil", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Anglo-Saxons", "author": "Marc Morris", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "A Great and Terrible King", "author": "Marc Morris", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Norman Conquest", "author": "Marc Morris", "year": 2013, "source": "physical", "themes": ["empire"]},
    {"title": "The Plantagenets", "author": "Dan Jones", "year": 2021, "source": "audible", "themes": ["empire"]},
    {"title": "The English and Their History", "author": "Robert Tombs", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Restless Republic", "author": "Anna Keay", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Devil-Land", "author": "Clare Jackson", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The British Are Coming", "author": "Rick Atkinson", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Britain Against Napoleon", "author": "Roger Knight", "year": 2023, "source": "kindle", "themes": ["empire"]},
    {"title": "The Anarchy", "author": "William Dalrymple", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "Istanbul", "author": "Bettany Hughes", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Fall of the Ottomans", "author": "Eugene Rogan", "year": 2022, "source": "kindle", "themes": ["empire"]},
    {"title": "The Damascus Events", "author": "Eugene Rogan", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "The Fall and Rise of China", "author": "Richard Baum", "year": 2015, "source": "audible", "themes": ["empire", "geopolitics"]},
    {"title": "Empress Dowager Cixi", "author": "Jung Chang", "year": 2020, "source": "audible", "themes": ["empire"]},
    {"title": "The Rise and Fall of the British Empire", "author": "Patrick N. Allitt", "year": 2015, "source": "audible", "themes": ["empire"]},
    {"title": "The Cold War", "author": "Odd Arne Westad", "year": 2021, "source": "audible", "themes": ["empire", "geopolitics"]},
    {"title": "The Long 19th Century", "author": "Robert I. Weiner", "year": 2021, "source": "audible", "themes": ["empire"]},
    {"title": "The Decline of the West", "author": "Oswald Spengler", "year": 2022, "source": "kindle", "themes": ["empire"]},
    {"title": "Eminent Victorians", "author": "Lytton Strachey", "year": 2025, "source": "audible", "themes": ["empire"]},
    {"title": "1929", "author": "Andrew Ross Sorkin", "year": 2025, "source": "audible", "themes": ["empire", "economics"]},
    {"title": "Lords of Finance", "author": "Liaquat Ahamed", "year": 2013, "source": "kindle", "themes": ["empire", "economics"]},
    {"title": "Stalingrad", "author": "Antony Beevor", "year": 2020, "source": "physical", "themes": ["empire"]},
    {"title": "The Storm of War", "author": "Andrew Roberts", "year": 2012, "source": "audible", "themes": ["empire"]},
    {"title": "Engineers of Victory", "author": "Paul Kennedy", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "A Concise History of Germany", "author": "Mary Fulbrook", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Blood and Iron", "author": "Katja Hoyer", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Beyond the Wall", "author": "Katja Hoyer", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "Not One Inch", "author": "M. E. Sarotte", "year": 2023, "source": "audible", "themes": ["empire", "geopolitics"]},
    {"title": "Lost Kingdom", "author": "Serhii Plokhy", "year": 2022, "source": "kindle", "themes": ["empire", "geopolitics"]},
    {"title": "Chernobyl", "author": "Serhii Plokhy", "year": 2020, "source": "physical", "themes": ["empire", "technology"]},
    {"title": "A History of Russia", "author": "Mark Steinberg", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "Stalin", "author": "Simon Sebag Montefiore", "year": 2022, "source": "kindle", "themes": ["empire"]},
    {"title": "The Gulag Archipelago", "author": "Aleksandr Solzhenitsyn", "year": 2024, "source": "audible", "themes": ["empire"]},
    {"title": "Hero of Two Worlds", "author": "Mike Duncan", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "The Pioneers", "author": "David McCullough", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "George Marshall", "author": "David L. Roll", "year": 2023, "source": "audible", "themes": ["empire"]},
    {"title": "The Path to Power", "author": "Robert A. Caro", "year": 2021, "source": "audible", "themes": ["empire"]},
    {"title": "George III", "author": "Andrew Roberts", "year": 2021, "source": "audible", "themes": ["empire"]},
    {"title": "Peter the Great", "author": "Robert K. Massie", "year": 2012, "source": "kindle", "themes": ["empire"]},
    {"title": "Catherine de Medici", "author": "Leonie Frieda", "year": 2018, "source": "audible", "themes": ["empire"]},
    {"title": "Florence: The Biography of a City", "author": "Christopher Hibbert", "year": 2013, "source": "kindle", "themes": ["empire"]},
    {"title": "The Rise and Fall of the House of Medici", "author": "Christopher Hibbert", "year": 2013, "source": "kindle", "themes": ["empire"]},
    {"title": "Spain", "author": "Robert Goodwin", "year": 2022, "source": "kindle", "themes": ["empire"]},
    {"title": "The Great Sea", "author": "David Abulafia", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "Crimea", "author": "Orlando Figes", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "The Great Anglo-Boer War", "author": "Byron Farwell", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "Towards the Flame", "author": "Dominic Lieven", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "Albion's Seed", "author": "David Hackett Fischer", "year": 2015, "source": "physical", "themes": ["empire", "civilisation"]},
    {"title": "Before 1776", "author": "Robert J. Allison", "year": 2022, "source": "audible", "themes": ["empire"]},
    {"title": "The Ideological Origins of the American Revolution", "author": "Bernard Bailyn", "year": 2025, "source": "audible", "themes": ["empire", "ideology"]},
    {"title": "The Origins of the Urban Crisis", "author": "Thomas J. Sugrue", "year": 2025, "source": "audible", "themes": ["empire", "economics"]},
    {"title": "Boomers", "author": "Helen Andrews", "year": 2025, "source": "audible", "themes": ["empire", "ideology"]},

    # ═══════════════════════════════════════════════════════════════
    # STRUCTURAL REALISM IN GEOPOLITICS
    # ═══════════════════════════════════════════════════════════════
    {"title": "The Tragedy of Great Power Politics", "author": "John J. Mearsheimer", "year": 2012, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "The Great Delusion", "author": "John J. Mearsheimer", "year": 2023, "source": "audible", "themes": ["geopolitics"]},
    {"title": "The Grand Chessboard", "author": "Zbigniew Brzezinski", "year": 2014, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "The Revenge of Geography", "author": "Robert D. Kaplan", "year": 2012, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "The End of the World Is Just the Beginning", "author": "Peter Zeihan", "year": 2023, "source": "audible", "themes": ["geopolitics"]},
    {"title": "Geography Is Destiny", "author": "Ian Morris", "year": 2023, "source": "audible", "themes": ["geopolitics"]},
    {"title": "Chip War", "author": "Chris Miller", "year": 2023, "source": "audible", "themes": ["geopolitics", "technology"]},
    {"title": "Apple in China", "author": "Patrick McGee", "year": 2025, "source": "audible", "themes": ["geopolitics", "technology"]},
    {"title": "The Red Emperor", "author": "Michael Sheridan", "year": 2025, "source": "audible", "themes": ["geopolitics"]},
    {"title": "Breakneck", "author": "Dan Wang", "year": 2025, "source": "audible", "themes": ["geopolitics", "technology"]},
    {"title": "The Influence of Seapower Upon History", "author": "Alfred T. Mahan", "year": 2024, "source": "audible", "themes": ["geopolitics"]},
    {"title": "The Grand Strategy of the Roman Empire", "author": "Edward N. Luttwak", "year": 2025, "source": "audible", "themes": ["geopolitics", "empire"]},
    {"title": "The Grand Strategy of the Byzantine Empire", "author": "Edward N. Luttwak", "year": 2013, "source": "kindle", "themes": ["geopolitics", "empire"]},
    {"title": "Strategy", "author": "Lawrence Freedman", "year": 2023, "source": "audible", "themes": ["geopolitics", "cognition"]},
    {"title": "Masters of War", "author": "Andrew R. Wilson", "year": 2015, "source": "audible", "themes": ["geopolitics"]},
    {"title": "Armies of Sand", "author": "Kenneth M. Pollack", "year": 2023, "source": "audible", "themes": ["geopolitics"]},
    {"title": "Why We Fight", "author": "Christopher Blattman", "year": 2022, "source": "audible", "themes": ["geopolitics"]},
    {"title": "Thinking Strategically", "author": "Avinash K. Dixit", "year": 2022, "source": "audible", "themes": ["geopolitics", "cognition"]},
    {"title": "Ghost Fleet", "author": "P. W. Singer & August Cole", "year": 2015, "source": "kindle", "themes": ["geopolitics", "fiction"]},
    {"title": "Destined for War", "author": "Graham Allison", "year": 2021, "source": "physical", "themes": ["geopolitics"]},
    {"title": "Belt and Road", "author": "Bruno Maçães", "year": 2021, "source": "physical", "themes": ["geopolitics"]},
    {"title": "Superpower Interrupted", "author": "Michael Schuman", "year": 2021, "source": "physical", "themes": ["geopolitics"]},
    {"title": "The Boiling Moat", "author": "Matt Pottinger", "year": 2024, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "The Technological Republic", "author": "Alexander C. Karp & Nicholas W. Zamiska", "year": 2025, "source": "audible", "themes": ["geopolitics", "technology"]},
    {"title": "House of Huawei", "author": "Eva Dou", "year": 2025, "source": "kindle", "themes": ["geopolitics", "technology"]},
    {"title": "The Nvidia Way", "author": "Tae Kim", "year": 2025, "source": "kindle", "themes": ["geopolitics", "technology"]},
    {"title": "Has China Won?", "author": "Kishore Mahbubani", "year": 2020, "source": "audible", "themes": ["geopolitics"]},
    {"title": "The Invention of China", "author": "Bill Hayton", "year": 2022, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "Dubai", "author": "Jim Krane", "year": 2022, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "Blood and Oil", "author": "Bradley Hope & Justin Scheck", "year": 2024, "source": "audible", "themes": ["geopolitics"]},
    {"title": "The Next 100 Years", "author": "George Friedman", "year": 2012, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "The World in 2050", "author": "Hamish McRae", "year": 2022, "source": "kindle", "themes": ["geopolitics"]},
    {"title": "America Alone", "author": "Mark Steyn", "year": 2021, "source": "physical", "themes": ["geopolitics"]},
    {"title": "Divided", "author": "Tim Marshall", "year": 2022, "source": "audible", "themes": ["geopolitics"]},

    # ═══════════════════════════════════════════════════════════════
    # ECONOMIC INCENTIVES & INSTITUTIONS
    # ═══════════════════════════════════════════════════════════════
    {"title": "Capitalism and Freedom", "author": "Milton Friedman", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "The Road to Serfdom", "author": "Friedrich A. Hayek", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "Economics in One Lesson", "author": "Henry Hazlitt", "year": 2023, "source": "audible", "themes": ["economics"]},
    {"title": "Human Action", "author": "Ludwig von Mises", "year": 2024, "source": "audible", "themes": ["economics"]},
    {"title": "Basic Economics", "author": "Thomas Sowell", "year": 2023, "source": "audible", "themes": ["economics"]},
    {"title": "Social Justice Fallacies", "author": "Thomas Sowell", "year": 2023, "source": "audible", "themes": ["economics", "ideology"]},
    {"title": "Migrations and Cultures", "author": "Thomas Sowell", "year": 2023, "source": "audible", "themes": ["economics", "civilisation"]},
    {"title": "Capital in the Twenty-First Century", "author": "Thomas Piketty", "year": 2014, "source": "kindle", "themes": ["economics"]},
    {"title": "Why Nations Fail", "author": "Daron Acemoglu & James Robinson", "year": 2012, "source": "kindle", "themes": ["economics", "civilisation"]},
    {"title": "Power and Progress", "author": "Simon Johnson & Daron Acemoglu", "year": 2023, "source": "audible", "themes": ["economics", "technology"]},
    {"title": "The Entrepreneurial State", "author": "Mariana Mazzucato", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "How Big Things Get Done", "author": "Bent Flyvbjerg & Dan Gardner", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "The Man Who Broke Capitalism", "author": "David Gelles", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "Abundance", "author": "Ezra Klein & Derek Thompson", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "The Case Against Education", "author": "Bryan Caplan", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "End of Growth", "author": "Richard Heinberg", "year": 2012, "source": "kindle", "themes": ["economics", "technology"]},
    {"title": "Narrative Economics", "author": "Robert J. Shiller", "year": 2024, "source": "audible", "themes": ["economics", "ideology"]},
    {"title": "Misbehaving", "author": "Richard H. Thaler", "year": 2023, "source": "audible", "themes": ["economics", "cognition"]},
    {"title": "Nudge: The Final Edition", "author": "Richard H. Thaler & Cass R. Sunstein", "year": 2022, "source": "kindle", "themes": ["economics", "cognition"]},
    {"title": "23 Things They Don't Tell You about Capitalism", "author": "Ha-Joon Chang", "year": 2022, "source": "kindle", "themes": ["economics"]},
    {"title": "The Power Law", "author": "Sebastian Mallaby", "year": 2023, "source": "audible", "themes": ["economics"]},
    {"title": "Zero to One", "author": "Peter Thiel & Blake Masters", "year": 2022, "source": "kindle", "themes": ["economics"]},
    {"title": "The Lean Startup", "author": "Eric Ries", "year": 2012, "source": "kindle", "themes": ["economics"]},
    {"title": "Good Strategy/Bad Strategy", "author": "Richard Rumelt", "year": 2023, "source": "audible", "themes": ["economics", "cognition"]},
    {"title": "7 Powers", "author": "Hamilton Helmer", "year": 2023, "source": "audible", "themes": ["economics", "cognition"]},
    {"title": "Behemoth: A History of the Factory", "author": "Joshua B. Freeman", "year": 2020, "source": "kindle", "themes": ["economics", "technology"]},
    {"title": "The Innovator's Dilemma", "author": "Clayton M. Christensen", "year": 2012, "source": "kindle", "themes": ["economics", "technology"]},
    {"title": "Butler to the World", "author": "Oliver Bullough", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "Company of One", "author": "Paul Jarvis", "year": 2025, "source": "audible", "themes": ["economics"]},
    {"title": "Pattern Breakers", "author": "Mike Maples Jr. & Peter Ziebelman", "year": 2024, "source": "audible", "themes": ["economics"]},
    {"title": "Democracy: The God That Failed", "author": "Hans-Hermann Hoppe", "year": 2023, "source": "audible", "themes": ["economics", "ideology"]},

    # ═══════════════════════════════════════════════════════════════
    # IDEOLOGY & NARRATIVE CAPTURE
    # ═══════════════════════════════════════════════════════════════
    {"title": "The True Believer", "author": "Eric Hoffer", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "Violence and the Sacred", "author": "René Girard", "year": 2024, "source": "audible", "themes": ["ideology", "religion"]},
    {"title": "Cynical Theories", "author": "Helen Pluckrose & James Lindsay", "year": 2022, "source": "audible", "themes": ["ideology"]},
    {"title": "We Have Never Been Woke", "author": "Musa al-Gharbi", "year": 2025, "source": "audible", "themes": ["ideology"]},
    {"title": "Woke Racism", "author": "John McWhorter", "year": 2022, "source": "audible", "themes": ["ideology"]},
    {"title": "The End of Race Politics", "author": "Coleman Hughes", "year": 2024, "source": "audible", "themes": ["ideology"]},
    {"title": "The War on the West", "author": "Douglas Murray", "year": 2022, "source": "audible", "themes": ["ideology"]},
    {"title": "On Democracies and Death Cults", "author": "Douglas Murray", "year": 2025, "source": "audible", "themes": ["ideology"]},
    {"title": "America's Cultural Revolution", "author": "Christopher F. Rufo", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "How Fascism Works", "author": "Jason Stanley", "year": 2025, "source": "audible", "themes": ["ideology"]},
    {"title": "The Psychology of Totalitarianism", "author": "Mattias Desmet", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "The Rise and Triumph of the Modern Self", "author": "Carl R. Trueman", "year": 2022, "source": "kindle", "themes": ["ideology", "religion"]},
    {"title": "The Anxious Generation", "author": "Jonathan Haidt", "year": 2024, "source": "audible", "themes": ["ideology", "biology"]},
    {"title": "The Coddling of the American Mind", "author": "Jonathan Haidt & Greg Lukianoff", "year": 2021, "source": "audible", "themes": ["ideology"]},
    {"title": "The Great Experiment", "author": "Yascha Mounk", "year": 2022, "source": "audible", "themes": ["ideology"]},
    {"title": "Invisible Rulers", "author": "Renée DiResta", "year": 2024, "source": "audible", "themes": ["ideology"]},
    {"title": "The Crowd: A Study of the Popular Mind", "author": "Gustave Le Bon", "year": 2022, "source": "kindle", "themes": ["ideology"]},
    {"title": "Rules for Radicals", "author": "Saul D. Alinsky", "year": 2024, "source": "audible", "themes": ["ideology"]},
    {"title": "Collapse of Global Liberalism", "author": "Philip Pilkington", "year": 2023, "source": "audible", "themes": ["ideology", "economics"]},
    {"title": "The Stakes", "author": "Michael Anton", "year": 2025, "source": "audible", "themes": ["ideology"]},
    {"title": "Second Class", "author": "Batya Ungar-Sargon", "year": 2025, "source": "audible", "themes": ["ideology"]},
    {"title": "Values, Voice and Virtue", "author": "Matthew Goodwin", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "Feminism Against Progress", "author": "Mary Harrington", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "The Case Against the Sexual Revolution", "author": "Louise Perry", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "Bad Therapy", "author": "Abigail Shrier", "year": 2024, "source": "audible", "themes": ["ideology"]},
    {"title": "The Boy Crisis", "author": "Warren Farrell & John Gray", "year": 2022, "source": "kindle", "themes": ["ideology", "biology"]},
    {"title": "Of Boys and Men", "author": "Richard V. Reeves", "year": 2022, "source": "audible", "themes": ["ideology", "biology"]},
    {"title": "White Shift", "author": "Eric Kaufmann", "year": 2021, "source": "physical", "themes": ["ideology"]},
    {"title": "Shall the Religious Inherit the Earth?", "author": "Eric Kaufmann", "year": 2022, "source": "kindle", "themes": ["ideology", "religion"]},
    {"title": "Colonialism: A Moral Reckoning", "author": "Nigel Biggar", "year": 2023, "source": "audible", "themes": ["ideology"]},
    {"title": "Empireland", "author": "Sathnam Sanghera", "year": 2024, "source": "audible", "themes": ["ideology"]},
    {"title": "End Times", "author": "Peter Turchin", "year": 2023, "source": "audible", "themes": ["ideology", "civilisation"]},
    {"title": "Blueprint for Revolution", "author": "Srdja Popovic", "year": 2024, "source": "kindle", "themes": ["ideology"]},
    {"title": "Politics on the Edge", "author": "Rory Stewart", "year": 2024, "source": "audible", "themes": ["ideology"]},
    {"title": "The Shock of History", "author": "Dominique Venner", "year": 2022, "source": "kindle", "themes": ["ideology"]},

    # ═══════════════════════════════════════════════════════════════
    # RELIGION AS SOCIAL TECHNOLOGY
    # ═══════════════════════════════════════════════════════════════
    {"title": "Dominion", "author": "Tom Holland", "year": 2022, "source": "audible", "themes": ["religion"]},
    {"title": "In the Shadow of the Sword", "author": "Tom Holland", "year": 2012, "source": "audible", "themes": ["religion"]},
    {"title": "Christendom", "author": "Peter Heather", "year": 2023, "source": "audible", "themes": ["religion"]},
    {"title": "The Rise of Western Christendom", "author": "Peter Brown", "year": 2023, "source": "audible", "themes": ["religion"]},
    {"title": "Christianity", "author": "Diarmaid MacCulloch", "year": 2012, "source": "audible", "themes": ["religion"]},
    {"title": "The Triumph of Christianity", "author": "Rodney Stark", "year": 2024, "source": "audible", "themes": ["religion"]},
    {"title": "Cities of God", "author": "Rodney Stark", "year": 2024, "source": "audible", "themes": ["religion"]},
    {"title": "How Religion Evolved", "author": "Robin Dunbar", "year": 2022, "source": "kindle", "themes": ["religion", "biology"]},
    {"title": "Inheritance", "author": "Harvey Whitehouse", "year": 2024, "source": "audible", "themes": ["religion", "biology"]},
    {"title": "The Hero with a Thousand Faces", "author": "Joseph Campbell", "year": 2024, "source": "audible", "themes": ["religion"]},
    {"title": "Islam, Authoritarianism, and Underdevelopment", "author": "Ahmet T. Kuru", "year": 2023, "source": "audible", "themes": ["religion", "geopolitics"]},
    {"title": "Defenders of the West", "author": "Raymond Ibrahim", "year": 2024, "source": "audible", "themes": ["religion", "empire"]},
    {"title": "The Word of Promise Audio Bible (NKJV)", "author": "Thomas Nelson", "year": 2025, "source": "audible", "themes": ["religion"]},
    {"title": "The God Delusion", "author": "Richard Dawkins", "year": 2015, "source": "physical", "themes": ["religion"]},
    {"title": "Outgrowing God", "author": "Richard Dawkins", "year": 2019, "source": "physical", "themes": ["religion"]},
    {"title": "The Demon-Haunted World", "author": "Carl Sagan", "year": 2024, "source": "audible", "themes": ["religion", "cognition"]},
    {"title": "Asimov's New Guide to the Bible", "author": "Isaac Asimov", "year": 2015, "source": "physical", "themes": ["religion"]},

    # ═══════════════════════════════════════════════════════════════
    # HARD CONSTRAINTS ON TECHNOLOGY
    # ═══════════════════════════════════════════════════════════════
    {"title": "Going Nuclear", "author": "Tim Gregory", "year": 2025, "source": "audible", "themes": ["technology"]},
    {"title": "Nuclear War", "author": "Annie Jacobsen", "year": 2024, "source": "audible", "themes": ["technology"]},
    {"title": "This Is How They Tell Me the World Ends", "author": "Nicole Perlroth", "year": 2024, "source": "audible", "themes": ["technology"]},
    {"title": "Ignition!", "author": "John D. Clark", "year": 2024, "source": "audible", "themes": ["technology"]},
    {"title": "Liftoff", "author": "Eric Berger", "year": 2024, "source": "audible", "themes": ["technology"]},
    {"title": "Reentry", "author": "Eric Berger", "year": 2024, "source": "audible", "themes": ["technology"]},
    {"title": "The Singularity Is Nearer", "author": "Ray Kurzweil", "year": 2024, "source": "audible", "themes": ["technology"]},
    {"title": "The Coming Wave", "author": "Mustafa Suleyman & Michael Bhaskar", "year": 2023, "source": "audible", "themes": ["technology"]},
    {"title": "Elon Musk", "author": "Walter Isaacson", "year": 2023, "source": "audible", "themes": ["technology"]},
    {"title": "The Innovators", "author": "Walter Isaacson", "year": 2022, "source": "kindle", "themes": ["technology"]},
    {"title": "Becoming Steve Jobs", "author": "Brent Schlender & Rick Tetzeli", "year": 2015, "source": "audible", "themes": ["technology"]},
    {"title": "Fossil Future", "author": "Alex Epstein", "year": 2023, "source": "audible", "themes": ["technology", "economics"]},
    {"title": "Apocalypse Never", "author": "Michael Shellenberger", "year": 2022, "source": "kindle", "themes": ["technology"]},
    {"title": "The Uninhabitable Earth", "author": "David Wallace-Wells", "year": 2019, "source": "audible", "themes": ["technology"]},
    {"title": "This Changes Everything", "author": "Naomi Klein", "year": 2019, "source": "audible", "themes": ["technology", "economics"]},
    {"title": "A Vast Machine", "author": "Paul N. Edwards", "year": 2020, "source": "audible", "themes": ["technology"]},
    {"title": "The Beginning of Infinity", "author": "David Deutsch", "year": 2024, "source": "audible", "themes": ["technology", "cognition"]},
    {"title": "Peak Human", "author": "Johan Norberg", "year": 2025, "source": "audible", "themes": ["technology"]},
    {"title": "Super Agers", "author": "Eric Topol", "year": 2025, "source": "audible", "themes": ["technology", "biology"]},
    {"title": "Surprise, Kill, Vanish", "author": "Annie Jacobsen", "year": 2024, "source": "audible", "themes": ["technology", "geopolitics"]},
    {"title": "Operation Paperclip", "author": "Annie Jacobsen", "year": 2024, "source": "audible", "themes": ["technology", "empire"]},
    {"title": "The Industrial Revolution", "author": "Patrick N. Allitt", "year": 2020, "source": "audible", "themes": ["technology", "civilisation"]},
    {"title": "The Clockwork Universe", "author": "Edward Dolnick", "year": 2023, "source": "audible", "themes": ["technology"]},
    {"title": "Creating the Twentieth Century", "author": "Vaclav Smil", "year": 2014, "source": "kindle", "themes": ["technology", "civilisation"]},

    # ═══════════════════════════════════════════════════════════════
    # COGNITIVE & RHETORICAL UPGRADES
    # ═══════════════════════════════════════════════════════════════
    {"title": "Thank You for Arguing", "author": "Jay Heinrichs", "year": 2024, "source": "audible", "themes": ["cognition"]},
    {"title": "Win Every Argument", "author": "Mehdi Hasan", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "How to Have Impossible Conversations", "author": "Peter Boghossian & James Lindsay", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "The Elements of Eloquence", "author": "Mark Forsyth", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "Rhetoric and Poetics", "author": "Aristotle", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "Plato's Republic", "author": "David Roochnik", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "The Great Ideas of Philosophy", "author": "Daniel N. Robinson", "year": 2018, "source": "audible", "themes": ["cognition"]},
    {"title": "The Structure of Scientific Revolutions", "author": "Thomas S. Kuhn", "year": 2024, "source": "audible", "themes": ["cognition"]},
    {"title": "Being and Time", "author": "Martin Heidegger", "year": 2024, "source": "audible", "themes": ["cognition"]},
    {"title": "The Spirit of the Laws", "author": "Montesquieu", "year": 2024, "source": "audible", "themes": ["cognition", "ideology"]},
    {"title": "Influence", "author": "Robert B. Cialdini", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "Pre-Suasion", "author": "Robert Cialdini", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "The Laws of Human Nature", "author": "Robert Greene", "year": 2024, "source": "audible", "themes": ["cognition"]},
    {"title": "The Master and His Emissary", "author": "Iain McGilchrist", "year": 2024, "source": "audible", "themes": ["cognition", "biology"]},
    {"title": "The Matter with Things", "author": "Iain McGilchrist", "year": 2024, "source": "physical", "themes": ["cognition", "biology"]},
    {"title": "Range", "author": "David Epstein", "year": 2024, "source": "audible", "themes": ["cognition"]},
    {"title": "Black Box Thinking", "author": "Matthew Syed", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "Rebel Ideas", "author": "Matthew Syed", "year": 2022, "source": "audible", "themes": ["cognition"]},
    {"title": "The Culture Map", "author": "Erin Meyer", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "Team of Teams", "author": "Stanley McChrystal", "year": 2015, "source": "kindle", "themes": ["cognition"]},
    {"title": "Turn the Ship Around!", "author": "L. David Marquet", "year": 2023, "source": "audible", "themes": ["cognition"]},
    {"title": "Never Split the Difference", "author": "Chris Voss & Tahl Raz", "year": 2019, "source": "audible", "themes": ["cognition"]},
    {"title": "Drive", "author": "Daniel H. Pink", "year": 2019, "source": "audible", "themes": ["cognition"]},
    {"title": "The War of Art", "author": "Steven Pressfield", "year": 2025, "source": "audible", "themes": ["cognition"]},
    {"title": "Man's Search for Meaning", "author": "Viktor E. Frankl", "year": 2020, "source": "audible", "themes": ["cognition"]},
    {"title": "A Theory of Justice", "author": "John Rawls", "year": 2020, "source": "physical", "themes": ["cognition", "ideology"]},
    {"title": "The Better Angels of Our Nature", "author": "Steven Pinker", "year": 2012, "source": "kindle", "themes": ["cognition", "civilisation"]},
    {"title": "The Pattern Seekers", "author": "Simon Baron-Cohen", "year": 2024, "source": "kindle", "themes": ["cognition", "biology"]},

    # ═══════════════════════════════════════════════════════════════
    # BIOLOGY & HUMAN NATURE
    # ═══════════════════════════════════════════════════════════════
    {"title": "Power, Sex, Suicide", "author": "Nick Lane", "year": 2025, "source": "audible", "themes": ["biology"]},
    {"title": "Transformer", "author": "Nick Lane", "year": 2023, "source": "audible", "themes": ["biology"]},
    {"title": "Life Ascending", "author": "Nick Lane", "year": 2012, "source": "kindle", "themes": ["biology"]},
    {"title": "The Evolution of Desire", "author": "David M. Buss", "year": 2025, "source": "audible", "themes": ["biology"]},
    {"title": "Determined", "author": "Robert M. Sapolsky", "year": 2024, "source": "audible", "themes": ["biology", "cognition"]},
    {"title": "How We Age", "author": "Coleen T. Murphy", "year": 2024, "source": "audible", "themes": ["biology"]},
    {"title": "Why We Die", "author": "Venki Ramakrishnan", "year": 2024, "source": "audible", "themes": ["biology"]},
    {"title": "Eve", "author": "Cat Bohannon", "year": 2023, "source": "audible", "themes": ["biology"]},
    {"title": "Epigenetics Revolution", "author": "Nessa Carey", "year": 2020, "source": "audible", "themes": ["biology"]},
    {"title": "Entangled Life", "author": "Merlin Sheldrake", "year": 2024, "source": "audible", "themes": ["biology"]},
    {"title": "I Contain Multitudes", "author": "Ed Yong", "year": 2023, "source": "audible", "themes": ["biology"]},
    {"title": "The Ape That Understood the Universe", "author": "Steve Stewart-Williams", "year": 2023, "source": "audible", "themes": ["biology"]},
    {"title": "Human Diversity", "author": "Charles Murray", "year": 2022, "source": "audible", "themes": ["biology"]},
    {"title": "A Troublesome Inheritance", "author": "Nicholas Wade", "year": 2025, "source": "audible", "themes": ["biology"]},
    {"title": "Civilized to Death", "author": "Christopher Ryan", "year": 2024, "source": "audible", "themes": ["biology", "civilisation"]},
    {"title": "The Selfish Gene", "author": "Richard Dawkins", "year": 2015, "source": "physical", "themes": ["biology"]},
    {"title": "The Blind Watchmaker", "author": "Richard Dawkins", "year": 2015, "source": "physical", "themes": ["biology"]},
    {"title": "The Greatest Show on Earth", "author": "Richard Dawkins", "year": 2015, "source": "physical", "themes": ["biology"]},
    {"title": "Ravenous", "author": "Henry Dimbleby & Jemima Lewis", "year": 2024, "source": "audible", "themes": ["biology"]},
    {"title": "Biology: The Science of Life", "author": "Stephen Nowicki", "year": 2015, "source": "audible", "themes": ["biology"]},
    {"title": "The Origin and Evolution of Earth", "author": "Robert M. Hazen", "year": 2015, "source": "audible", "themes": ["biology"]},
    {"title": "The Invention of the Jewish People", "author": "Shlomo Sand", "year": 2024, "source": "audible", "themes": ["biology", "ideology"]},
    {"title": "The Broken Spears", "author": "Miguel León-Portilla", "year": 2024, "source": "audible", "themes": ["biology", "empire"]},

    # ═══════════════════════════════════════════════════════════════
    # FICTION AS CIVILISATIONAL SIMULATION
    # ═══════════════════════════════════════════════════════════════
    {"title": "Foundation", "author": "Isaac Asimov", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "Foundation and Empire", "author": "Isaac Asimov", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "Second Foundation", "author": "Isaac Asimov", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "Prelude to Foundation", "author": "Isaac Asimov", "year": 2024, "source": "audible", "themes": ["fiction"]},
    {"title": "Forward the Foundation", "author": "Isaac Asimov", "year": 2024, "source": "audible", "themes": ["fiction"]},
    {"title": "Dune", "author": "Frank Herbert", "year": 2020, "source": "audible", "themes": ["fiction"]},
    {"title": "The Way of Kings", "author": "Brandon Sanderson", "year": 2025, "source": "audible", "themes": ["fiction"]},
    {"title": "Mistborn", "author": "Brandon Sanderson", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "The Well of Ascension", "author": "Brandon Sanderson", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "The Hero of Ages", "author": "Brandon Sanderson", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "The Count of Monte Cristo", "author": "Alexandre Dumas", "year": 2024, "source": "audible", "themes": ["fiction"]},
    {"title": "The Three Musketeers", "author": "Alexandre Dumas", "year": 2024, "source": "audible", "themes": ["fiction"]},
    {"title": "War and Peace", "author": "Leo Tolstoy", "year": 2014, "source": "kindle", "themes": ["fiction"]},
    {"title": "Brave New World", "author": "Aldous Huxley", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "Consider Phlebas", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Player of Games", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "Use of Weapons", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "Excession", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "Matter", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "Surface Detail", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Hydrogen Sonata", "author": "Iain M. Banks", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "Master and Commander", "author": "Patrick O'Brian", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "Post Captain", "author": "Patrick O'Brian", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "H.M.S. Surprise", "author": "Patrick O'Brian", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "The Pillars of the Earth", "author": "Ken Follett", "year": 2014, "source": "kindle", "themes": ["fiction"]},
    {"title": "World Without End", "author": "Ken Follett", "year": 2014, "source": "kindle", "themes": ["fiction"]},
    {"title": "Fall of Giants", "author": "Ken Follett", "year": 2014, "source": "kindle", "themes": ["fiction"]},
    {"title": "Pandora's Star", "author": "Peter F. Hamilton", "year": 2012, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Reality Dysfunction", "author": "Peter F. Hamilton", "year": 2012, "source": "kindle", "themes": ["fiction"]},
    {"title": "Pompeii", "author": "Robert Harris", "year": 2014, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Cicero Trilogy", "author": "Robert Harris", "year": 2014, "source": "kindle", "themes": ["fiction"]},
    {"title": "Gardens of the Moon", "author": "Steven Erikson", "year": 2013, "source": "kindle", "themes": ["fiction"]},
    {"title": "Exhalation", "author": "Ted Chiang", "year": 2020, "source": "audible", "themes": ["fiction"]},
    {"title": "Project Hail Mary", "author": "Andy Weir", "year": 2021, "source": "kindle", "themes": ["fiction"]},
    {"title": "Babel", "author": "R. F. Kuang", "year": 2023, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Poppy War", "author": "R. F. Kuang", "year": 2021, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Mercy of Gods", "author": "James S. A. Corey", "year": 2025, "source": "kindle", "themes": ["fiction"]},
    {"title": "Leviathan Wakes", "author": "James S. A. Corey", "year": 2021, "source": "kindle", "themes": ["fiction"]},
    {"title": "Caliban's War", "author": "James S. A. Corey", "year": 2021, "source": "kindle", "themes": ["fiction"]},
    {"title": "Wool", "author": "Hugh Howey", "year": 2013, "source": "kindle", "themes": ["fiction"]},
    {"title": "Starship Troopers", "author": "Robert A. Heinlein", "year": 2020, "source": "kindle", "themes": ["fiction"]},
    {"title": "Eagle in the Snow", "author": "Wallace Breem", "year": 2018, "source": "kindle", "themes": ["fiction"]},
    {"title": "Sixteen Ways to Defend a Walled City", "author": "K. J. Parker", "year": 2020, "source": "kindle", "themes": ["fiction"]},
    {"title": "Devices and Desires", "author": "K. J. Parker", "year": 2020, "source": "kindle", "themes": ["fiction"]},
    {"title": "The Grapes of Wrath", "author": "John Steinbeck", "year": 2012, "source": "audible", "themes": ["fiction"]},
    {"title": "A Farewell to Arms", "author": "Ernest Hemingway", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "A Place of Greater Safety", "author": "Hilary Mantel", "year": 2012, "source": "kindle", "themes": ["fiction"]},
    {"title": "A Tale of Two Cities", "author": "Charles Dickens", "year": 2018, "source": "audible", "themes": ["fiction"]},
    {"title": "Wuthering Heights", "author": "Emily Brontë", "year": 2017, "source": "audible", "themes": ["fiction"]},
    {"title": "Circe", "author": "Madeline Miller", "year": 2020, "source": "audible", "themes": ["fiction"]},
    {"title": "The Odyssey", "author": "Homer", "year": 2023, "source": "audible", "themes": ["fiction"]},
    {"title": "Life After Life", "author": "Kate Atkinson", "year": 2015, "source": "kindle", "themes": ["fiction"]},
    {"title": "Lord of the Flies", "author": "William Golding", "year": 2023, "source": "audible", "themes": ["fiction"]},
    {"title": "The Picture of Dorian Gray", "author": "Oscar Wilde", "year": 2023, "source": "audible", "themes": ["fiction"]},
    {"title": "One Day in the Life of Ivan Denisovich", "author": "Aleksandr Solzhenitsyn", "year": 2020, "source": "audible", "themes": ["fiction"]},
    {"title": "Service Model", "author": "Adrian Tchaikovsky", "year": 2025, "source": "kindle", "themes": ["fiction"]},
    {"title": "Slow Gods", "author": "Claire North", "year": 2025, "source": "kindle", "themes": ["fiction"]},
    {"title": "On Basilisk Station", "author": "David Weber", "year": 2013, "source": "kindle", "themes": ["fiction"]},
    {"title": "Hundred Years War Vol 1: Trial by Battle", "author": "Jonathan Sumption", "year": 2024, "source": "kindle", "themes": ["fiction", "empire"]},
    {"title": "Niccolo Rising", "author": "Dorothy Dunnett", "year": 2024, "source": "kindle", "themes": ["fiction"]},
    {"title": "The World of Yesterday", "author": "Stefan Zweig", "year": 2023, "source": "kindle", "themes": ["fiction", "empire"]},
    {"title": "Crime and Punishment", "author": "Fyodor Dostoyevsky", "year": 2013, "source": "kindle", "themes": ["fiction"]},
    {"title": "Ready Player One", "author": "Ernest Cline", "year": 2018, "source": "kindle", "themes": ["fiction"]},
]


def get_library_stats():
    """Return summary statistics for the library."""
    themes_count = len(THEMES)
    books_count = len(BOOKS)
    years = [b["year"] for b in BOOKS if b.get("year")]
    min_year = min(years) if years else 2012
    max_year = max(years) if years else 2025
    sources = set(b["source"] for b in BOOKS)
    return {
        "books": books_count,
        "themes": themes_count,
        "min_year": min_year,
        "max_year": max_year,
        "sources": len(sources),
    }


def get_books_by_theme():
    """Return books grouped by theme."""
    grouped = {tid: [] for tid in THEMES}
    for book in BOOKS:
        primary_theme = book["themes"][0] if book["themes"] else None
        if primary_theme and primary_theme in grouped:
            grouped[primary_theme].append(book)
    # Sort each group by year descending
    for tid in grouped:
        grouped[tid].sort(key=lambda b: (-b.get("year", 0), b["title"]))
    return grouped


def get_books_by_year():
    """Return books grouped by year."""
    grouped = {}
    for book in BOOKS:
        y = book.get("year", 0)
        if y not in grouped:
            grouped[y] = []
        grouped[y].append(book)
    # Sort each year's books by title
    for y in grouped:
        grouped[y].sort(key=lambda b: b["title"])
    return grouped
