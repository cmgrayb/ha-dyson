# libdyson Extraction Plan

## Converting Vendor Library to Standalone PyPI Package

This document outlines the detailed plan to extract the embedded `vendor/libdyson` library into a standalone PyPI package, which is essential for:

- **Official HA Integration**: Core integrations cannot include vendor code
- **Maintainability**: Easier updates and version management
- **Reusability**: Other projects can use the library
- **Quality**: Professional package distribution standards

## 📊 **Current State Analysis**

### **Library Structure**

```
custom_components/dyson_local/vendor/libdyson/
├── __init__.py                 # Main exports and factory functions
├── const.py                   # Device types and constants
├── discovery.py               # mDNS device discovery
├── dyson_device.py           # Base device class
├── dyson_*.py                # Device-specific implementations (12 files)
├── exceptions.py             # Custom exceptions
├── utils.py                  # Utility functions
└── cloud/                    # Cloud API integration
    ├── __init__.py
    ├── account.py            # Account management
    ├── cloud_*.py           # Cloud device classes
    ├── device_info.py       # Device information
    ├── regions.py           # Regional API endpoints
    └── utils.py             # Cloud utilities
```

### **Integration Dependencies**

```python
# 33 import statements across 12 integration files
from .vendor.libdyson import get_device, DEVICE_TYPE_NAMES
from .vendor.libdyson.cloud import DysonAccount, DysonDeviceInfo
from .vendor.libdyson.exceptions import DysonException, DysonInvalidAuth
from .vendor.libdyson.const import MessageType, CleaningMode
# ... many more
```

### **External Dependencies Analysis**

```python
# Current vendor dependencies (from code inspection):
- paho-mqtt          # MQTT client for device communication
- requests           # HTTP client for cloud API
- cryptography       # Encryption for device authentication
- zeroconf           # mDNS discovery (likely uses HA's)
- typing             # Python typing (stdlib)
- enum               # Python enums (stdlib)
```

## 🎯 **Extraction Strategy**

### **Phase 1: Repository Setup (Week 1)**

#### **1.1 Create Standalone Repository**

```bash
# Create new repository: libdyson-wg/libdyson
mkdir libdyson
cd libdyson
git init
git remote add origin https://github.com/libdyson-wg/libdyson.git
```

#### **1.2 Package Structure**

```
libdyson/
├── pyproject.toml           # Modern Python packaging
├── README.md               # Package documentation
├── LICENSE                 # MIT or Apache 2.0
├── .github/
│   └── workflows/
│       ├── test.yml        # CI testing
│       └── publish.yml     # PyPI publishing
├── src/
│   └── libdyson/          # Source code
│       ├── __init__.py    # Public API exports
│       ├── const.py       # Constants
│       ├── discovery.py   # Discovery functionality
│       ├── devices/       # Device classes
│       ├── cloud/         # Cloud integration
│       └── exceptions.py  # Exception classes
├── tests/                 # Test suite
└── docs/                  # Documentation
```

#### **1.3 Packaging Configuration**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "libdyson"
version = "2.0.0"  # Major version for standalone release
description = "Python library for Dyson devices"
readme = "README.md"
license = {file = "LICENSE"}
authors = [
    {name = "libdyson-wg", email = "maintainer@example.com"},
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Home Automation",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "paho-mqtt>=1.6.0",
    "requests>=2.28.0",
    "cryptography>=3.4.8",
    "zeroconf>=0.39.0",
]
requires-python = ">=3.11"

[project.urls]
"Homepage" = "https://github.com/libdyson-wg/libdyson"
"Bug Reports" = "https://github.com/libdyson-wg/libdyson/issues"
"Source" = "https://github.com/libdyson-wg/libdyson"

