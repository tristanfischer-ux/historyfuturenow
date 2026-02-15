#!/usr/bin/env python3
"""
History Future Now — Editorial Illustration Prompt Generator

Generates Gemini 3.0 Pro image prompts for all 54 articles,
in the style of The Economist's conceptual editorial illustrations.

Outputs image_prompts.json with prompts at three sizes:
  - hero (1200x675)  — article header
  - card (600x400)   — homepage/section cards
  - thumb (300x200)  — related articles, search
"""

import json
from pathlib import Path

STYLE_PREFIX = (
    "Editorial illustration for a serious analytical magazine about history and geopolitics. "
    "Conceptual and metaphorical, not literal or photorealistic. "
    "Bold flat shapes with clean geometric composition. "
    "Palette: muted earth tones (warm cream, deep crimson #c43425, navy blue, ochre, olive) "
    "with one or two vivid accent colours. "
    "No text, no lettering, no words, no logos in the image. "
    "Inspired by Noma Bar, Christoph Niemann, and the conceptual illustration tradition "
    "of The Economist magazine covers. "
    "Sophisticated, intellectual, slightly provocative. "
    "Suitable for a publication about historical forces shaping the future. "
)

SIZES = {
    "hero":  {"width": 1200, "height": 675, "suffix": "Wide panoramic composition."},
    "card":  {"width": 600,  "height": 400, "suffix": "Compact composition, clear focal point."},
    "thumb": {"width": 300,  "height": 200, "suffix": "Simple iconic composition, reads well at small size."},
}

