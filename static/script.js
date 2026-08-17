document.addEventListener(
    "DOMContentLoaded",
    function () {
        const form =
            document.getElementById("upload-form");

        form.addEventListener(
            "submit",
            function () {
                console.log("Uploading activities...");
            }
        );
    }
);

// Toggle full activity-type list on/off.
document.getElementById('show-all').addEventListener('change', function () {
    document.querySelectorAll('.extra-type').forEach(function (opt) {
        opt.hidden = !this.checked;
    }, this);
});