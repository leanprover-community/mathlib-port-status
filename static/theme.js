
function getTheme() {
    return localStorage.getItem("theme") || "system";
}

function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    if (themeName == "system") {
        themeName = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    document.documentElement.setAttribute('data-bs-theme', themeName);
}

setTheme(getTheme())

$(document).ready(function () {
    let tables = $('.main-table').DataTable({
        // the default, but no search
        dom: "<'row'<'col-sm-12 col-md-6'l>>" +
            "<'row'<'col-sm-12'tr>>" +
            "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        columnDefs: [
            { targets: 'lines-column', width: '4em'},
        ]
    });

    $('#search-input').on('search', function(e) {
        tables.search(this.value).draw();
    });

    // also check to see if the user changes their theme settings while the page is loaded.
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        setTheme(getTheme());
    })

    window.addEventListener('storage', (event) => setTheme(getTheme()));
});