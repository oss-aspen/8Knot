"""
Layout components for the main application structure.

This file contains reusable UI components that make up the main application shell,
including the sidebar, main content area, and navigation elements.
"""

from dash import html, dcc
import dash
import dash_bootstrap_components as dbc

# This will be imported from the main layout file
search_bar = None


def sidebar_section(icon_src=None, text="Hello", page_link="/", horizontal_padding=12, vertical_padding=16):
    """
    Creates a clickable section in the sidebar, which allows navigation to different pages

    Args:
        icon_src: Optionally label the section with an icon
        text: The text that will be displayed in the sidebar section
        page_link: The page to navigate to
        horizontal_padding and vertical_padding: Fine-tune the spacing (kept for compatibility)
    """
    if icon_src:
        return dbc.NavLink(
            [
                html.Img(src=icon_src, alt=text, className="sidebar-section-icon"),
                html.Span(text, className="sidebar-section-text"),
            ],
            href=page_link,
            className="sidebar-section",
        )
    else:
        return dbc.NavLink(
            text,
            href=page_link,
            className="sidebar-section-text-no-icon",
        )


def sidebar_dropdown(
    icon_src, text, dropdown_links, dropdown_id="dropdown", horizontal_padding=12, vertical_padding=16
):
    """Create a dropdown navigation with main item and dropdown content

    Args:
        icon_src (str): Source path for the icon image
        text (str): Text to display next to the icon
        dropdown_links (list): List of dropdown link components
        dropdown_id (str): Unique identifier for this dropdown (default: "dropdown")
        horizontal_padding (int): Horizontal padding for the toggle button (kept for compatibility)
        vertical_padding (int): Vertical padding for the toggle button (kept for compatibility)
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Img(src=icon_src, alt=text, className="sidebar-section-icon"),
                    html.Span(text, className="sidebar-section-text"),
                ],
                className="sidebar-dropdown-toggle",
                id={"type": "sidebar-dropdown-toggle", "index": dropdown_id},
            ),
            html.Div(
                dropdown_links,
                id={"type": "sidebar-dropdown-content", "index": dropdown_id},
                className="sidebar-dropdown-content",
            ),
        ],
        id={"type": "sidebar-dropdown-container", "index": dropdown_id},
        className="sidebar-dropdown-container",
    )


def create_main_content_area():
    """Create the main content area with loading components and page container."""
    return html.Div(
        id="page-container",
        className="page-container",
        children=[
            dcc.Loading(
                children=[html.Div(id="results-output-container", className="loading-container mb-4")],
                type="dot",
                fullscreen=True,
            ),
            dcc.Loading(
                dbc.Badge(
                    children="Data Loaded",
                    id="data-badge",
                    className="data-badge me-1",
                ),
                type="cube",
            ),
            dash.page_container,
        ],
    )


def create_sidebar_navigation():
    """Create the sidebar navigation menu."""
    return html.Div(
        className="sidebar-navigation",
        children=[
            sidebar_section(
                "/assets/repo_overview.svg",
                "Repo Overview",
                "/repo_overview",
            ),
            sidebar_section(
                None,
                "Code Languages",
                "/repo_overview#code-languages",
            ),
            sidebar_section(
                None,
                "Package Version",
                "/repo_overview#package-version",
            ),
            sidebar_section(
                None,
                "OSSF Scorecard",
                "/repo_overview#ossf-scorecard",
            ),
            sidebar_section(
                None,
                "Repo General Info",
                "/repo_overview#repo-general-info",
            ),
            sidebar_section(
                "/assets/contributions.svg",
                "Contributions",
                "/contributions",
            ),
            sidebar_dropdown(
                "/assets/contributors.svg",
                "Contributors",
                [
                    sidebar_section(
                        icon_src=None,
                        text="Behavior",
                        page_link="/contributors/behavior",
                    ),
                    sidebar_section(
                        text="Contribution Types",
                        page_link="/contributors/contribution_types",
                    ),
                ],
                dropdown_id="contributors-dropdown",
            ),
            sidebar_section(
                "/assets/affiliation.svg",
                "Affiliation",
                "/affiliation",
            ),
            sidebar_section("/assets/chaoss_small.svg", "CHAOSS", "/chaoss"),
        ],
    )


def create_sidebar():
    """Create the collapsible sidebar with search and navigation."""
    return dbc.Collapse(
        html.Div(
            [
                html.Div(
                    [
                        search_bar,
                        create_sidebar_navigation(),
                    ],
                    className="sidebar-body",
                ),
            ],
            className="sidebar-container",
        ),
        id="sidebar-collapse",
        is_open=False,
        dimension="width",
    )


def create_main_layout():
    """Create the main application layout container."""
    return html.Div(
        id="main-layout-container",
        className="main-layout-container",
        children=[
            create_sidebar(),
            create_main_content_area(),
        ],
    )


def create_app_stores():
    """Create application-level data stores."""
    return [
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        dcc.Store(id="job-ids", storage_type="session", data=[]),
        dcc.Store(id="user-group-loading-signal", data="", storage_type="memory"),
        dcc.Location(id="url"),
    ]


def create_storage_quota_script():
    """Create JavaScript for handling storage quota issues."""
    return html.Script(
        """
        window.addEventListener('error', function(event) {
            if (event.message && event.message.toLowerCase().includes('quota') &&
                event.message.toLowerCase().includes('exceeded')) {
                var warningEl = document.getElementById('storage-quota-warning');
                if (warningEl) {
                    warningEl.style.display = 'block';
                }
            }
        });

        try {
            var testKey = 'storage_test';
            var testString = new Array(512 * 1024).join('a');
            sessionStorage.setItem(testKey, testString);
            sessionStorage.removeItem(testKey);
        } catch (e) {
            if (e.name === 'QuotaExceededError' ||
                (e.message &&
                (e.message.toLowerCase().includes('quota') ||
                 e.message.toLowerCase().includes('exceeded')))) {
                var warningEl = document.getElementById('storage-quota-warning');
                if (warningEl) {
                    warningEl.style.display = 'block';
                }
            }
        }
        """
    )


def initialize_components(search_bar_ref):
    """
    Initialize component references from the main layout file.

    Args:
        search_bar_ref: Reference to the search bar component from index_layout.py
                       Used to make the search bar available to sidebar components
    """
    global search_bar
    search_bar = search_bar_ref
