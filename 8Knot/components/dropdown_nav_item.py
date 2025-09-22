from dash import Output, Input, html, callback, ALL
import dash_bootstrap_components as dbc


# All-in-One Components should be suffixed with 'AIO'
class DropdownNavItemAIO(html.Div):
    def __init__(self, children: list, image_path: str, title: str, link_ref: str, image_alt=None, external_link=False):
        """
        Creates a clickable section in the sidebar, which allows navigation to a page and displays a list of sub pages when active

        Args:
            children (list): The navigation items items to display underneath this one
            image_path (str): The path to an icon for the navigation entry
            title (str): The text that will be displayed as the title of this nav item next to the icon
            link_ref (str): The path of the page to navigate to
            image_alt (str): The alt text to set on the icon (defaults to the title)
            external_link (boolean): whether or not to treat this link as external (i.e. trigger a full browser refresh) (default: False)
        """

        if image_alt is None:
            image_alt = title

        collapse_id = {"type": "collapse-menu", "index": link_ref}
        topLink_id = {"type": "topLink", "index": link_ref}

        # Define the component's layout
        super().__init__(
            [
                dbc.NavLink(
                    [
                        html.Img(src=image_path, alt=image_alt, className="sidebar-section-icon"),
                        html.Span(title, className="sidebar-section-text"),
                    ],
                    external_link=external_link,
                    href=link_ref,
                    id=topLink_id,
                    active="partial",
                ),
                dbc.Collapse(
                    children,
                    id=collapse_id,
                    is_open=False,  # The callback will manage this
                ),
            ],
            className="sidebar-dropdown-container",
        )

    @callback(
        Output({"type": "collapse-menu", "index": ALL}, "is_open"),
        Input({"type": "topLink", "index": ALL}, "href"),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )
    def toggle_collapses_dynamically(href, pathname):
        """
        This dynamic callback manages the state of all collapsible nav items
        by matching components with a dictionary ID.
        """
        return list(map(pathname.startswith, href))
