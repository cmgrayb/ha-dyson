# Home Assistant Integration Coding Standards

This document defines the coding standards and best practices for the Dyson Local Home Assistant integration.

## 📋 Code Quality Standards

### File Organization

- ✅ **Single Responsibility**: Each file should have a single, well-defined purpose
- ✅ **Modular Design**: Break large files into focused modules (target: <200 lines per file)
- ✅ **Clear Imports**: Group imports logically (stdlib, third-party, local)
- ✅ **Type Hints**: Use type hints for all function signatures and class attributes

### Home Assistant Integration Patterns

- ✅ **Property Override Handling**: Use `_attr_` pattern when possible, strategic `# type: ignore[override]` when necessary
- ✅ **Multiple Inheritance**: Proper inheritance order - custom base class first, then HA entity class
- ✅ **Cached Properties**: Avoid overriding Home Assistant cached properties; use attributes instead
- ✅ **Entity Framework**: Inherit from appropriate HA entity base classes with proper method signatures

### Home Assistant Best Practices

- ✅ **Integration Structure**: Follow HA integration patterns with proper `__init__.py`, platform files, and config flow
- ✅ **Entity Framework**: Inherit from appropriate HA entity base classes
- ✅ **Config Entries**: Use config entries for device setup and management
- ✅ **Data Coordinators**: Use DataUpdateCoordinator for polling devices
- ✅ **Device Registry**: Properly register devices with unique identifiers
- ✅ **Property Management**: Use `_attr_` attributes instead of property overrides when possible
- ✅ **Type Safety**: Strategic use of `# type: ignore[override]` for necessary property overrides
- ✅ **Inheritance Conflicts**: Resolve multiple inheritance issues with proper ordering and type annotations

### Python Code Style

- ✅ **PEP 8 Compliance**: Follow Python style guidelines
- ✅ **Black Formatting**: Use Black for consistent code formatting
- ✅ **Import Sorting**: Use isort for organized imports
- ✅ **Line Length**: Maximum 88 characters (Black default)
- ✅ **Docstrings**: Use Google-style docstrings for all public functions/classes

## 🔧 Common Quality Issues & Solutions

### Property Override Conflicts

**Issue**: Home Assistant cached properties conflict with custom overrides
**Solution**:

```python
# ❌ Avoid - conflicts with cached properties
@property
def should_poll(self) -> bool:
    return False

# ✅ Preferred - use attribute pattern
def __init__(self, device, name):
    self._attr_should_poll = False

# ✅ When override necessary - use type ignore
@property
def unique_id(self) -> str:  # type: ignore[override]
    return f"{self._device.serial}-{self.sub_unique_id}"
```

### Multiple Inheritance Issues

**Issue**: Pylance errors with multiple inheritance in entity classes
**Solution**:

```python
# ✅ Correct inheritance order - custom base class first
class DysonBinarySensor(DysonEntity, BinarySensorEntity):  # type: ignore[misc]
    """Base binary sensor for Dyson devices."""
```

### Method Signature Compatibility

**Issue**: Method signatures don't match parent class expectations
**Solution**:

```python
# ✅ Match parent signatures exactly, add Optional types
async def async_step_email(self, info: Optional[dict] = None):
    # Ensure consistent parameter types with parent
```

### Null Safety & Type Annotations

**Issue**: Potential null pointer access and missing type hints
**Solution**:

```python
# ✅ Add assertions for null safety
assert self._device_info is not None  # Should be set by discovery step

# ✅ Comprehensive type annotations
def _get_current_oscillation_state(self) -> dict:
    """Get the current oscillation state for comparison."""
```

### Error Handling

- ✅ **Specific Exceptions**: Catch specific exceptions, avoid bare `except:`
- ✅ **Logging**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- ✅ **Graceful Degradation**: Handle device disconnections gracefully
- ✅ **Configuration Validation**: Validate all user inputs

### Testing & Quality Assurance

- ✅ **Linting**: Pass flake8, mypy, and bandit checks
- ✅ **Pre-commit Hooks**: Use pre-commit for automated quality checks
- ✅ **HACS Validation**: Pass HACS and hassfest validation
- ✅ **Device Testing**: Test with real devices when possible
- ✅ **Vendor Exclusions**: Exclude third-party vendor code from linting with proper setup.cfg configuration

## 🏗️ Architecture Standards

### Component Structure

```
custom_components/dyson_local/
├── __init__.py           # Integration setup (< 100 lines)
├── config_flow.py        # User configuration
├── const.py             # Constants and configuration
├── device_manager.py    # Device lifecycle management
├── connection.py        # Device connection handling
├── discovery_manager.py # Device discovery coordination
├── entity.py           # Base entity classes
├── utils.py            # Utility functions
├── [platform].py       # Platform implementations (fan, sensor, etc.)
├── cloud/              # Cloud service integration
└── vendor/             # Third-party libraries
```

### Function Size Limits

