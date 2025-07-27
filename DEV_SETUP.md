# Development Environment Setup

This repository includes a complete devcontainer configuration that automatically sets up the development environment for the Dyson Home Assistant integration.

## Automatic Setup

When you open this repository in VS Code with the Dev Containers extension, the following will be automatically configured:

1. **Python Virtual Environment**: A `.venv` directory with Python 3.12 and all required dependencies
2. **VS Code Settings**: Proper Python interpreter path and import resolution for Home Assistant modules
3. **Development Tools**: Black, isort, flake8, mypy, bandit, and pre-commit hooks
4. **Home Assistant Test Config**: Basic configuration in `./config` for testing

## What Happens During Setup

The devcontainer automatically runs a post-create script that:

- Creates a Python virtual environment in `.venv/`
- Installs the integration package in editable mode
- Installs all development dependencies from `requirements_dev.txt`
- Sets up pre-commit hooks for code quality
- Creates a basic Home Assistant configuration for testing
- Sets up symbolic links for the custom component

## Manual Setup (if needed)

If you need to recreate the virtual environment manually:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install -r requirements_dev.txt

# Install pre-commit hooks
pre-commit install
```

## Verification

After setup, verify everything is working:

1. Open any Python file - VS Code should show no import errors for `homeassistant` modules
2. Run quality checks: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run All Quality Checks"
3. Test Home Assistant: `Ctrl+Shift+P` → "Tasks: Run Task" → "Start Home Assistant Development"

## VS Code Configuration

The devcontainer automatically configures VS Code with:

- Python interpreter: `./.venv/bin/python`
- Import resolution: `./.venv/lib/python3.12/site-packages`
- Linting and formatting tools enabled
- Format on save enabled

No additional VS Code configuration should be needed.

## Troubleshooting

If you encounter import resolution issues:

1. Check that VS Code is using the correct Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" → choose `./.venv/bin/python`
2. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Verify the virtual environment: `which python` should show `.venv/bin/python` when in the activated environment
