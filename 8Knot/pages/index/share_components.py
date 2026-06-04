"""
Share link UI components.

This module defines the modal and supporting elements used by the
shareable URL system. It is kept SEPARATE from `index_components.py`
to avoid polluting the existing layout shell (`create_app_stores`,
`create_main_content_area`) — past attempts to mix share-related
components into those functions broke Dash's page rendering because
elements like Toasts and Clipboards do not behave as inert stores.

Architecture notes:
- All components returned by `create_share_modal()` are wrapped in a
  single `html.Div` so the layout file only needs to add one child.
- The modal stays `is_open=False` until a callback opens it.
- A `dcc.Store` is included so URL-loaded state can flow through a
  brand-new channel (avoids `allow_duplicate=True` conflicts with the
  existing `repo-choices` store).
- No callbacks are defined in this file — they live in
  `index_callbacks.py` so registration happens through the standard
  import path used by `app.py`.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_share_modal() -> html.Div:
    """Return the share-link modal and its supporting state store.

    The returned Div is intended to be added as a direct child of the
    main `dbc.Container` in `index_layout.py`, AFTER all existing
    layout elements. It must not be placed inside `create_app_stores()`.
    """
    return html.Div(
        id="share-system-container",
        children=[
            # State channel for URL-loaded share payloads.
            # Consumed by a separate callback that drives the existing
            # multiselect/search flow — never written to `repo-choices`
            # directly.
            dcc.Store(id="share-loaded-state", data=None),
            # No-op output target for the clientside scroll-to-anchor callback.
            dcc.Store(id="share-scroll-dummy", data=None),
            # Inline feedback shown when a shared link fails to load
            # (expired, corrupted, or pointing at a removed graph).
            # Owned by exactly one callback (`handle_share_url`).
            dbc.Alert(
                "",
                id="share-load-alert",
                is_open=False,
                dismissable=True,
                color="warning",
                className="share-load-alert",
            ),
            dbc.Modal(
                id="share-modal",
                is_open=False,
                size="lg",
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Share this graph")),
                    dbc.ModalBody(
                        [
                            html.P(
                                "Copy the link below to share this exact view "
                                "(repositories + graph) with someone else.",
                                className="mb-2",
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="share-url-display",
                                        type="text",
                                        readonly=True,
                                        value="",
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-copy me-1"), "Copy"],
                                        id="share-copy-button",
                                        color="primary",
                                        n_clicks=0,
                                    ),
                                ]
                            ),
                            html.Div(
                                id="share-status-message",
                                className="mt-2 text-success",
                            ),
                            html.Div(
                                id="share-warning-text",
                                className="mt-2 text-warning",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="share-modal-close",
                            color="secondary",
                            n_clicks=0,
                        )
                    ),
                ],
            ),
        ],
    )
