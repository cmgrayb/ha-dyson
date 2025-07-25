# .copilot Directory

This directory contains coding standards, quality gates, and compliance documentation for the Dyson Home Assistant integration.

## 📁 Contents

### [`standards.md`](./standards.md)

Comprehensive coding standards and best practices for the integration, including:

- Code quality standards
- Home Assistant best practices
- Architecture guidelines
- Security requirements
- Common quality issues and solutions

### [`home-assistant-patterns.md`](./home-assistant-patterns.md)

Specific patterns for Home Assistant integration development:

- Property override handling
- Multiple inheritance patterns
- Method signature compatibility
- Null safety patterns
- Type annotation best practices

### [`compliance-report.md`](./compliance-report.md)

Current compliance status and assessment report, including:

- Refactoring achievements
- Metrics and improvements
- Remaining issues
- Next steps

### [`quality-gates.md`](./quality-gates.md)

Quality gates configuration and thresholds:

- Automated checks setup
- Quality thresholds
- CI/CD pipeline requirements
- Review processes

## 🎯 Purpose

This directory ensures the codebase maintains high quality standards and follows Home Assistant integration best practices through:

1. **Clear Standards**: Well-defined coding guidelines
2. **Automated Validation**: Quality gates and checks
3. **Progress Tracking**: Compliance monitoring
4. **Continuous Improvement**: Regular reviews and updates

## 🔍 Quick Compliance Check

To verify current compliance status:

```bash
# Run quality checks
flake8 custom_components/dyson_local/
black --check custom_components/dyson_local/
isort --check-only custom_components/dyson_local/
mypy custom_components/dyson_local/

# Check for specific patterns
grep -r "# type: ignore\[override\]" custom_components/dyson_local/  # Should find strategic overrides
grep -r "_attr_" custom_components/dyson_local/  # Should find attribute patterns
grep -r "assert.*is not None" custom_components/dyson_local/  # Should find null safety

# Check file sizes
find custom_components/dyson_local/ -name "*.py" -exec wc -l {} + | sort -n

# Run Home Assistant validation
hass --script check_config --config ./config
```

## 🎯 Quality Patterns Summary

The integration now follows these key patterns learned from quality improvements:

1. **Property Overrides**: Use `_attr_` when possible, `# type: ignore[override]` when necessary
2. **Multiple Inheritance**: Custom base class first, strategic type ignores
3. **Method Signatures**: Match parent class expectations exactly
4. **Null Safety**: Use assertions for expected state
5. **Type Coverage**: 100% annotation coverage with strategic ignores

## ✅ Current Status

**Status**: ✅ **COMPLIANT**

The integration has undergone major refactoring and now meets all established coding standards:

- Modular architecture implemented
- File sizes within limits
- Code quality standards met
- Home Assistant best practices followed

See [`compliance-report.md`](./compliance-report.md) for detailed assessment.