# Hand-crafted subject prompts for each article
ARTICLE_SUBJECTS = {
    "a-frozen-society-the-long-term-implications-of-nsas-secrets": (
        "A human eye reflected in a surveillance camera lens, with frost crystals spreading "
        "across the surface. Binary code fading into ice. The chill of total surveillance."
    ),
    "big-european-electricity-utilities-are-facing-an-existential-crisis-how-did-this-happen-and-what-should-they-do": (
        "A massive cooling tower cracking apart, with solar panels and wind turbines growing "
        "through the cracks like plants. Old energy infrastructure crumbling into new."
    ),
    "cassandra-time-to-give-up-on-predicting-climate-change": (
        "The figure of Cassandra from Greek mythology, silhouetted against a burning horizon. "
        "She points at rising thermometer shapes while figures turn their backs."
    ),
    "china-has-many-of-the-characteristics-of-an-emerging-colonial-power-how-does-it-compare-historically": (
        "A Chinese dragon coiling around the African continent, its scales morphing into "
        "infrastructure: railways, ports, bridges. Colonial-era ships ghosted in background."
    ),
    "clash-of-titans-how-the-warrior-ethos-and-judeo-christian-monotheism-shaped-the-soul-of-the-west": (
        "A sword and a cross merged into a single object, casting a long shadow shaped like "
        "the map of Europe. Viking runes and cathedral arches in the background geometry."
    ),
    "crisis-or-an-explanation-on-the-origins-of-the-decline-of-the-west": (
        "A classical Greek column crumbling from the top down, with the rubble forming the "
        "skyline of a modern Western city. Sunset colours, long shadows, a tilting compass."
    ),
    "dealing-with-the-consequences-of-climate-chance-inaction-the-impact-of-food": (
        "A dinner plate cracking in half: one side lush crops, the other parched desert. "
        "A thermometer bisects the plate vertically. Fork and knife framing the scene."
    ),
    "debt-jubilees-and-hyperinflation-why-history-shows-that-this-might-be-the-way-forward-for-us-all": (
        "A wheelbarrow overflowing with banknotes tipping over, the notes morphing into "
        "confetti. In the background, ancient Mesopotamian clay tablets with debt records. "
        "A broken chain link at the centre."
    ),
    "emigration-colonies-of-the-mind-and-space": (
        "Human silhouettes walking across a bridge made of stars and constellations, "
        "connecting Earth to a distant planet. Footprints from Africa to the cosmos. "
        "Deep navy and gold palette."
    ),
    "establishing-a-price-floor-for-energy": (
        "A floor made of solar panels and oil barrels, with a price tag dangling from a "
        "balance scale. One side holds a sun, the other a barrel of crude oil. "
        "Clean geometric composition."
    ),
    "europe-rearms-why-the-continent-that-invented-total-war-is-spending-800-billion-on-defence": (
        "The map of Europe forming the shape of a shield, with medieval armour plates "
        "overlapping modern military radar dishes. A red NATO star at the centre. "
        "Dark navy and crimson palette."
    ),
    "forging-peace-from-centuries-of-war-to-ukraines-future": (
        "A blacksmith's anvil shaped like Ukraine, with a hammer striking it. Sparks fly "
        "upward forming dove silhouettes. Swords being bent into ploughshares in the background."
    ),
    "green-is-not-red-but-blue-environmentalism-and-the-mystery-of-right-wing-opposition": (
        "A chameleon sitting on a barricade, its skin shifting between green, red, and blue. "
        "Political rosettes and wind turbines in background. The colours bleed into each other."
    ),
    "hinkley-point-decision-is-really-about-china-and-brexit": (
        "A nuclear power plant with a Chinese dragon wrapped around one cooling tower "
        "and a British Union Jack flag on the other. The English Channel between them."
    ),
    "history-is-written-by-the-winners-and-europeans-are-losing": (
        "A giant quill pen writing on a scroll, but the ink is running out. "
        "The written text morphs into the silhouettes of African and Asian figures "
        "who are picking up their own pens. European figures fade in the background."
    ),
    "is-democracy-the-opium-of-the-masses": (
        "A ballot box shaped like a poppy flower, with voters sleepwalking toward it. "
        "Smoke rises from the box like incense. Classical columns frame the scene."
    ),
    "jobs-first-get-rid-of-expensive-westerners-second-get-rid-of-people-entirely": (
        "A factory assembly line where Western worker silhouettes are replaced by "
        "Asian worker silhouettes, which are then replaced by robotic arms. "
        "A conveyor belt running left to right showing the progression."
    ),
    "keynes-and-hayek-are-both-dead-and-wrong": (
        "Two gravestones side by side, one marked with a Keynesian demand curve, "
        "the other with Hayek's price signal. Both are crumbling. "
        "A question mark grows between them like a plant."
    ),
    "lets-talk-about-sex-does-the-separation-of-pleasure-and-procreation-mean-the-end-of-people": (
        "A contraceptive pill splitting into two halves: one side shows a heart symbol, "
        "the other a baby. Between them, a downward-trending population graph. "
        "Warm tones, clinical geometry."
    ),
    "platform-technologies-how-foundational-technologies-of-the-past-show-us-the-foundational-technologies-of-the-future": (
        "A tree with roots made of historical inventions (printing press, steam engine, "
        "lightbulb) and branches growing into modern icons (microchip, solar panel, DNA helix). "
        "Cross-section view."
    ),
    "prisons-we-never-used-to-have-them-will-they-exist-in-the-future": (
        "Prison bars dissolving into digital pixels at the top, while at the bottom they "
        "grow from stocks and pillories. A timeline runs vertically. "
        "Grey and ochre palette."
    ),
    "robotics-and-slavery": (
        "A human hand and a robotic hand reaching toward each other, connected by "
        "chains that are dissolving into circuit board traces. Industrial revolution "
        "gears morph into microchips in the background."
    ),
    "rome-vs-persia-and-the-transfer-of-strategic-technologies-to-china": (
        "A Roman eagle and a Persian lion facing each other across the Silk Road, "
        "while a Chinese dragon below them gathers scrolls and blueprints. "
        "Terracotta and lapis lazuli colours."
    ),
    "roots-a-historical-understanding-of-climate-change-denial-creationism-and-slavery-1629-1775": (
        "A tree with three distinct root systems intertwined underground: one shaped like "
        "chains, one like a Bible, one like a smokestacks. The roots connect beneath the soil. "
        "Map of the American South in background."
    ),
    "a-lost-generation-why-the-personal-story-of-the-beautiful-yulia-is-also-our-story": (
        "A young woman's silhouette standing at a crossroads where all paths lead downward. "
        "One path to a degree scroll, another to a suitcase, another to an empty purse. "
        "Muted tones of loss and possibility."
    ),
    "are-europeans-fundamentally-racist": (
        "A mirror reflecting the map of Europe, but the reflection shows colonial-era "
        "imagery: ships, plantation fields, divided territories. The mirror has a crack "
        "running through it."
    ),
    "dont-confuse-what-is-legal-with-what-is-morally-right": (
        "A gavel and a compass sitting on opposite sides of a scale. The gavel side "
        "tips down but the compass points upward. Legal documents and moral philosophy "
        "books scattered around."
    ),
    "why-buying-cheap-imported-products-is-more-expensive-for-individuals-and-not-just-society": (
        "A shopping cart overflowing with cheap goods, but its wheels are crushing "
        "a factory and houses beneath it. Price tags hang like anchors. "
        "Consumer packaging with hidden costs revealed."
    ),
    "why-the-nuclear-family-needs-to-die-in-order-for-us-to-live": (
        "A white picket fence around a small house, cracking and breaking apart to reveal "
        "a larger, interconnected community web behind it. Extended family silhouettes "
        "reaching through the gaps."
    ),
    "the-150-year-life-how-radical-longevity-will-transform-our-world": (
        "A human figure stretching like taffy across a timeline from cradle to 150, "
        "with life stages compressed and expanded. DNA helixes spiralling around them. "
        "Hourglass running impossibly long."
    ),
    "the-death-of-the-fourth-estate-what-the-collapse-of-newspapers-means-for-democracy-power-and-truth": (
        "A printing press crumbling into digital dust, with newspapers falling like autumn "
        "leaves. A flashlight (representing truth) flickers and dims. Democracy's pillars "
        "losing their fourth column."
    ),
    "the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people": (
        "An hourglass made of human silhouettes, with figures falling from top to bottom "
        "as sand. The bottom half is nearly empty. A nursery crib dissolves into dust. "
        "Empty classroom chairs in the background."
    ),
    "the-immorality-of-climate-change-a-reflection-on-slavery-and-the-civil-war": (
        "Chains made of smokestacks and exhaust pipes, connecting historical plantation "
        "silhouettes to modern fossil fuel infrastructure. A moral compass spins in the centre."
    ),
    "the-long-term-impact-of-covid-19": (
        "A virus particle acting as a wrecking ball, smashing through interconnected "
        "global supply chain lines. Some broken connections regrow as local networks. "
        "Pre and post pandemic world divided by the impact."
    ),
    "the-north-african-threat-and-mediterranean-reunification": (
        "The Mediterranean Sea as a mirror reflecting North Africa and Southern Europe "
        "as two halves of the same face. Migration boats dot the surface like stitches "
        "connecting the two halves."
    ),
    "the-paradox-of-mass-migration-and-robots-in-the-age-of-automation": (
        "Two conveyor belts crossing: one carries migrant worker silhouettes moving right, "
        "the other carries robots moving left. They meet in an impossible intersection. "
        "A question mark at the centre."
    ),
    "the-perils-of-prediction-lessons-from-history-on-navigating-an-uncertain-future": (
        "A crystal ball cracked into pieces, each shard showing a different failed prediction. "
        "A compass spins wildly. Historical almanacs and modern charts surround the scene. "
        "Foggy horizon."
    ),
    "the-renewables-and-battery-revolution": (
        "A giant battery powering a city of the future, with solar panels as rooftops "
        "and wind turbines as trees. Fossil fuel plants shrink into the distance. "
        "An exponential curve rises in the sky."
    ),
    "the-rise-of-the-west-was-based-on-luck-that-has-run-out": (
        "A four-leaf clover wilting, with each leaf representing a different Western advantage: "
        "geography, timing, resources, conquest. The clover sits on a tilting globe. "
        "Dawn in the East, dusk in the West."
    ),
    "the-unintended-consequences-of-war-how-the-loss-of-young-men-transformed-womens-roles-in-society-and-ushered-in-the-welfare-state": (
        "Rows of war memorial crosses casting long shadows that transform into silhouettes "
        "of women entering factories and voting booths. A Rosie-the-Riveter-style figure "
        "emerges from the shadows."
    ),
    "the-war-in-ukraine-escalation-miscalculation-and-the-path-to-peace": (
        "A chess board with the map of Ukraine as the surface. Russian and NATO chess pieces "
        "face each other across the board. Some pieces are toppled. "
        "A narrow golden path threads between them."
    ),
    "the-wests-romance-with-free-trade-is-over-why": (
        "A wedding ring cracking in half, with one side showing container ships and the "
        "other showing tariff walls. Trade documents serve as a divorce decree. "
        "Heart-shaped globe breaking apart."
    ),
    "vertical-farming-the-electrical-convergence-power-transport-and-agriculture": (
        "A skyscraper with each floor growing crops under LED lights, connected to "
        "solar panels on the roof and electric vehicles at the base. Cross-section view "
        "showing convergence of power, transport, agriculture."
    ),
    "what-does-it-take-to-get-europeans-to-have-a-revolution": (
        "A pressure cooker shaped like Europe, with the lid about to blow off. "
        "Steam forms the silhouettes of revolutionary figures from 1789, 1848, 1989. "
        "A thermometer shows rising social temperature."
    ),
    "what-happens-when-china-becomes-the-largest-economy-in-the-world": (
        "Two bars on a bar chart crossing: the falling American flag bar and the rising "
        "Chinese flag bar. They form an X shape. A globe tilts toward the East. "
        "Gold and crimson palette."
    ),
    "what-the-history-of-immigration-teaches-us-about-europes-future": (
        "Waves of human silhouettes flowing into the map of Europe from multiple directions, "
        "layered like geological strata showing centuries of migration. "
        "Roman, Ottoman, modern refugee waves distinguished by colour."
    ),
    "where-are-all-the-jobs-going-lessons-from-the-first-industrial-revolution-and-150-years-of-pain": (
        "A factory from the Industrial Revolution era morphing into a modern automated "
        "facility, with workers shrinking in number at each stage. "
        "A 150-year timeline runs along the bottom."
    ),
    "who-are-the-losers-in-the-energy-revolution": (
        "A trophy podium where fossil fuel companies fall off while renewable energy "
        "companies climb on. Oil rigs sink while solar farms rise. "
        "Stock ticker tape surrounds the scene."
    ),
    "who-benefits-from-our-increased-social-fragmentation": (
        "A shattered mirror reflecting a fragmented society, with tech company logos "
        "visible in the cracks. Each shard shows a different echo chamber. "
        "A puppet master's hands visible at the top."
    ),
    "why-china-could-invade-taiwan-and-get-away-with-it": (
        "The island of Taiwan as a semiconductor chip, with Chinese military vessels "
        "circling it like electrons around a nucleus. The chip glows gold. "
        "Pacific Ocean in dark navy."
    ),
    "why-do-we-need-the-military-securing-energy-supplies-and-trade-routes": (
        "Aircraft carriers and warships forming a protective chain along maritime trade "
        "routes on a world map. Oil pipelines and shipping lanes glow red. "
        "Military and energy infrastructure intertwined."
    ),
    "why-god-needs-the-government-multiculturalism-vs-monotheism": (
        "Religious symbols (cross, crescent, Star of David) placed inside a government "
        "building dome. The dome cracks where the symbols press against each other. "
        "Multicultural crowd below."
    ),
    "why-is-bisexuality-becoming-mainstream": (
        "A Venn diagram with two overlapping circles in pink and blue, the overlap "
        "forming a gradient purple. Human silhouettes stand throughout all three areas. "
        "Clean, modern, non-judgmental composition."
    ),
    "why-land-deals-in-africa-could-make-the-great-irish-famine-a-minor-event": (
        "The African continent as a dinner plate being carved up by oversized forks "
        "and knives held by distant hands. Crop fields visible on the continent's surface. "
        "A ghosted image of Ireland's famine in the corner."
    ),
}


