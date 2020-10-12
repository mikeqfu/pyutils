"""
Configuration file for the Sphinx documentation builder.
"""

# Path setup ===========================================================================
import os
import sys

# If the directory is relative to the documentation root,
# use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../pyhelpers'))

# Project information ==================================================================
import datetime
import pyhelpers

# General information about the project.
project = u'PyHelpers'
copyright = u'2019-{}, {}'.format(datetime.datetime.now().year, pyhelpers.__author__)

# The version info for the project
version = pyhelpers.__version__  # The short X.Y version.
release = version  # The full version, including alpha/beta/rc tags.

# General configuration ================================================================


def setup(app):
    app.add_js_file('copybutton.js')


# Sphinx extension module names,
#   which can be extensions coming with Sphinx (named 'sphinx.ext.*') or custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.githubpages',
    'sphinx.ext.todo',
    'sphinx_rtd_theme',
]

# The language for content autogenerated by Sphinx.
language = 'en'

# Patterns (relative to source directory) that match files & directories to ignore.
exclude_patterns = ['_build', '../_build', '../build']

# Whether to scan all found documents for autosummary directives,
#   and to generate stub pages for each.
autosummary_generate = True

# A list of modules to be mocked up.
autodoc_mock_imports = ['gdal', 'shapely']

# The suffix(es) of source filenames (For multiple suffix, a list of string.
source_suffix = '.rst'  # e.g. source_suffix = ['.rst', '.md'])

# The master toctree document.
master_doc = 'index'

# Automatically documented members are sorted by source order ('bysource').
autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# Options for HTML and HTMLHelp output =================================================
html_theme = 'sphinx_rtd_theme'  # The theme to use for HTML & HTML Help pages.

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'  # or 'default'

# Paths containing custom static files (e.g. style sheets), relative to this directory.
html_static_path = ['_static']

# Output file base name for HTML help builder. Default is 'pydoc'.
htmlhelp_basename = project + 'doc'

# Options for LaTeX output =============================================================
from pygments.formatters.latex import LatexFormatter
from sphinx.highlighting import PygmentsBridge


class CustomLatexFormatter(LatexFormatter):
    def __init__(self, **options):
        super(CustomLatexFormatter, self).__init__(**options)
        self.verboptions = r"formatcom=\footnotesize"


PygmentsBridge.latex_formatter = CustomLatexFormatter

# The LaTeX engine to build the docs.
latex_engine = 'pdflatex'

# Grouping the document tree into LaTeX files.
latex_documents = [
    ('index',  # source start file
     'pyhelpers.tex',  # target name
     u'PyHelpers Documentation',  # title
     u'Qian Fu',  # author
     'manual',  # document class ['howto', 'manual', or own class]
     1  # toctree only
     ),
]

# LaTeX customization.
latex_elements = {
    'papersize': 'a4paper',  # The paper size ('letterpaper' or 'a4paper').
    'pointsize': '10pt',  # The font size ('10pt', '11pt' or '12pt').
    'pxunit': '0.25bp',
    'preamble': r'''
        \setlength{\headheight}{14pt}
        \DeclareUnicodeCharacter{229E}{\ensuremath{\boxplus}}
        \setcounter{tocdepth}{2}
        \usepackage[none]{hyphenat}
        \usepackage[document]{ragged2e}
        \usepackage[utf8]{inputenc}
        \usepackage{textcomp}
        \usepackage{amsfonts}
        \usepackage{textgreek}
        \usepackage{graphicx}
        \usepackage{svg}
        ''',
    'printindex': r'''
        \IfFileExists{\jobname.ind}
                     {\footnotesize\raggedright\printindex}
                     {\begin{sphinxtheindex}\end{sphinxtheindex}}
    ''',
    'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
    'fvset': r'\fvset{fontsize=auto}',
    'figure_align': 'H'  # Latex figure (float) alignment
}

# The theme that the LaTeX output should use.
latex_theme = 'manual'

# Options for manual page output =======================================================

man_pages = [  # How to group the document tree into manual pages.
    ('index',  # startdocname
     'pyhelpers',  # name
     u'PyHelpers Documentation',  # description
     [u'Qian Fu'],  # authors
     1  # section
     )
]

# Options for Texinfo output ===========================================================

texinfo_documents = [  # Grouping the document tree into Texinfo files.
    (master_doc,  # source start file
     'pyhelpers',  # target name
     u'PyHelpers Documentation',  # title
     u'Qian Fu',  # author
     'PyHelpers',  # dir menu entry
     'A toolkit for facilitating basic data manipulation.',
     'Data manipulation tools',  # category
     1  # toctree only
     ),
]
