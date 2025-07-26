# libdyson-neon Migration Plan

## Direct Migration to libdyson-neon (No Contribution Needed!)

### Overview

Great news! The Dyson 360 Vis Nav support is **already fully implemented** in libdyson-neon and available on PyPI. We can migrate directly from vendor bundling to PyPI dependency without any upstream contribution needed.

### ✅ **Discovery Results**

- **libdyson-neon** is the actively maintained fork (not the old libdyson)
- **Dyson360VisNav support** already implemented in v1.4.0 (March 31, 2024)
- **PyPI availability**: libdyson-neon 1.5.2 includes all needed features
- **GitHub latest**: v1.5.6 (even newer features available)

### 🎯 **Migration Plan**

No upstream contribution needed! We can migrate directly:

1. **Change dependency** from `libdyson` to `libdyson-neon`
2. **Update imports** from `.vendor.libdyson` to `libdyson`
3. **Remove vendor directory** after testing
4. **Test compatibility** with PyPI libdyson-neon 1.5.2+

### Benefits

- ✅ **No waiting** - Can migrate immediately to PyPI libdyson-neon 1.5.2
- ✅ **All features included** - Dyson360VisNav and other vendor features
- ✅ **Active maintenance** - libdyson-neon is actively developed
- ✅ **Clean migration** - No vendor workarounds needed

### Timeline

1. **This week**: Test compatibility with libdyson-neon 1.5.2
2. **Next week**: Implement migration to libdyson-neon
3. **Following week**: Remove vendor directory and finalize

### Next Steps

1. Test current integration with `pip install libdyson-neon==1.5.2`
2. Update manifest.json to use libdyson-neon dependency
3. Update all imports from `.vendor.libdyson` to `libdyson`
4. Remove vendor directory after validation
