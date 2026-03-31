/**
 * Cascading Enter key handler for the search bar.
 *
 * When the Mantine MultiSelect dropdown has visible options, Enter
 * selects the highlighted item (Mantine's default behavior — we do nothing).
 *
 * When there are no visible options (dropdown closed or empty), Enter
 * triggers the search by clicking the search button.
 */
document.addEventListener("DOMContentLoaded", function () {
    // Use MutationObserver to attach the handler once the MultiSelect input exists
    var observer = new MutationObserver(function () {
        var input = document.querySelector("#projects input");
        if (!input) return;

        // Stop observing once we've found the input
        observer.disconnect();

        input.addEventListener("keydown", function (e) {
            if (e.key !== "Enter") return;

            // Check if the dropdown has visible selectable options.
            // Mantine keeps the dropdown element in the DOM while focused,
            // so we check for actual option elements instead.
            var options = document.querySelectorAll(
                ".mantine-MultiSelect-option"
            );
            if (options.length > 0) {
                // Dropdown has options — let Mantine handle Enter
                // to select the highlighted item
                return;
            }

            // Dropdown is closed — trigger search
            e.preventDefault();
            var searchButton = document.getElementById("search-button");
            if (searchButton) {
                searchButton.click();
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
