import { register } from "ol/proj/proj4";
import { get as getProjection } from "ol/proj";
import proj4 from "proj4";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import WMTS from "ol/source/WMTS";
import WMTSTileGrid from "ol/tilegrid/WMTS";
import { getTopLeft, getWidth } from "ol/extent";

// RD New (Amersfoort / RD New), official EPSG.io definition string.
proj4.defs(
  "EPSG:28992",
  "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 " +
    "+k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel " +
    "+towgs84=565.4171,50.3319,465.5524,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs"
);
register(proj4);

const rdNew = getProjection("EPSG:28992");
const projectionExtent = [-285401.92, 22598.08, 595401.92, 903401.92];
rdNew.setExtent(projectionExtent);

// Shared between the WMTS tile grid and the View: without an explicit resolutions
// array, View can't derive a valid resolution for a custom (non-default) projection,
// which silently results in a NaN resolution and zero tile requests ever being made.
const RESOLUTIONS = [];
const MATRIX_IDS = [];
{
  const size = getWidth(projectionExtent) / 256;
  for (let z = 0; z < 15; z += 1) {
    RESOLUTIONS.push(size / 2 ** z);
    MATRIX_IDS.push(String(z));
  }
}

// All PDOK background WMTS services (BRT achtergrondkaart variants + the aerial-photo
// luchtfoto service) publish the same EPSG:28992 tile grid (origin/resolutions), so one
// shared tileGrid/RESOLUTIONS setup works for every basemap option below.
export const BASEMAPS = {
  standaard: {
    label: "Standaard",
    url: "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{TileMatrix}/{TileCol}/{TileRow}.png",
    layer: "standaard",
  },
  grijs: {
    label: "Grijs",
    url: "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992/{TileMatrix}/{TileCol}/{TileRow}.png",
    layer: "grijs",
  },
  pastel: {
    label: "Pastel",
    url: "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/pastel/EPSG:28992/{TileMatrix}/{TileCol}/{TileRow}.png",
    layer: "pastel",
  },
  luchtfoto: {
    label: "Luchtfoto (satelliet)",
    url: "https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/Actueel_orthoHR/EPSG:28992/{TileMatrix}/{TileCol}/{TileRow}.jpeg",
    layer: "Actueel_orthoHR",
  },
};

function buildWmtsSource(basemapKey) {
  const basemap = BASEMAPS[basemapKey];
  return new WMTS({
    url: basemap.url,
    layer: basemap.layer,
    matrixSet: "EPSG:28992",
    format: basemap.url.endsWith(".jpeg") ? "image/jpeg" : "image/png",
    projection: rdNew,
    requestEncoding: "REST",
    tileGrid: new WMTSTileGrid({
      origin: getTopLeft(projectionExtent),
      resolutions: RESOLUTIONS,
      matrixIds: MATRIX_IDS,
    }),
    style: "default",
  });
}

export function createMap(targetId) {
  const baseLayer = new TileLayer({ source: buildWmtsSource("standaard") });

  const map = new Map({
    target: targetId,
    layers: [baseLayer],
    view: new View({
      projection: rdNew,
      extent: projectionExtent,
      center: [155000, 463000], // centre of the Netherlands in RD New
      resolutions: RESOLUTIONS,
      zoom: 3,
    }),
  });

  function setBasemap(basemapKey) {
    baseLayer.setSource(buildWmtsSource(basemapKey));
  }

  return { map, setBasemap };
}

export { rdNew };
