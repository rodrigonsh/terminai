#!/bin/bash
# Terminai Installation Script

set -e

echo "🚀 Installing Terminai..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python $PYTHON_VERSION is too old. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Install the package
echo "📦 Installing terminai package..."
pip3 install -e .

# Create configuration directory
echo "⚙️  Setting up configuration..."
mkdir -p ~/.terminai
if [ ! -f ~/.terminai/config.json ]; then
    cp config/default.json ~/.terminai/config.json
    echo "✅ Configuration file created at ~/.terminai/config.json"
else
    echo "⚠️  Configuration file already exists at ~/.terminai/config.json"
fi

# Create logs directory
mkdir -p ~/.terminai/logs

echo ""
echo "🎉 Terminai installed successfully!"
echo ""
echo "Usage:"
echo "  terminai                    # Start the terminal"
echo "  terminai --help            # Show help"
echo ""
echo "Configuration:"
echo "  Edit ~/.terminai/config.json to set up LLM providers"
echo ""
echo "Next steps:"
echo "  1. Add your API keys to ~/.terminai/config.json"
echo "  2. Run 'terminai' to start using the intelligent terminal"
echo ""
echo "Available LLM providers:"
echo "  - OpenAI (GPT models)"
echo "  - Anthropic (Claude models)"
echo "  - Google (Gemini models)"
echo "  - DeepSeek"
echo "  - OpenRouter"
echo ""
echo "For more information, see the README.md file"
