"""
Codebase page module.

This module forces early import of visualization modules to ensure
all Dash callbacks are registered at app startup, before the server
begins handling requests.
"""

# Force import of visualization modules to register callbacks
# This must happen before the app starts serving requests
# Importing these modules triggers the @callback decorators
from .visualizations import cntrb_file_heatmap
from .visualizations import contribution_file_heatmap
from .visualizations import reviewer_file_heatmap

# Explicitly import the page module to ensure it's loaded
from . import codebase
