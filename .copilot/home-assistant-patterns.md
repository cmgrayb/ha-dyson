# Home Assistant Integration Patterns

This document contains specific coding patterns learned from resolving quality issues in the Dyson integration.

## 🏠 Property Override Patterns

### Problem: Home Assistant Cached Property Conflicts

Home Assistant uses cached properties that can conflict with custom property overrides, causing Pylance errors.

### Solution 1: Use Attribute Pattern (Preferred)

```python
# ❌ Problematic - overrides cached property
class DysonEntity(Entity):
    @property
    def should_poll(self) -> bool:
        return False

# ✅ Preferred - use attribute pattern
class DysonEntity(Entity):
    def __init__(self, device: DysonDevice, name: str):
        self._attr_should_poll = False
```

### Solution 2: Strategic Type Ignore (When Override Necessary)

```python
# ✅ When property override is necessary
class DysonEntity(Entity):
    @property
    def name(self) -> str:  # type: ignore[override]
        """Return the name of the entity."""
        if self.sub_name is None:
            return self._name
        return f"{self._name} {self.sub_name}"

    @property
    def unique_id(self) -> str:  # type: ignore[override]
        """Return the entity unique id."""
        if self.sub_unique_id is None:
            return self._device.serial
        return f"{self._device.serial}-{self.sub_unique_id}"

    @property
    def device_info(self) -> dict:  # type: ignore[override]
        """Return device info of the entity."""
        return {
            "identifiers": {(DOMAIN, self._device.serial)},
            "name": self._name,
            "manufacturer": "Dyson",
            "model": self._device.device_type,
        }
```

## 🔄 Multiple Inheritance Patterns

### Problem: Multiple Inheritance Conflicts

When inheriting from both custom base classes and Home Assistant entity classes, Pylance can report inheritance conflicts.

### Solution: Proper Inheritance Order + Type Ignore

```python
# ✅ Correct pattern - custom base class first, then HA entity
class DysonBinarySensor(DysonEntity, BinarySensorEntity):  # type: ignore[misc]
    """Base binary sensor for Dyson devices."""

class DysonButton(DysonEntity, ButtonEntity):  # type: ignore[misc]
    """Base button for Dyson devices."""

class DysonClimateEntity(DysonEntity, ClimateEntity):  # type: ignore[misc]
    """Base climate entity for Dyson devices."""
```

## 🔧 Method Signature Patterns

### Problem: Method Signature Mismatches

Config flow and other methods must match parent class signatures exactly.

### Solution: Match Parent Signatures with Optional Types

```python
# ✅ Correct - match parent signature exactly
async def async_step_email(self, info: Optional[dict] = None):
    # Always use Optional[dict] = None for step methods

async def async_step_host(self, info: Optional[dict] = None):
    # Consistent parameter typing across all step methods
```

## 🛡️ Null Safety Patterns

### Problem: Potential Null Pointer Access

Variables that should be set by previous steps might be None.

### Solution: Assertions for Null Safety

```python
# ✅ Add assertions for expected state
async def async_step_host(self, info: Optional[dict] = None):
    if info is not None:
        assert self._device_info is not None  # Should be set by discovery step

        device_type = self._device_info.get_device_type()
        # Continue with logic...
```

## 📝 Type Annotation Patterns

### Comprehensive Type Hints

```python
# ✅ Complete type annotations for all methods
def _get_current_oscillation_state(self) -> dict:
    """Get the current oscillation state for comparison."""
    if hasattr(self._device, "oscillation_angle_low"):
        return {
            "oscillation": getattr(self._device, "oscillation", None),
            "angle_low": getattr(self._device, "oscillation_angle_low", None),
            "angle_high": getattr(self._device, "oscillation_angle_high", None),
            "center": getattr(self._device, "oscillation_center", None),
        }
    return {}

def _schedule_oscillation_entities_update_debounced(self) -> None:
    """Schedule state updates for oscillation-related entities with debouncing."""
    # Clear return type annotation
```

## 🎯 When to Use Each Pattern

### Use `_attr_` Pattern When:

- Setting simple boolean or string properties
- Property doesn't require complex logic
- Home Assistant supports the attribute pattern for that property

### Use `# type: ignore[override]` When:

- Property requires custom logic (like concatenating sub_name)
- Property must return computed values
- No `_attr_` equivalent exists

### Use `# type: ignore[misc]` When:

- Multiple inheritance conflicts that are intentional
- Necessary for Home Assistant entity patterns
- Other miscellaneous type issues that are by design

## ✅ Quality Check Commands

Always run these commands after implementing patterns:

```bash
# Check for remaining type issues
mypy custom_components/dyson_local/

# Verify formatting
black --check custom_components/dyson_local/
isort --check-only custom_components/dyson_local/

# Check for code quality issues
flake8 custom_components/dyson_local/

# Verify all quality checks pass
pre-commit run --all-files
```

## 🚫 Anti-Patterns to Avoid

### Don't Override Cached Properties Without Type Ignore

```python
# ❌ Causes Pylance errors
@property
def should_poll(self) -> bool:  # Missing type ignore
    return False
```

### Don't Use Wrong Inheritance Order

```python
# ❌ Wrong order causes issues
class DysonSensor(SensorEntity, DysonEntity):  # Wrong order
```

### Don't Ignore Type Safety

```python
# ❌ Unsafe - could be None
device_type = self._device_info.get_device_type()  # _device_info could be None

# ✅ Safe with assertion
assert self._device_info is not None
device_type = self._device_info.get_device_type()
```
