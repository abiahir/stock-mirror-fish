#!/bin/bash
cd "$(dirname "$0")"

echo ""
echo " ============================================"
echo "   STOCK MIRROR FISH  |  Multi-Agent AI"
echo " ============================================"
echo ""

# Install deps
pip install -r requirements.txt --quiet

# Open browser after short delay
(sleep 4 && open "http://localhost:8080" 2>/dev/null || xdg-open "http://localhost:8080" 2>/dev/null) &

echo " Starting server at http://localhost:8080"
echo " Press Ctrl+C to stop."
echo ""

python app.py
