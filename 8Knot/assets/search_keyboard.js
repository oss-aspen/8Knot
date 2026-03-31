/**
 * Cascading Enter key handler for the search bar.
 *
 * When the Mantine MultiSelect dropdown is OPEN, Enter selects the
 * highlighted item (Mantine's default behavior — we do nothing).
 *
 * When the dropdown is CLOSED, Enter triggers the search by clicking
 * the search button, which fires the existing Dash callback chain.
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

            // Check if the Mantine dropdown is currently open
            var dropdown = document.querySelector(
                ".mantine-MultiSelect-dropdown"
            );
            if (dropdown) {
                // Dropdown is open — let Mantine handle the Enter key
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
