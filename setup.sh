#!/bin/bash

# Check if Homebrew is installed
if ! command -v brew &> /dev/null
then
    echo "❌ Homebrew not found. Please install Homebrew first."
    echo "🔗 You can install it by running:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

# Install Python using Homebrew
echo "ℹ️ Installing Python..."
brew install python
echo "✅ Python installation complete."

# Install dependencies
echo "ℹ️Installing other dependencies..."
pip3 install requests==2.31
pip3 install pathlib==1.0.1
pip3 install urllib3==1.26.17

# Make the main script executable
chmod +x send_figma_tests_all_tests.py

echo "✅ Dependencies installed successfully! Script send_figma_tests_all_tests.py is now executable." 