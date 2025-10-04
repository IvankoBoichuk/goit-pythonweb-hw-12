# Documentation

This directory contains the Sphinx documentation for the FastAPI Contacts API.

## Building Documentation

### Using Docker (Recommended)

Run the build script:

```bash
# On Windows
build-docs.bat

# On Linux/Mac  
./build-docs.sh
```

### Manual Build

If you have Python and Sphinx installed locally:

```bash
cd docs
pip install -r ../pyproject.toml[docs]
sphinx-build -b html . _build/html
```

### Using Make

If you have Make installed:

```bash
cd docs
make html
```

## Viewing Documentation

After building, open `docs/_build/html/index.html` in your browser.

## Documentation Structure

- `index.rst` - Main documentation index
- `overview.rst` - Project architecture and overview
- `quickstart.rst` - Getting started guide
- `api/` - API endpoint documentation
- `modules/` - Code documentation with autodoc
- `conf.py` - Sphinx configuration

## Adding Documentation

### Docstrings

Add Google-style docstrings to your code:

```python
def my_function(param1: str, param2: int = 0) -> bool:
    """Short description of the function.
    
    Longer description if needed.
    
    Args:
        param1 (str): Description of param1
        param2 (int, optional): Description of param2. Defaults to 0.
        
    Returns:
        bool: Description of return value
        
    Raises:
        ValueError: Description of when this error is raised
    """
    return True
```

### New Modules

Add new modules to the appropriate `.rst` file in `modules/`:

```rst
.. automodule:: src.new_module
   :members:
   :undoc-members:
   :show-inheritance:
```

### API Documentation

Add new endpoints to the appropriate file in `api/` using HTTP directive format.

## Dependencies

Documentation dependencies are defined in `pyproject.toml`:

- `sphinx` - Documentation generator
- `sphinx-rtd-theme` - Read the Docs theme
- `sphinx-autodoc-typehints` - Type hints support
- `myst-parser` - Markdown support