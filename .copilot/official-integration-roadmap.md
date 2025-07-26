# Official Home Assistant Integration Roadmap

## Path to Platinum Level Quality Scale

This document outlines the requirements and action plan to get the Dyson Local integration accepted as an official Home Assistant integration with **Platinum level quality scale** - the highest tier possible!

## 🎯 **Current Status Assessment**

### ✅ **Already Implemented (Bronze + Silver + Most Gold Requirements)**

#### Bronze Level ✓

- [x] **Config Flow**: Complete UI-based setup with multiple authentication methods
- [x] **Unique Config Entry**: Prevents duplicate device setup
- [x] **Test Coverage**: Comprehensive test suite covering config flow and platforms
- [x] **Entity Unique IDs**: All entities have stable unique identifiers
- [x] **Appropriate Polling**: Configurable polling intervals for different device types
- [x] **Common Modules**: Well-organized codebase with shared utilities
- [x] **Documentation**: Step-by-step setup instructions in README
- [x] **Branding**: Assets available for integration display

#### Silver Level ✓

- [x] **Integration Owner**: Active codeowners (@libdyson-wg, @dotvezz)
- [x] **Config Entry Unloading**: Complete cleanup and disconnection
- [x] **Reauthentication Flow**: Automatic reauth triggers for expired credentials
- [x] **Entity Unavailable**: Proper handling of offline devices
- [x] **Log When Unavailable**: Appropriate logging for connection issues
- [x] **Action Exceptions**: Service actions raise proper exceptions
- [x] **Test Coverage**: Above 95% coverage across integration modules

#### Gold Level ✓ (95% Complete)

- [x] **Discovery**: Zeroconf/mDNS automatic device discovery
- [x] **Devices**: Creates proper device entities with correct relationships
- [x] **Dynamic Devices**: Handles devices added after integration setup
- [x] **Entity Categories**: Proper categorization of diagnostic vs primary entities
- [x] **Device Classes**: Appropriate sensor/binary_sensor device classes
- [x] **Entity Translations**: Full translation system implemented
- [x] **Diagnostics**: Comprehensive diagnostic data collection
- [x] **Reconfiguration Flow**: UI-based reconfiguration available
- [x] **Documentation**: Extensive troubleshooting and setup guides

### 🔄 **Requirements to Complete**

#### **For Platinum Level Achievement:**

##### 1. **Complete Gold Requirements (95% done)**

```
Remaining Gold Items:
- Entity disabled by default for diagnostic/noisy entities
- Exception message translations (ensure all errors translatable)
- Icon translations for dynamic state-based icons
```

##### 2. **Platinum Requirements (Only 3 items!)**

```
Platinum Requirements:
- Strict typing: Full mypy --strict compliance
- WebSession injection: Verify libdyson-neon supports aiohttp session injection
- Async dependency: ✅ Already complete (fully async integration)
```

##### 3. **Repository Migration & Structure** (Same as before)

```
Required Changes:
- Fork home-assistant/core repository
- Move integration to homeassistant/components/dyson_local/
- Remove custom integration specific files (hacs.json, version from manifest)
- Update manifest.json for core integration standards
```

##### 2. **Documentation Migration**

```
Required:
- Create official documentation at www.home-assistant.io/integrations/dyson_local
- Follow HA documentation standards and templates
- Include troubleshooting, supported devices, configuration options
- Remove custom integration documentation references
```

##### 3. **Dependency Management**

```
Current Issue: Vendor libraries included
Solution Required:
- Extract libdyson to separate PyPI package
- Update requirements in manifest.json
- Ensure dependency follows HA standards
```

##### 4. **Testing Infrastructure**

```
Required:
- Ensure tests run in HA CI environment
- Remove custom integration specific test setup
- Add hassfest validation compliance
```

##### 5. **Quality Scale Compliance**

```
Required Files:
- Create quality_scale.yaml tracking compliance
- Document exemptions with justifications
- Ensure all Bronze + Silver requirements met
```

## 📋 **Detailed Action Plan**

### **Phase 1: Code Preparation (Estimated: 2-3 weeks)**

#### **1.1 Dependency Migration**

- [x] **libdyson-neon exists**: GitHub has v1.5.6, PyPI has v1.5.2 (gap identified)
- [ ] **Request PyPI update**: Ask maintainer to publish v1.5.6 to PyPI
- [ ] **Update manifest requirements**: Use libdyson-neon>=1.5.6 from PyPI
- [ ] **Remove vendor directory**: Migrate imports from `.vendor.libdyson` to `libdyson`
- [ ] **Test compatibility**: Ensure functionality unchanged with PyPI version

#### **1.2 Manifest Updates**

