# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Graph Dataset"
copyright = "2024, Kapil Duwadi, Aadil Latif, Andrew Glaws"
author = "Kapil Duwadi, Aadil Latif, Andrew Glaws"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",  # rich parser for markdowns
    "sphinx.ext.autodoc",  # import module for documenting
    "sphinx.ext.autosummary",  # generates function/method/attribute summary list
    "sphinx.ext.napoleon",  # parsing numpy and google style docstrings to rst
    "sphinx.ext.intersphinx",  # keeps all links upto date
    "sphinxcontrib.autodoc_pydantic",  # converts pydantic properly
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_field_summary = False
autodoc_inherit_docstrings = False
autodoc_pydantic_field_show_constraints = False
autodoc_pydantic_settings_show_validator_summary = False
autodoc_pydantic_settings_show_validator_members = False
autodoc_pydantic_validator_list_fields = False
autodoc_pydantic_field_list_validators = False
autodoc_pydantic_model_show_validator_summary = False


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]


source_suffix = [".md", ".rst"]
