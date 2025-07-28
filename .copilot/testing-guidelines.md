# Testing Guidelines

This document provides specific guidelines for testing the Dyson Home Assistant integration.

## 🧪 Testing Approach

### ⚠️ Important: Use Terminal Commands Only

**Always use terminal commands directly instead of VSCode tasks** for testing and quality checks. VSCode task outputs are not accessible for validation.

### 🚀 Quick Start: Pre-Push Preparation

For convenience, there's a VSCode task that runs the complete pre-push sequence:

**VSCode Task: "Prepare for Push (Pre-commit Ready)"**
- Access via Command Palette: `Ctrl+Shift+P` → "Tasks: Run Task" → "Prepare for Push (Pre-commit Ready)"
- Runs: Flake8 → isort → pytest → Black (in that order)
- Provides clear status indicators for each step
- Stops on first failure for immediate feedback

## 🔧 Quality Check Commands

### Code Quality

```bash
# Linting
flake8 custom_components/dyson_local/

# Type checking
mypy custom_components/dyson_local/

# Security scanning
bandit -r custom_components/dyson_local/

# Code formatting check
black --check custom_components/dyson_local/

# Import sorting check
isort --check-only custom_components/dyson_local/
```

### Code Formatting

```bash
# Apply formatting
black custom_components/dyson_local/

# Sort imports
isort custom_components/dyson_local/
```

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=custom_components.dyson_local --cov-report=term-missing
```

### Integration Tests

```bash
# Check Python syntax
python3 -m py_compile custom_components/dyson_local/__init__.py

# Validate Home Assistant config
hass --script check_config --config ./config

# Test device creation
python3 -c "
from custom_components.dyson_local.vendor.libdyson import get_device
device = get_device('test', 'test', '438M')
print('Device creation test:', 'PASS' if device else 'FAIL')
"
```

### File Structure Analysis

```bash
# Check file sizes (should be under 300 lines)
find custom_components/dyson_local/ -name "*.py" -exec wc -l {} + | sort -n

# Check for compliance patterns
grep -r "# type: ignore\[override\]" custom_components/dyson_local/
grep -r "_attr_" custom_components/dyson_local/
grep -r "assert.*is not None" custom_components/dyson_local/
```

## 🎯 Complete Quality Check Sequence

Run this complete sequence to verify code quality:

```bash
#!/bin/bash
echo "Running complete quality checks..."

echo "1. Code formatting..."
black custom_components/dyson_local/
isort custom_components/dyson_local/

echo "2. Linting..."
flake8 custom_components/dyson_local/

echo "3. Type checking..."
mypy custom_components/dyson_local/

echo "4. Security scanning..."
bandit -r custom_components/dyson_local/

echo "5. Running tests..."
pytest tests/ -v

echo "6. Syntax validation..."
python3 -m py_compile custom_components/dyson_local/__init__.py

echo "All quality checks completed!"
```

## 🚨 Pre-commit Checklist

Before committing changes, run:

1. **Format code**: `black custom_components/dyson_local/ && isort custom_components/dyson_local/`
2. **Run linting**: `flake8 custom_components/dyson_local/`
3. **Check types**: `mypy custom_components/dyson_local/`
4. **Run tests**: `pytest tests/ -v`
5. **Validate syntax**: `python3 -m py_compile custom_components/dyson_local/__init__.py`

## 📝 Testing Notes

- **Never use VSCode tasks**: Use terminal commands directly for consistent, verifiable results
- **Verify outputs**: Always check command outputs for errors or warnings
- **Fix issues incrementally**: Address one type of issue at a time
- **Test device creation**: Verify that device creation works for all supported device types
- **Check Home Assistant compatibility**: Validate that changes work with current HA version