```json
{
  "domain": "dyson_local",
  "name": "Dyson",
  "codeowners": ["@libdyson-wg", "@dotvezz"],
  "config_flow": true,
  "dependencies": ["mqtt", "zeroconf"],
  "documentation": "https://www.home-assistant.io/integrations/dyson_local",
  "integration_type": "hub",
  "iot_class": "local_push",
  "quality_scale": "silver",
  "requirements": ["libdyson==0.8.11"]
}
```

#### **1.3 Code Quality Enhancements**

- [ ] **Runtime Data**: Migrate to ConfigEntry.runtime_data pattern
- [ ] **Entity Categories**: Assign appropriate categories to all entities
- [ ] **Device Classes**: Ensure all sensors use proper device classes
- [ ] **Translations**: Complete entity name translations
- [ ] **Type Annotations**: 100% type annotation coverage

### **Phase 2: Testing & Validation (Estimated: 1-2 weeks)**

#### **2.1 Test Suite Enhancement**

- [ ] **Config Flow Coverage**: 100% test coverage for all flows
- [ ] **Platform Coverage**: Test all entity platforms comprehensively
- [ ] **Error Handling**: Test failure scenarios and recovery
- [ ] **Mock Testing**: Proper mocking of external dependencies

#### **2.2 Quality Validation**

- [ ] **hassfest**: Pass Home Assistant validation
- [ ] **mypy**: Full type checking compliance
- [ ] **pytest**: All tests pass in HA environment
- [ ] **Code Coverage**: Maintain 95%+ coverage

### **Phase 3: Documentation (Estimated: 1-2 weeks)**

#### **3.1 Official Documentation**

- [ ] **Integration Page**: Create comprehensive integration documentation
- [ ] **Configuration**: Document all setup methods and options
- [ ] **Troubleshooting**: Common issues and solutions
- [ ] **Supported Devices**: Complete device compatibility list
- [ ] **Examples**: Automation and dashboard examples

#### **3.2 Quality Scale Documentation**

```yaml
# quality_scale.yaml
rules:
  config_flow: done
  entity_unique_id: done
  integration_owner: done
  reauthentication_flow: done
  test_coverage: done
  # ... complete checklist
```

### **Phase 4: Submission Process (Estimated: 2-4 weeks)**

#### **4.1 Pull Request Preparation**

- [ ] **Fork HA Core**: Create development branch
- [ ] **Integration Migration**: Move code to proper core location
- [ ] **Remove Custom Elements**: Clean up HACS-specific files
- [ ] **Core Compliance**: Ensure integration follows core patterns

#### **4.2 PR Submission Requirements**

```markdown
Required PR Content:

- Complete quality scale checklist with evidence
- Links to relevant code sections
- Test coverage report
- Documentation links
- Migration plan for existing users
```

## 🛡️ **Challenges & Mitigation Strategies**

### **Challenge 1: Vendor Library Dependency**

**Issue**: Core integrations cannot include vendor libraries
**Solution**:

- Extract libdyson to separate maintained PyPI package
- Ensure package follows HA dependency standards
- Maintain backward compatibility

### **Challenge 2: Existing User Migration**

**Issue**: Users have custom integration installed
**Solution**:

- Provide clear migration documentation
- Ensure domain name compatibility
- Coordinate with HACS for deprecation notice

### **Challenge 3: Active Development Requirement**

**Issue**: Core integrations need active maintainers
**Solution**:

- Ensure codeowners commit to long-term maintenance
- Establish clear communication channels
- Document contribution guidelines

### **Challenge 4: Review Process Timeline**

**Issue**: Core integration reviews can take months
**Solution**:

- Prepare comprehensive submission
- Engage with HA dev community early
- Address feedback promptly and thoroughly

## 📊 **Success Metrics**

### **Silver Level Achievement Criteria:**

- ✅ **Code Quality**: All Bronze + Silver checklist items completed
- ✅ **Test Coverage**: >95% coverage across all modules
- ✅ **Documentation**: Complete official HA documentation
- ✅ **Community Review**: Positive feedback from HA core team
- ✅ **User Experience**: Stable, reliable operation

### **Timeline Estimate:**

- **Total Duration**: 6-10 weeks
- **Development**: 4-6 weeks
- **Review Process**: 2-4 weeks (dependent on HA team)
- **Launch**: Next HA major release after acceptance

## 🎉 **Benefits of Official Status**

### **For Users:**

- ✅ **Built-in Integration**: No additional installation required
- ✅ **Official Support**: Backed by Home Assistant project
- ✅ **Automatic Updates**: Included in HA core updates
- ✅ **Enhanced Reliability**: Rigorous testing and quality standards

### **For Developers:**

- ✅ **Wider Reach**: Included in all HA installations
- ✅ **Community Recognition**: Official integration status
- ✅ **Collaborative Development**: HA core team involvement
- ✅ **Long-term Stability**: Maintained as part of HA ecosystem

This roadmap provides a clear path to achieving official Home Assistant integration status with Silver level quality scale. The integration already meets most requirements and with focused effort on the remaining items, official status is highly achievable! 🎯
