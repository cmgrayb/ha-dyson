#!/bin/bash

# Post-create script for Home Assistant Dyson Integration development

echo "🚀 Setting up Home Assistant Dyson Integration development environment..."

# Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install Python dependencies for development
echo "📦 Installing Python development dependencies..."
.venv/bin/pip install -e .
.venv/bin/pip install -r requirements_dev.txt 2>/dev/null || echo "No requirements_dev.txt found, skipping..."

# Install pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
.venv/bin/pre-commit install

# Create a basic Home Assistant configuration for testing
echo "🏠 Setting up basic Home Assistant test configuration..."
mkdir -p config
if [ ! -f config/configuration.yaml ]; then
cat > config/configuration.yaml << EOF
# Basic Home Assistant configuration for testing Dyson integration

homeassistant:
  name: Dyson Development
  latitude: 37.7749
  longitude: -122.4194
  elevation: 0
  unit_system: metric
  time_zone: UTC

default_config:

logger:
  default: info
  logs:
    custom_components.dyson_local: debug

# Enable the Dyson Local integration
dyson_local:
EOF
fi

# Create symbolic link to custom_components in config
echo "🔗 Creating symbolic link to custom_components..."
ln -sf /workspaces/ha-dyson/custom_components config/custom_components

echo "✅ Development environment setup complete!"
echo ""
echo "To start Home Assistant for testing:"
echo "  hass -c config"
echo ""
echo "Or use the VS Code tasks (Ctrl+Shift+P -> Tasks: Run Task)"
