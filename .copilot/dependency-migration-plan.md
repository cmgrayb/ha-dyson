# libdyson Dependency Migration Plan

## From Vendor Bundling to PyPI Dependency

This document outlines the plan to migrate the ha-dyson integration from bundled libdyson (vendor directory) to using libdyson as a PyPI dependency. This migration is a prerequisite for submitting the integration to Home Assistant core, which requires all dependencies to be available as PyPI packages rather than bundled code.

## 🔍 **Current State Discovery**

- ✅ **libdyson-wg/libdyson already exists** as a separate GitHub repository
- ✅ **libdyson is published to PyPI** with latest version 0.8.11
- ✅ **vendor/libdyson/** contains a copy of libdyson source for development/bundling
- ✅ **Integration imports from `.vendor.libdyson`** throughout the codebase
- ⚠️ **manifest.json has no requirements field** - uses bundled approach for HACS compatibility

## 🎯 **Migration Objectives**

### **Primary Goals**

1. **Remove vendor bundling** - Delete `vendor/libdyson/` directory
2. **Add PyPI dependency** - Declare libdyson requirement in manifest.json
3. **Update all imports** - Change from `.vendor.libdyson` to `libdyson`
4. **Maintain compatibility** - Ensure no functionality regressions
5. **Version synchronization** - Use appropriate libdyson version

### **Quality Targets**

- ✅ All existing functionality preserved
- ✅ Import statements properly updated
- ✅ Version compatibility verified
- ✅ Tests continue to pass
- ✅ HACS compatibility maintained (with PyPI fallback)

## 📋 **Implementation Timeline**

### **Phase 1: Preparation (1 week)**

#### **1.1 Version Compatibility Analysis**

```bash
# Check vendor libdyson version vs PyPI version
cd custom_components/dyson_local/vendor/libdyson
git log --oneline -10  # Check recent changes
pip show libdyson      # Check PyPI version 0.8.11
```

**Tasks:**

- [ ] Compare vendor code with PyPI libdyson 0.8.11
- [ ] Identify any custom patches or modifications
- [ ] Document version differences and compatibility
- [ ] Test integration with PyPI libdyson in development

#### **1.2 Import Analysis**

```bash
# Find all vendor imports
grep -r "vendor.libdyson" custom_components/dyson_local/
```

**Expected locations:**

- `config_flow.py` - Device discovery and authentication
- `device_manager.py` - Device initialization
- `*.py` - All platform files (sensor, fan, etc.)

### **Phase 2: Migration Implementation (1 week)**

#### **2.1 Update manifest.json**

```json
{
  "domain": "dyson_local",
  "name": "Dyson",
  "codeowners": ["@libdyson-wg", "@dotvezz"],
  "config_flow": true,
  "dependencies": ["mqtt", "zeroconf"],
  "requirements": ["libdyson==0.8.11"],
  "documentation": "https://github.com/libdyson-wg/ha-dyson",
  "import_executor": true,
  "iot_class": "local_push",
  "issue_tracker": "https://github.com/libdyson-wg/ha-dyson/issues",
  "version": "1.6.0"
}
```

#### **2.2 Update Import Statements**

**Before:**

```python
from .vendor.libdyson import DEVICE_TYPE_NAMES, get_device
from .vendor.libdyson.cloud import DysonAccount
from .vendor.libdyson.const import DEVICE_TYPE_360_EYE
```

**After:**

```python
from libdyson import DEVICE_TYPE_NAMES, get_device
from libdyson.cloud import DysonAccount
from libdyson.const import DEVICE_TYPE_360_EYE
```

#### **2.3 Systematic Import Updates**

Files requiring updates (based on grep results):

- [ ] `config_flow.py` - 8 import statements
- [ ] `device_manager.py` - 3 import statements
- [ ] `utils.py` - 3 import statements
- [ ] `sensor.py` - 3 import statements
- [ ] `select.py` - 2 import statements
- [ ] `fan.py` - 1 import statement
- [ ] `entity.py` - 2 import statements
- [ ] `discovery_manager.py` - 2 import statements
- [ ] `connection.py` - 2 import statements
- [ ] `switch.py` - 1 import statement

### **Phase 3: Testing & Validation (1 week)**

#### **3.1 Development Testing**

```bash
# Install development requirements with PyPI libdyson
pip install -r requirements-dev.txt
pip install libdyson==0.8.11

# Run all tests
pytest tests/ -v

# Run quality checks
flake8 custom_components/dyson_local/
mypy custom_components/dyson_local/
```

#### **3.2 Integration Testing**

- [ ] Test device discovery via mDNS
- [ ] Test cloud authentication flow
- [ ] Test local device connection
- [ ] Test all device types (fans, purifiers, vacuums)
- [ ] Verify all entities are created correctly
- [ ] Test configuration options flow

#### **3.3 Compatibility Verification**

- [ ] Home Assistant development environment
- [ ] HACS installation (with PyPI dependency)
- [ ] Container deployment scenarios

### **Phase 4: Cleanup & Documentation (1 week)**

#### **4.1 Remove Vendor Directory**

```bash
# Remove bundled libdyson after testing
rm -rf custom_components/dyson_local/vendor/
```

#### **4.2 Update Documentation**

- [ ] Update README.md installation instructions
- [ ] Update development setup guide
- [ ] Document PyPI dependency approach
- [ ] Update HACS compatibility notes

#### **4.3 Version Management**

- [ ] Bump integration version to 1.6.0
- [ ] Tag release with migration notes
- [ ] Update changelog with dependency changes

## 🔧 **Technical Implementation**

### **Import Migration Script**

```python
#!/usr/bin/env python3
"""Script to migrate vendor imports to PyPI imports"""

import os
import re
from pathlib import Path

def migrate_imports(file_path):
    """Replace vendor.libdyson imports with libdyson imports"""
    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern to match vendor imports
    patterns = [
        (r'from \.vendor\.libdyson', 'from libdyson'),
        (r'import \.vendor\.libdyson', 'import libdyson'),
    ]

    for old_pattern, new_pattern in patterns:
        content = re.sub(old_pattern, new_pattern, content)

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"Updated imports in {file_path}")

# Run migration
component_dir = Path("custom_components/dyson_local")
for py_file in component_dir.glob("*.py"):
    migrate_imports(py_file)
```

## ⚠️ **Risk Assessment**

### **Low Risk**

- **Import changes** - Straightforward find/replace operation
- **PyPI dependency** - libdyson is already published and stable
- **Testing coverage** - Comprehensive test suite exists

### **Medium Risk**

- **Version compatibility** - Vendor code might be newer than PyPI
- **HACS installation** - Users need PyPI access for dependencies
- **Environment isolation** - Some HA installs have restricted PyPI

### **Mitigation Strategies**

1. **Thorough testing** in multiple environments before release
2. **Version pinning** to specific libdyson version (0.8.11)
3. **Rollback plan** - Keep vendor branch as backup
4. **Documentation** - Clear migration notes for users

## 🎯 **Success Criteria**

### **Functional Requirements**

- [ ] All device types connect and function correctly
- [ ] All entities are discovered and controllable
- [ ] Configuration flows work for cloud and local setup
- [ ] No import errors or dependency issues

### **Quality Requirements**

- [ ] All tests pass
- [ ] Type checking passes (mypy)
- [ ] Linting passes (flake8, black, isort)
- [ ] No security issues (bandit)

### **Integration Requirements**

- [ ] HACS installation works with PyPI dependency
- [ ] Home Assistant core requirements met
- [ ] Documentation updated and comprehensive

## 📈 **Post-Migration Benefits**

### **For Official HA Integration**

- ✅ **Core requirement met** - No bundled dependencies
- ✅ **Dependency management** - HA handles libdyson installation
- ✅ **Version control** - Clear dependency versioning
- ✅ **Security scanning** - PyPI packages are scanned

### **For Maintainers**

- ✅ **Simplified updates** - Update libdyson version in manifest
- ✅ **Reduced codebase** - Smaller integration repository
- ✅ **Clear separation** - Library vs integration concerns
- ✅ **Community contributions** - libdyson can evolve independently

### **For Users**

- ✅ **Automatic updates** - HA manages dependency updates
- ✅ **Smaller downloads** - No bundled library code
- ✅ **Better reliability** - Official PyPI package management

## 🚀 **Next Steps**

1. **Immediate**: Verify vendor vs PyPI version compatibility
2. **This week**: Implement import migration in development branch
3. **Next week**: Comprehensive testing and validation
4. **Following week**: Release with migration to PyPI dependency

This migration will position the integration perfectly for official Home Assistant core submission while maintaining all current functionality and HACS compatibility.
