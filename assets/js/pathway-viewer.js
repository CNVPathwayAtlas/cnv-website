// Zoom control for the static pathway SVG on the CNV page
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".pathway-container").forEach(function (container) {
    var img = container.querySelector(".pathway-canvas img");
    var resetButton = container.querySelector('[data-zoom="reset"]');
    var zoom = 100;

    function setZoom(value) {
      zoom = Math.min(400, Math.max(50, value));
      img.style.width = zoom + "%";
      resetButton.textContent = zoom + "%";
    }

    container.querySelectorAll("[data-zoom]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.dataset.zoom;
        setZoom(action === "in" ? zoom + 25 : action === "out" ? zoom - 25 : 100);
      });
    });
  });
});
