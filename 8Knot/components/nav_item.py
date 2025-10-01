from dash import html
import dash_bootstrap_components as dbc


# All-in-One Components should be suffixed with 'AIO'
class NavItemAIO(dbc.NavLink):
    def __init__(
        self,
        text,
        link_ref,
        image_path=None,
        image_alt=None,
        external_link=False,
        active="partial",
    ):
        """
        Creates a clickable section in the sidebar, which allows navigation to different pages

        Args:
            text: The text that will be displayed in the sidebar section
            link_ref: The path of the page to navigate to.
            image_path : The path to an icon for the navigation entry (default: None)
            image_alt (str): The alt text to set on the icon (defaults to the title)
            external_link (boolean): whether or not to treat this link as external (i.e. trigger a full browser refresh). This will be true if link target is an identifier on this page (default: False)
            active (str): when to consider each link "active" for the purpose of styling. Accepts the same values as dbc.NavLink's active argument. (Default: "partial")
        """

        if "#" in link_ref:
            external_link = True

        children = None

        if image_path is not None:
            if image_alt is None:
                image_alt = text

            children = [
                html.Img(src=image_path, alt=image_alt, className="sidebar-section-icon"),
                html.Span(text, className="sidebar-section-text"),
            ]
        else:
            children = text

        # Define the component's layout
        super().__init__(
            children,
            external_link=external_link,
            href=link_ref,
            active=active,
            className=("sidebar-section" if image_path is not None else "sidebar-section-text"),
        )
