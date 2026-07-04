import "ol/ol.css";
import { createMap, BASEMAPS } from "./map.js";
import { setupDrawing } from "./draw.js";
import { setupUI } from "./ui.js";
import { setupSearch } from "./search.js";

window.addEventListener("error", (event) => {
  const statusEl = document.getElementById("status");
  if (statusEl) statusEl.textContent = `JS-fout: ${event.message}`;
});

const { map, setBasemap } = createMap("map");
const drawing = setupDrawing(map);
setupSearch(map);
setupUI(drawing);

const basemapSelect = document.getElementById("basemap-select");
for (const [key, basemap] of Object.entries(BASEMAPS)) {
  const option = document.createElement("option");
  option.value = key;
  option.textContent = basemap.label;
  basemapSelect.appendChild(option);
}
basemapSelect.addEventListener("change", () => setBasemap(basemapSelect.value));
