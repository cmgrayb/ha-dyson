# Quality Gates Configuration

This file defines the quality gates and automated checks for the Dyson integration.

## 🚦 Required Quality Gates

### Code Quality Thresholds

```yaml
file_size:
  max_lines: 300
  target_lines: 200
  critical_threshold: 500

function_complexity:
  max_cyclomatic: 10
  max_cognitive: 15
  max_nesting: 4

function_size:
  max_lines: 50
  target_lines: 25

class_size:
  max_lines: 300
  target_lines: 150
```

### Linting Requirements

- **flake8**: Must pass with zero errors
- **mypy**: Must pass type checking (strategic `# type: ignore` allowed for necessary overrides)
- **bandit**: Must pass security checks
- **black**: Must be formatted
- **isort**: Imports must be sorted

**Testing Approach**: Use terminal commands directly instead of VSCode tasks:

```bash
flake8 custom_components/dyson_local/
mypy custom_components/dyson_local/
bandit -r custom_components/dyson_local/
black --check custom_components/dyson_local/
isort --check-only custom_components/dyson_local/
```

### Home Assistant Specific Patterns

- **Property Overrides**: Use `_attr_` pattern when possible
- **Type Ignores**: Only use `# type: ignore[override]` for necessary property overrides
- **Inheritance Order**: Custom base class first, then HA entity class
- **Method Signatures**: Must match parent class expectations exactly
- **Null Safety**: Use assertions for null checking where appropriate

### Coverage Requirements

- **Type Hints**: 90% coverage minimum
- **Docstrings**: 100% for public APIs
- **Error Handling**: All exceptions must be caught specifically

### Home Assistant Validation

- **hassfest**: Must pass validation
- **HACS**: Must pass HACS checks
- **Integration Load**: Must load without errors

## 🔧 Automated Checks

### Pre-commit Hooks

```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy

  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit
```

### CI/CD Pipeline

1. **Linting Stage**: Run all linters
2. **Type Checking**: Verify type annotations
3. **Security Scan**: Check for security issues
4. **HA Validation**: Run hassfest checks
5. **Integration Test**: Load in test environment

## 📋 Quality Checklist

### Architecture Review

- [ ] Single responsibility principle followed
- [ ] Dependencies properly injected
- [ ] Resources properly managed
- [ ] Error handling comprehensive

### Code Review

- [ ] All functions under 50 lines
- [ ] All files under 300 lines
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] No code duplication

### Integration Review

- [ ] Follows HA patterns
- [ ] Proper entity inheritance (custom base class first)
- [ ] Property overrides use `_attr_` pattern when possible
- [ ] Strategic `# type: ignore[override]` for necessary overrides
- [ ] Method signatures match parent expectations
- [ ] Config flow implemented
- [ ] Device registration correct
- [ ] Cleanup on unload
- [ ] Null safety with assertions

### Security Review

- [ ] Input validation present
- [ ] No credential exposure
- [ ] Secure communications
- [ ] Error messages safe

## 🎯 Compliance Targets

### Green (Excellent)

- File size < 200 lines
- Function complexity < 5
- 100% type coverage
- Zero linting errors

### Yellow (Acceptable)

- File size 200-300 lines
- Function complexity 5-10
- 90% type coverage
- Minor linting warnings

### Red (Needs Improvement)

- File size > 300 lines
- Function complexity > 10
- < 90% type coverage
- Linting errors present

## 🔄 Review Frequency

- **Daily**: Automated checks on commits
- **Weekly**: Manual code review
- **Monthly**: Architecture review
- **Release**: Full compliance audit
