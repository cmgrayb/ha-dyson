# Strict Typing Fixes - Phase 1

## 📊 Error Analysis (448 total)

### **Category Breakdown:**

1. **Library stubs missing**: ~60 errors (libdyson imports)
2. **Unused type ignores**: ~200 errors (easy to fix)
3. **Missing return types**: ~100 errors (medium difficulty)
4. **Missing parameter types**: ~50 errors (medium difficulty)
5. **Generic type parameters**: ~38 errors (easy to fix)

### **Fix Priority:**

1. ✅ **Phase 1**: Remove unused `# type: ignore` comments
2. ✅ **Phase 2**: Add missing return type annotations
3. ✅ **Phase 3**: Fix generic type parameters
4. ✅ **Phase 4**: Add parameter type annotations
5. ✅ **Phase 5**: Handle library stub issues

### **Strategy:**

- Start with entity.py (foundation file)
- Move to platform files (sensor, switch, etc.)
- Fix config_flow.py last (most complex)
- Create type stubs for libdyson if needed

### **Tools:**

```bash
# Run mypy on single file to focus
python -m mypy custom_components/dyson_local/entity.py --strict

# Remove unused ignores automatically
python -m mypy custom_components/dyson_local/ --strict 2>&1 | grep "Unused.*ignore" | cut -d: -f1-2 | sort -u
```

## 🎯 **Starting with entity.py - Foundation File**

This file has the core typing issues that affect all platforms.
