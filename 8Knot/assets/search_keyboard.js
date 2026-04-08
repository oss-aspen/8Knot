/**
 * Cascading Enter key handler for the search bar.
 *
 * When the Mantine MultiSelect dropdown is open (aria-expanded="true"),
 * Enter selects the highlighted item (Mantine's default — we do nothing).
 *
 * When the dropdown is closed, Enter triggers the search by incrementing
 * the search-trigger dcc.Store via dash_clientside.set_props.
 */
document.addEventListener("DOMContentLoaded", function () {
    var observer = new MutationObserver(function () {
        var input = document.querySelector("#projects input");
        if (!input) return;

        observer.disconnect();

        input.addEventListener("keydown", function (e) {
            if (e.key !== "Enter") return;

            // If dropdown is open, let Mantine handle Enter to select the highlighted item
            if (input.getAttribute("aria-expanded") === "true") return;

            // Dropdown is closed — trigger search via the dcc.Store
            e.preventDefault();
            var store = document.querySelector("#search-trigger");
            var current = store ? JSON.parse(store.textContent || "0") : 0;
            dash_clientside.set_props("search-trigger", { data: current + 1 });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