[tool.hatch.build.targets.wheel]
packages = ["src/libdyson"]
```

### **Phase 2: Code Migration (Week 1-2)**

#### **2.1 Direct File Migration**

```bash
# Copy vendor code to new package structure
cp -r vendor/libdyson/* src/libdyson/
```

#### **2.2 Import Path Updates**

```python
# Update internal imports within libdyson
# Old: from .cloud.account import DysonAccount
# New: from libdyson.cloud.account import DysonAccount

# Files requiring import updates:
- __init__.py           # Main exports
- device classes        # Internal cross-references
- cloud/__init__.py     # Cloud exports
- discovery.py          # Device factory imports
```

#### **2.3 Public API Design**

```python
# src/libdyson/__init__.py - Clean public API
"""Dyson device library for Python."""

# Version
__version__ = "2.0.0"

# Main factory function
from .factory import get_device, get_mqtt_info_from_wifi_info

# Device classes (most commonly used)
from .devices.dyson_device import DysonDevice
from .devices.pure_cool import DysonPureCool
from .devices.pure_hot_cool import DysonPureHotCool
from .devices.pure_humidify_cool import DysonPureHumidifyCool
from .devices.vacuum_360_eye import Dyson360Eye
from .devices.vacuum_360_heurist import Dyson360Heurist
from .devices.vacuum_360_vis_nav import Dyson360VisNav

# Constants
from .const import (
    DEVICE_TYPE_NAMES,
    MessageType,
    CleaningMode,
    CleaningType,
    AirQualityTarget,
    HumidifyOscillationMode,
    Tilt,
)

# Exceptions
from .exceptions import (
    DysonException,
    DysonInvalidAuth,
    DysonConnectTimeout,
    DysonNotConnected,
    DysonAuthRequired,
)

# Cloud integration
from .cloud import (
    DysonAccount,
    DysonAccountCN,
    DysonDeviceInfo,
    REGIONS,
)

# Discovery
from .discovery import DysonDiscovery

__all__ = [
    # Factory
    "get_device",
    "get_mqtt_info_from_wifi_info",
    # Devices
    "DysonDevice",
    "DysonPureCool",
    "DysonPureHotCool",
    "DysonPureHumidifyCool",
    "Dyson360Eye",
    "Dyson360Heurist",
    "Dyson360VisNav",
    # Constants
    "DEVICE_TYPE_NAMES",
    "MessageType",
    # Exceptions
    "DysonException",
    "DysonInvalidAuth",
    # Cloud
    "DysonAccount",
    "DysonDeviceInfo",
    "REGIONS",
    # Discovery
    "DysonDiscovery",
]
```

### **Phase 3: Quality & Testing (Week 2)**

#### **3.1 Test Suite Creation**

```python
# tests/test_devices.py
import pytest
from libdyson import get_device, DysonPureCool
from libdyson.const import DEVICE_TYPE_PURE_COOL

def test_device_factory():
    """Test device creation via factory."""
    device = get_device("SERIAL123", "CREDENTIAL", DEVICE_TYPE_PURE_COOL)
    assert isinstance(device, DysonPureCool)
    assert device.serial == "SERIAL123"

# tests/test_cloud.py
def test_cloud_account():
    """Test cloud account functionality."""
    # Mock tests for cloud integration

# tests/test_discovery.py
def test_device_discovery():
    """Test mDNS device discovery."""
    # Mock tests for discovery
```

#### **3.2 Documentation**

```markdown
# README.md - Package documentation

# Installation

pip install libdyson

# Usage

from libdyson import get_device, DEVICE_TYPE_PURE_COOL

device = get_device("SERIAL", "CREDENTIAL", DEVICE_TYPE_PURE_COOL)
await device.connect("192.168.1.100")

# Examples

- Basic device control
- Cloud integration
- Device discovery
- Error handling
```

#### **3.3 CI/CD Pipeline**

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e .[test]
      - run: pytest tests/ -v
      - run: mypy src/
      - run: flake8 src/
```

### **Phase 4: Integration Migration (Week 3)**

#### **4.1 Update Integration Dependencies**

```json
// manifest.json
{
  "requirements": ["libdyson>=2.0.0,<3.0.0"]
}
```

#### **4.2 Import Statement Migration**

```python
# Automated search & replace across integration
# Old: from .vendor.libdyson
# New: from libdyson

# Example file updates:
# device_manager.py
from libdyson import Dyson360Eye, Dyson360Heurist, Dyson360VisNav, get_device
from libdyson.dyson_device import DysonDevice
from libdyson.exceptions import DysonException, DysonInvalidAuth

# config_flow.py
from libdyson import DEVICE_TYPE_NAMES, get_device, get_mqtt_info_from_wifi_info
from libdyson.cloud import DysonAccount, DysonAccountCN, DysonDeviceInfo, REGIONS
from libdyson.const import DEVICE_TYPE_360_EYE, DEVICE_TYPE_360_HEURIST # etc...
```

#### **4.3 Remove Vendor Directory**

```bash
# After successful migration and testing
rm -rf custom_components/dyson_local/vendor/
```

### **Phase 5: Release & Distribution (Week 4)**

#### **5.1 PyPI Release Process**

```bash
# Build package
python -m build

# Test on PyPI Test
twine upload --repository testpypi dist/*

# Verify installation
pip install --index-url https://test.pypi.org/simple/ libdyson

# Release to PyPI
twine upload dist/*
```

#### **5.2 Integration Testing**

```bash
# Test integration with new package
pip install libdyson==2.0.0
# Run integration test suite
pytest tests/ -v
# Manual testing with real devices
```

## 🔧 **Technical Considerations**

### **Dependency Management**

```python
# Potential conflicts to resolve:
# 1. zeroconf - HA provides this, ensure compatibility
# 2. paho-mqtt - Version compatibility with HA
# 3. cryptography - Core dependency, ensure version alignment

# Solution: Use compatible version ranges
dependencies = [
    "paho-mqtt>=1.6.0,<2.0.0",      # Stable MQTT client
    "requests>=2.28.0,<3.0.0",      # HTTP client
    "cryptography>=3.4.8,<42.0.0",  # Encryption (HA compatible)
    "zeroconf>=0.39.0,<1.0.0",      # mDNS discovery
]
```

### **Backward Compatibility**

```python
# Maintain same public API for smooth migration:
# ✅ Same function signatures
# ✅ Same class interfaces
# ✅ Same exception types
# ✅ Same constants and enums

# Only internal imports change, not public API
```

### **Version Strategy**

```
v2.0.0 - Initial standalone release
v2.0.1 - Bug fixes
v2.1.0 - New features
v3.0.0 - Breaking changes (future)
```

## 📋 **Migration Checklist**

### **Repository Setup**

- [ ] Create libdyson-wg/libdyson repository
- [ ] Setup pyproject.toml with proper dependencies
- [ ] Configure GitHub Actions for CI/CD
- [ ] Add comprehensive README and documentation

### **Code Migration**

- [ ] Copy vendor code to new package structure
- [ ] Update internal import paths
- [ ] Design clean public API in **init**.py
- [ ] Ensure all device classes are properly exported

### **Quality Assurance**

- [ ] Create comprehensive test suite (>90% coverage)
- [ ] Add type annotations and mypy compliance
- [ ] Setup linting (flake8, black, isort)
- [ ] Test with real Dyson devices

### **Distribution**

- [ ] Test package build and installation
- [ ] Release to PyPI Test for validation
- [ ] Release v2.0.0 to PyPI production
- [ ] Verify package installation and imports

### **Integration Migration**

- [ ] Update manifest.json requirements
- [ ] Replace vendor imports with libdyson imports (33+ files)
- [ ] Remove vendor/ directory completely
- [ ] Test integration with new package
- [ ] Update documentation and README

### **Validation**

- [ ] All integration tests pass
- [ ] Real device testing confirms functionality
- [ ] Performance matches previous implementation
- [ ] No regressions in features

## 🎯 **Success Criteria**

### **Package Quality**

- ✅ **Professional PyPI Package**: Proper metadata, versioning, documentation
- ✅ **Test Coverage**: >90% test coverage with CI validation
- ✅ **Type Safety**: Full mypy compliance with type annotations
- ✅ **API Stability**: Backward compatible public interface

### **Integration Quality**

- ✅ **Seamless Migration**: No user-facing changes or regressions
- ✅ **Performance**: Equal or better performance vs vendor version
- ✅ **Maintainability**: Cleaner imports and dependency management
- ✅ **Official HA Ready**: Meets core integration requirements

### **Ecosystem Benefits**

- ✅ **Reusable Library**: Other projects can use libdyson
- ✅ **Community Contributions**: Easier for community to contribute
- ✅ **Version Management**: Professional release cycle and updates
- ✅ **Documentation**: Comprehensive API documentation

## ⏱️ **Timeline Estimate**

**Total Duration: 3-4 weeks**

- **Week 1**: Repository setup, code migration, basic testing
- **Week 2**: Quality assurance, comprehensive testing, documentation
- **Week 3**: Integration migration, testing, validation
- **Week 4**: Release process, final validation, documentation updates

This extraction will significantly improve the integration's maintainability and is a crucial step toward official Home Assistant core status! 🚀
