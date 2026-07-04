const API_BASE = "http://localhost:8000/api";

export async function getLayers() {
  const resp = await fetch(`${API_BASE}/layers`);
  if (!resp.ok) throw new Error(`Kon lagen niet laden (${resp.status})`);
  return resp.json();
}

export async function createJob(polygonFeatureGeoJSON, layerKeys, outputFormat) {
  const resp = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      polygon: polygonFeatureGeoJSON.geometry,
      crs: "EPSG:28992",
      layers: layerKeys,
      output_format: outputFormat,
    }),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}));
    throw new Error(detail.detail || `Job aanmaken mislukt (${resp.status})`);
  }
  return resp.json();
}

export async function getJobStatus(jobId) {
  const resp = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!resp.ok) throw new Error(`Status ophalen mislukt (${resp.status})`);
  return resp.json();
}

export function downloadUrl(jobId) {
  return `${API_BASE}/jobs/${jobId}/download`;
}
