# Development Environment Setup

This repository includes a complete devcontainer configuration that automatically sets up the development environment for the Dyson Home Assistant integration.

## 🏆 Platinum Status Architecture

This integration achieves **Platinum status** by using external dependencies instead of vendored code:

- **Primary Dependency**: [`libdyson-neon`](https://pypi.org/project/libdyson-neon/) - External package for Dyson device communication
- **Clean Architecture**: No vendored dependencies in the integration code
- **Modern Standards**: Follows Home Assistant Core integration requirements

## Automatic Setup

When you open this repository in VS Code with the Dev Containers extension, the following will be automatically configured:

1. **Python Virtual Environment**: A `.venv` directory with Python 3.12 and all required dependencies
2. **External Dependencies**: `libdyson-neon` package automatically installed
3. **VS Code Settings**: Proper Python interpreter path and import resolution for Home Assistant modules
4. **Development Tools**: Black, isort, flake8, mypy, bandit, and pre-commit hooks
5. **Home Assistant Test Config**: Basic configuration in `./config` for testing

## What Happens During Setup

The devcontainer automatically runs a post-create script that:

- Creates a Python virtual environment in `.venv/`
- Installs the integration package in editable mode
- **Installs `libdyson-neon`** - The external dependency package
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

# Install the external dependency first
pip install libdyson-neon

# Install integration in editable mode
pip install -e .

# Install development dependencies
pip install -r requirements_dev.txt

# Install pre-commit hooks
pre-commit install
```

## Development Dependencies

### Core Dependencies

- **libdyson-neon**: External package for Dyson device communication
- **homeassistant**: For integration development and testing

### Development Tools

- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking
- **bandit**: Security analysis
- **pre-commit**: Git hooks for quality assurance
- **pytest**: Testing framework

## Verification

After setup, verify everything is working:

1. **Import Resolution**: Open any Python file - VS Code should show no import errors for `homeassistant` or `libdyson` modules
2. **Quality Checks**: Run `Ctrl+Shift+P` → "Tasks: Run Task" → "Run All Quality Checks"
3. **External Dependency**: Verify libdyson imports work:
   ```python
   from libdyson import get_device, DEVICE_TYPE_PURE_COOL
   ```
4. **Home Assistant**: Test with `Ctrl+Shift+P` → "Tasks: Run Task" → "Start Home Assistant Development"

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_config_flow.py -v

# Run with coverage
pytest tests/ --cov=custom_components.dyson_local
```

### Integration Testing

```bash
# Start Home Assistant in development mode
hass --config ./config --debug

# Validate configuration
hass --config ./config --script check_config
```

## Quality Assurance

### Available Tasks

Use `Ctrl+Shift+P` → "Tasks: Run Task" to access:

- **Run All Quality Checks**: Complete validation (flake8, black, isort, mypy, bandit)
- **Format All Code**: Auto-format with black and isort
- **Run Tests**: Execute pytest test suite
- **Run Pre-commit**: Run all pre-commit hooks

### Manual Commands

```bash
# Formatting
black custom_components/dyson_local/
isort custom_components/dyson_local/

# Linting
flake8 custom_components/dyson_local/

# Type checking
mypy custom_components/dyson_local/

# Security analysis
bandit -r custom_components/dyson_local/

# All checks
pre-commit run --all-files
```

## Architecture Notes

### External Dependencies

The integration uses `libdyson-neon` as an external dependency rather than vendoring the code. This provides:

- **Easier maintenance**: Updates through package management
- **Better separation**: Clear boundaries between integration and device library
- **Platinum compliance**: Meets Home Assistant Core integration standards

### Import Structure

```python
# Correct - External dependency
from libdyson import get_device, DEVICE_TYPE_PURE_COOL
from libdyson.dyson_device import DysonDevice
from libdyson.exceptions import DysonException

# Old pattern - No longer used
# from .vendor.libdyson import get_device  # ❌ Removed
```

### Development Workflow

1. Make changes to integration code
2. External `libdyson-neon` changes require separate package update
3. Run quality checks before committing
4. Test with real or mocked devices

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'libdyson'`:

```bash
# Ensure external dependency is installed
pip install libdyson-neon

# Or reinstall all dependencies
pip install -r requirements_dev.txt
```

### VS Code Python Path

Ensure VS Code is using the correct Python interpreter:

1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Choose `.venv/bin/python`

### Pre-commit Issues

If pre-commit hooks fail:

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Run manually
pre-commit run --all-files
```

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
