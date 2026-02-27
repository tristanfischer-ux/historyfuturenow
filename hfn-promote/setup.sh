#!/bin/bash
set -e
echo "═══════════════════════════════════════"
echo "  HFN Promote — Setup"
echo "═══════════════════════════════════════"
cd "$(dirname "$0")"
if [ ! -f ".env" ]; then cp .env.example .env; echo "  Created .env — edit with your API key"; fi
if [ ! -d "venv" ]; then
  echo "  Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
echo "  Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  Installing Playwright Chromium..."
playwright install chromium 2>/dev/null
echo ""
echo "  ✓ Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your Anthropic API key"
echo "  2. source venv/bin/activate"
echo "  3. python hfn.py ingest"
echo "  4. python hfn.py login x"
echo "  5. python hfn.py login linkedin"
echo "  6. python hfn.py dashboard"
echo "═══════════════════════════════════════"
