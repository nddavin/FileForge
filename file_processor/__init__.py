"""Compatibility shim package.

This small package makes imports like `import file_processor.services` work
by re-exporting the `backend.file_processor` package modules. Tests in
the repo import `file_processor.*`, so this shim avoids changing existing
imports or test configuration.
"""
import importlib
import sys

_backend_root = "backend.file_processor"

# Attempt to import the backend package; if it's missing the import will
# raise the original error so failures surface clearly.
backend_pkg = importlib.import_module(_backend_root)

# Re-export common subpackages used throughout the codebase.
_subpackages = [
    "api",
    "core",
    "models",
    "services",
    "crud",
    "schemas",
    "processors",
    "queue",
    "utils",
]

for sp in _subpackages:
    try:
        mod = importlib.import_module(f"{_backend_root}.{sp}")
        # Place the module into sys.modules under the expected name so
        # `import file_processor.{sp}` resolves to the backend module.
        sys.modules[f"file_processor.{sp}"] = mod
        setattr(sys.modules[__name__], sp, mod)
    except ModuleNotFoundError:
        # Some subpackages may not exist yet; ignore silently.
        pass

# Also make `file_processor` map to the backend package for direct imports
sys.modules["file_processor.backend"] = backend_pkg
# Expose the backend package as an attribute too
file_processor_backend = backend_pkg