- ✅ **Functions**: Maximum 50 lines per function
- ✅ **Classes**: Maximum 300 lines per class
- ✅ **Files**:
  - **Integration core** (`__init__.py`): Target < 100 lines
  - **Platform files** (fan, sensor, etc.): Target < 500 lines, maximum 800 lines
  - **Utility/helper files**: Target < 200 lines, maximum 300 lines
  - **Config flow**: Target < 600 lines (complex device setup is acceptable)

### Naming Conventions

- ✅ **Variables**: `snake_case`
- ✅ **Functions**: `snake_case`
- ✅ **Classes**: `PascalCase`
- ✅ **Constants**: `UPPER_SNAKE_CASE`
- ✅ **Private Methods**: `_leading_underscore`

## 🔍 Quality Metrics Targets

### Code Complexity

- ✅ **Cyclomatic Complexity**: < 10 per function
- ✅ **Cognitive Complexity**: < 15 per function
- ✅ **Nesting Depth**: < 4 levels

### Documentation

- ✅ **Docstring Coverage**: 100% for public APIs
- ✅ **Type Annotation**: 100% for function signatures
- ✅ **README**: Complete setup and usage documentation

### Performance

- ✅ **Startup Time**: Integration loads in < 30 seconds
- ✅ **Memory Usage**: Reasonable memory footprint
- ✅ **API Efficiency**: Minimize device polling frequency

## 🚨 Critical Requirements

### Security

- ✅ **Input Validation**: Validate all external inputs
- ✅ **Credential Storage**: Use HA's secure credential storage
- ✅ **Network Security**: Use TLS for external communications
- ✅ **Error Information**: Don't leak sensitive data in logs/errors

### Reliability

- ✅ **Error Recovery**: Graceful handling of device disconnections
- ✅ **State Management**: Proper cleanup on unload/reload
- ✅ **Resource Management**: Properly close connections and clean up resources
- ✅ **Backwards Compatibility**: Maintain compatibility across HA versions

### User Experience

- ✅ **Configuration**: Clear, intuitive setup process
- ✅ **Error Messages**: Helpful, actionable error messages
- ✅ **Entity Naming**: Consistent, descriptive entity names
- ✅ **Device Info**: Complete device information and diagnostics

## 📊 Compliance Checklist

Use this checklist to verify compliance:

### File Structure & Size

- [ ] Core files (init, utils) under 300 lines
- [ ] Platform files under 800 lines (with preference for < 500)
- [ ] All functions under 50 lines
- [ ] Single responsibility per file/class

### Code Quality

- [ ] 100% type annotation coverage
- [ ] All linting checks pass (flake8, mypy, bandit)
- [ ] Black formatting applied
- [ ] isort import organization
- [ ] All docstrings present
- [ ] No bare except clauses
- [ ] Proper error handling

### Home Assistant Compatibility

- [ ] Use `_attr_` pattern instead of property overrides when possible
- [ ] Strategic `# type: ignore[override]` for necessary property overrides
- [ ] Correct multiple inheritance order (custom base class first)
- [ ] Method signatures match parent class expectations
- [ ] Null safety with assertions where needed
- [ ] Proper async/await usage

### Integration Standards

- [ ] HACS validation passes
- [ ] Integration follows HA patterns
- [ ] Proper resource cleanup
- [ ] Security best practices followed
- [ ] Device info properly configured
- [ ] Entity unique IDs are stable

## 🔄 Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one reviewer approval required
3. **Testing**: Manual testing with real devices
4. **Documentation**: Update relevant documentation
5. **Backward Compatibility**: Ensure no breaking changes

## 🔐 Authentication & Authorization Patterns

### Cloud Authentication

- ✅ **OAuth2 Flow**: Implement proper OAuth2 authorization code flow
- ✅ **Token Management**: Secure storage and refresh of access/refresh tokens
- ✅ **Error Handling**: Graceful handling of authentication failures with user-friendly messages
- ✅ **Reauthentication**: Automatic token refresh and manual reauth flows
- ✅ **Timeout Handling**: Proper handling of network timeouts and connection errors

### Authentication Error Recovery

```python
# ✅ Proper authentication error handling pattern
try:
    cloud_devices = await cloud_manager.get_devices()
except DysonAuthRequired:
    # Trigger config flow for reauthentication
    self.hass.async_create_task(
        self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH},
            data=self.config_entry.data,
        )
    )
    return
except Exception as ex:
    _LOGGER.error("Unexpected error during cloud authentication: %s", ex)
    return
```

### Local Device Authentication

- ✅ **Credential Validation**: Validate device credentials before attempting connection
- ✅ **Connection Retry**: Implement exponential backoff for failed authentication attempts
- ✅ **Device State**: Maintain authentication state across reconnections
- ✅ **Security**: Never log or expose device credentials in plain text

## 🔍 Auto-Discovery & Configuration Patterns

### Discovery Manager Design

