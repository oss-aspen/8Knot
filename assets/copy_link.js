/**
 * Copy-link functionality for visualization cards.
 *
 * This clientside callback is registered with MATCH pattern to handle
 * all copy-link buttons across all VisualizationAIO cards.
 *
 * When clicked, constructs a URL with the current query string and the
 * card's anchor fragment, then copies it to clipboard.
 */
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        copy_link_to_clipboard: function(n_clicks, btn_id) {
            if (!n_clicks) {
                return window.dash_clientside.no_update;
            }

            // Extract anchor from button's pattern-matching ID
            var anchor = btn_id["index"];

            // Build full URL: origin + pathname + search + #anchor
            var url = window.location.origin
                    + window.location.pathname
                    + window.location.search
                    + "#" + anchor;

            /**
             * Fallback clipboard copy for browsers without Clipboard API.
             * Creates a temporary textarea, selects it, and uses execCommand.
             */
            function copyFallback(text) {
                var ta = document.createElement("textarea");
                ta.value = text;
                ta.style.position = "fixed";
                ta.style.opacity = "0";
                document.body.appendChild(ta);
                ta.focus();
                ta.select();
                try {
                    document.execCommand("copy");
                } catch (_e) {
                    // Silent fail - user will notice link wasn't copied
                }
                document.body.removeChild(ta);
            }

            // Try modern Clipboard API first, fallback to execCommand
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).catch(function() {
                    copyFallback(url);
                });
            } else {
                copyFallback(url);
            }

            return n_clicks;
        }
    }
});
