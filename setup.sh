#!/bin/bash
set -e
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
echo ""
echo "✅ CLI CivilEng installed. Activate with: source venv/bin/activate"
echo "   Then run: cli-civileng --help"