def generate_prompts():
    """Build the full prompts JSON for all articles at all sizes."""
    search_index_path = Path(__file__).parent.parent / "hfn-site-output" / "search-index.json"
    articles = json.loads(search_index_path.read_text(encoding="utf-8"))

    prompts = []
    for article in articles:
        slug = article["slug"]
        subject = ARTICLE_SUBJECTS.get(slug)
        if not subject:
            print(f"  WARNING: No subject prompt for {slug} -- skipping")
            continue

        for size_key, size_info in SIZES.items():
            full_prompt = (
                f"{STYLE_PREFIX}"
                f"{subject} "
                f"{size_info['suffix']} "
                f"Image dimensions: {size_info['width']}x{size_info['height']} pixels."
            )
            prompts.append({
                "slug": slug,
                "title": article["title"],
                "section": article["section"],
                "size": size_key,
                "width": size_info["width"],
                "height": size_info["height"],
                "prompt": full_prompt,
                "output_path": f"images/articles/{slug}/{size_key}.webp",
            })

    return prompts


def main():
    prompts = generate_prompts()

    output_path = Path(__file__).parent / "image_prompts.json"
    output_path.write_text(
        json.dumps(prompts, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    n_articles = len(set(p["slug"] for p in prompts))
    print(f"Generated {len(prompts)} prompts for {n_articles} articles")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
