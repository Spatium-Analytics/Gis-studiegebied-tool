import VectorSource from "ol/source/Vector";
import VectorLayer from "ol/layer/Vector";
import Draw from "ol/interaction/Draw";
import GeoJSON from "ol/format/GeoJSON";
import { Style, Stroke, Fill } from "ol/style";

const geojsonFormat = new GeoJSON();

function formatCoords(geometry) {
  if (!geometry) return "-";
  let ring = geometry.getCoordinates()[0] || [];
  // GeoJSON polygon rings repeat the first point as the last point to close the
  // ring; that's required for valid output but redundant in a human-readable list.
  if (ring.length > 1) {
    const [firstX, firstY] = ring[0];
    const [lastX, lastY] = ring[ring.length - 1];
    if (firstX === lastX && firstY === lastY) ring = ring.slice(0, -1);
  }
  return ring.map(([x, y]) => `${x.toFixed(2)}, ${y.toFixed(2)}`).join("\n");
}

export function setupDrawing(map) {
  const source = new VectorSource();
  const layer = new VectorLayer({
    source,
    style: new Style({
      stroke: new Stroke({ color: "#1a73e8", width: 2 }),
      fill: new Fill({ color: "rgba(26, 115, 232, 0.15)" }),
    }),
  });
  map.addLayer(layer);

  const coordsBox = document.getElementById("coords-box");
  let draw = null;
  let currentFeature = null;

  function startDrawing(onChange) {
    if (draw) map.removeInteraction(draw);
    source.clear();
    coordsBox.textContent = "-";
    draw = new Draw({ source, type: "Polygon" });
    map.addInteraction(draw);

    draw.on("drawstart", (event) => {
      event.feature.getGeometry().on("change", (geomEvent) => {
        coordsBox.textContent = formatCoords(geomEvent.target);
      });
    });

    draw.on("drawend", (event) => {
      map.removeInteraction(draw);
      draw = null;
      coordsBox.textContent = formatCoords(event.feature.getGeometry());
      // OL adds the sketch feature to the source AFTER dispatching drawend, so
      // reading the source here would race against that and find it still empty.
      // Build the GeoJSON straight from the event's feature instead.
      currentFeature = event.feature;
      onChange(toGeoJSON(event.feature));
    });
  }

  function clear(onChange) {
    if (draw) {
      map.removeInteraction(draw);
      draw = null;
    }
    source.clear();
    currentFeature = null;
    coordsBox.textContent = "-";
    onChange(null);
  }

  function finish() {
    // Lets the user finish a polygon with a button instead of relying on a
    // double-click or closing-the-loop click, which is easy to miss/mistime.
    if (draw) draw.finishDrawing();
  }

  function toGeoJSON(feature) {
    // EPSG:28992 is both the map view and data projection here, so no transform is needed.
    return JSON.parse(geojsonFormat.writeFeature(feature));
  }

  function getPolygonGeoJSON() {
    return currentFeature ? toGeoJSON(currentFeature) : null;
  }

  return { startDrawing, clear, finish, getPolygonGeoJSON };
}
