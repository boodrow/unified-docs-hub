#!/bin/bash
# Unified Docs Hub - Quick Setup Script

echo "🚀 Unified Docs Hub - Quick Setup"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To configure for Claude Desktop, add this to ~/Library/Application Support/Claude/claude_desktop_config.json:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "unified-docs-hub": {'
echo '      "command": "'$(pwd)'/venv/bin/python",'
echo '      "args": ["'$(pwd)'/unified_docs_hub_server.py"],'
echo '      "env": {'
echo '        "GITHUB_TOKEN": "your-github-token-here"'
echo '      }'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "For automated updates, run: ./setup_automated_indexing.sh"
echo ""
echo "To start using, restart Claude Desktop and use the unified_search() tool!"
