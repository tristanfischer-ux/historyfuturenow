#!/bin/bash
# Batch regenerate remaining articles with Gemini TTS (Puck/Kore)
# Deploys every BATCH_SIZE articles
set -e

BATCH_SIZE=5
BUILD_DIR="$(dirname "$0")"
SITE_DIR="$BUILD_DIR/../hfn-site-output"
AUDIO_DIR="$SITE_DIR/audio"

# Articles still needing Puck/Kore voices
ARTICLES=(
  "are-europeans-fundamentally-racist"
  "crisis-or-an-explanation"
  "dont-confuse-what-is-legal"
  "emigration-colonies-of-the-mind"
  "platform-technologies"
  "prisons-we-never-used-to-have"
  "robotics-and-slavery"
  "rome-vs-persia"
  "roots-a-historical-understanding"
  "the-150-year-life"
  "the-builders-are-dying"
  "the-death-of-the-fourth-estate"
  "the-empty-cradle-bargain"
  "the-gates-of-nations"
  "the-great-emptying"
  "the-immorality-of-climate-change"
  "the-long-term-impact-of-covid"
  "the-new-literacy"
  "the-north-african-threat"
  "the-paradox-of-mass-migration"
  "the-perils-of-prediction"
  "the-renewables-and-battery"
  "the-return-of-the-state-factory"
  "the-rise-of-the-west"
  "the-robot-bargain"
  "the-scramble-for-the-solar-system"
  "the-silence-of-the-scribes"
  "the-unintended-consequences-of-war"
  "the-war-in-ukraine"
  "the-wests-romance-with-free-trade"
  "vertical-farming"
  "what-does-it-take-to-get-europeans"
  "what-happens-when-china"
  "what-the-history-of-immigration"
  "where-are-all-the-jobs-going"
  "who-are-the-losers"
  "who-benefits-from-our-increased"
  "who-guards-the-guards"
  "why-buying-cheap-imported"
  "why-china-could-invade-taiwan"
  "why-do-we-need-the-military"
  "why-god-needs-the-government"
  "why-is-bisexuality"
  "why-land-deals-in-africa"
  "why-the-nuclear-family"
)

cd "$BUILD_DIR"

count=0
total=${#ARTICLES[@]}
echo "=== Batch regeneration: $total articles ==="
echo ""

for slug in "${ARTICLES[@]}"; do
  count=$((count + 1))
  echo "[$count/$total] Generating: $slug"
  
  PYTHONUNBUFFERED=1 python3 generate_audio.py --article "$slug" --force || {
    echo "  FAILED: $slug — continuing..."
    continue
  }
  
  # Deploy every BATCH_SIZE articles
  if [ $((count % BATCH_SIZE)) -eq 0 ]; then
    echo ""
    echo "=== Deploying batch (articles 1-$count of $total) ==="
    cd "$BUILD_DIR"
    python3 build.py
    cd "$SITE_DIR"
    vercel --prod --yes
    echo "=== Deploy complete ==="
    echo ""
  fi
done

# Final deploy if there are remaining articles
if [ $((count % BATCH_SIZE)) -ne 0 ]; then
  echo ""
  echo "=== Final deploy (all $total articles) ==="
  cd "$BUILD_DIR"
  python3 build.py
  cd "$SITE_DIR"
  vercel --prod --yes
  echo "=== Deploy complete ==="
fi

echo ""
echo "=== ALL DONE: $total articles regenerated ==="
