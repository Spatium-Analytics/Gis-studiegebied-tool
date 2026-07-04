const LOCATIESERVER_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free";

// PDOK Locatieserver's `type` field tells us roughly how large the result is; zooming
// everything to a fixed street-level zoom (as before) overshoots badly for a
// province/municipality/city search. The view's resolution at zoom z is ~3440.64/2^z
// m/px (map.js's RESOLUTIONS), so a ~1000px-wide map shows roughly that many km at
// z=3, narrowing by half each step up - levels below are picked so each result type
// fills a sensible chunk of the viewport instead of one fixed crop.
const ZOOM_BY_TYPE = {
  provincie: 5, // ~108 km across
  gemeente: 7, // ~27 km across
  woonplaats: 9, // ~6.7 km across
  wijk: 10, // ~3.4 km across
  buurt: 11, // ~1.7 km across
  weg: 12, // ~840 m across
  postcode: 13, // ~420 m across
  adres: 15, // ~105 m across
  perceel: 15,
};
const DEFAULT_ZOOM = 10;

async function searchLocations(query) {
  if (!query || query.trim().length < 2) return [];
  const url = `${LOCATIESERVER_URL}?q=${encodeURIComponent(query)}&fl=weergavenaam,centroide_rd,type&rows=6`;
  const resp = await fetch(url);
  if (!resp.ok) return [];
  const data = await resp.json();
  return (data.response?.docs || []).map((doc) => {
    const match = /POINT\(([-\d.]+)\s+([-\d.]+)\)/.exec(doc.centroide_rd || "");
    return {
      label: doc.weergavenaam,
      type: doc.type,
      x: match ? parseFloat(match[1]) : null,
      y: match ? parseFloat(match[2]) : null,
    };
  }).filter((r) => r.x !== null && r.y !== null);
}

export function setupSearch(map) {
  const input = document.getElementById("search-input");
  const resultsEl = document.getElementById("search-results");
  let debounceTimer = null;

  function renderResults(results) {
    resultsEl.innerHTML = "";
    for (const r of results) {
      const li = document.createElement("li");
      li.textContent = r.label;
      li.addEventListener("click", () => {
        const zoom = ZOOM_BY_TYPE[r.type] ?? DEFAULT_ZOOM;
        map.getView().animate({ center: [r.x, r.y], zoom, duration: 400 });
        resultsEl.innerHTML = "";
        input.value = r.label;
      });
      resultsEl.appendChild(li);
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const query = input.value;
    debounceTimer = setTimeout(async () => {
      try {
        const results = await searchLocations(query);
        renderResults(results);
      } catch {
        resultsEl.innerHTML = "";
      }
    }, 300);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("#search-bar")) {
      resultsEl.innerHTML = "";
    }
  });
}
