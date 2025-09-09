import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# # Project information
# project = "Map Binning Tool"
# author = "Chia-Wei Hsu"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Support for NumPy/Google-style docstrings
    "sphinx.ext.viewcode",  # Link to source code
]

# autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# # Paths for templates and static files
# templates_path = ['_templates']
# exclude_patterns = []

# # HTML theme
# html_theme = "sphinx_book_theme"
