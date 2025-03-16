document.addEventListener("DOMContentLoaded", function () {
    console.log("Initializing DataTable filtering...");

    if (typeof jQuery === "undefined") {
        console.error("jQuery is not loaded. Make sure jQuery is included before this script.");
        return;
    }
    if (!$.fn.DataTable) {
        console.error("DataTables is not loaded. Ensure DataTables JS is included.");
        return;
    }

    var table = $("#cnvs-table").DataTable({
        paging: true,
        searching: true,
        lengthChange: true, // use the build in search
        initComplete: function () {
            console.log("DataTable initialized successfully!");
        }
    });
   
});

// TODO: add custom filter - be able to filter the table by any column and consider multiple inputs form different rows.