- ✅ **Singleton Pattern**: Use coordinator pattern for discovery management
- ✅ **Device Deduplication**: Prevent duplicate device entries across local/cloud discovery
- ✅ **Background Discovery**: Non-blocking discovery that doesn't delay integration startup
- ✅ **Discovery Coordination**: Coordinate between local mDNS and cloud API discovery

### Configuration Flow Architecture

```python
# ✅ Proper config flow with cloud and local discovery
class DysonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle user initiated flow."""
        # Present discovery options (cloud, local, manual)

    async def async_step_cloud(self, user_input=None):
        """Handle cloud authentication step."""
        # OAuth2 flow with proper error handling

    async def async_step_discovery(self, discovery_info):
        """Handle discovered devices."""
        # Auto-configure discovered devices

    async def async_step_reauth(self, user_input=None):
        """Handle reauthentication."""
        # Seamless token refresh flow
```

### Options Flow Implementation

- ✅ **Runtime Configuration**: Allow users to modify settings without reconfiguration
- ✅ **Validation**: Validate all option changes before applying
- ✅ **Persistence**: Properly save and load option configurations
- ✅ **Backward Compatibility**: Handle missing options gracefully
- ✅ **User-Friendly Labels**: Use clear, descriptive labels that match industry standards (e.g., Philips Hue patterns)
- ✅ **Conditional Options**: Show relevant options based on device type (cloud vs local)

```python
# ✅ Proper options flow pattern with conditional options
async def async_step_init(self, user_input=None):
    """Manage the options."""
    if user_input is not None:
        # Validate and save options
        return self.async_create_entry(title="", data=user_input)

    # Show different options based on device configuration
    if CONF_AUTH in self.config_entry.data:
        # Cloud device - full options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_AUTO_DISCOVERY, default=current_auto_discovery): bool,
                vol.Optional(CONF_ENABLE_POLLING, default=current_enable_polling): bool,
                vol.Optional(CONF_CLOUD_POLL_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=300, max=86400)
                ),
            })
        )
    else:
        # Local device - basic options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_ENABLE_POLLING, default=current_enable_polling): bool,
            })
        )
```

## 🏗️ Advanced Integration Architecture

### Device Manager Patterns

- ✅ **Lifecycle Management**: Proper device setup, update, and cleanup lifecycle
- ✅ **Error Recovery**: Graceful handling of device connection failures
- ✅ **Cloud Coordination**: Seamless integration of cloud and local device management
- ✅ **Resource Cleanup**: Proper cleanup of device connections and resources

### Coordinator Implementation

```python
# ✅ Proper coordinator pattern for device management
class DysonDeviceUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, device, update_interval):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Dyson {device.name}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.device = device

    async def _async_update_data(self):
        """Fetch data from device."""
        try:
            async with asyncio.timeout(10):
                await self.device.request_current_state()
                return self.device.environmental_data
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with device: {ex}")
```

## 🔧 Advanced Linting & Quality Control

### Setup.cfg Configuration

```ini
# ✅ Comprehensive flake8 configuration
[flake8]
max-line-length = 88
exclude =
    .venv,
    .git,
    .tox,
    docs,
    venv,
    bin,
    lib,
    deps,
    build,
    custom_components/dyson_local/vendor
ignore =
    E203,  # Whitespace before ':' (conflicts with black)
    W503,  # Line break before binary operator (conflicts with black)
per-file-ignores =
    __init__.py:F401  # Allow unused imports in __init__.py
```

### Import Management

- ✅ **Systematic Cleanup**: Regular review and removal of unused imports
- ✅ **Import Organization**: Use isort for consistent import ordering
- ✅ **Conditional Imports**: Proper handling of optional dependencies
- ✅ **Vendor Dependencies**: Isolate vendor imports to prevent namespace pollution

### Professional Repository Standards

- ✅ **Demo Script Management**: Remove debug/demo scripts from public repositories
- ✅ **Test Organization**: Proper separation of unit tests, integration tests, and demo scripts
- ✅ **Documentation**: Comprehensive README with setup, configuration, and troubleshooting
- ✅ **Version Control**: Proper .gitignore and exclusion of development artifacts

### Quality Gate Automation

```python
# ✅ Pre-commit hook configuration
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
```

## 🚀 Performance & Scalability

### Connection Management

- ✅ **Connection Pooling**: Reuse connections where possible
- ✅ **Timeout Configuration**: Appropriate timeouts for all network operations
- ✅ **Resource Limits**: Proper limits on concurrent connections and operations
- ✅ **Memory Management**: Efficient memory usage and garbage collection

### Data Flow Optimization

- ✅ **Batch Operations**: Group related API calls to reduce overhead
- ✅ **Caching Strategy**: Intelligent caching of device state and configuration
- ✅ **Update Intervals**: Configurable update intervals based on device capabilities
- ✅ **Event-Driven Updates**: Use device events rather than polling where possible
