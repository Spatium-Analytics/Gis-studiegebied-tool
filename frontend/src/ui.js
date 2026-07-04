import { getLayers, createJob, getJobStatus, downloadUrl } from "./api.js";

export async function setupUI(drawing) {
  const layerListEl = document.getElementById("layer-list");
  const layerSearchEl = document.getElementById("layer-search");
  const selectAllBtn = document.getElementById("btn-select-all");
  const deselectAllBtn = document.getElementById("btn-deselect-all");
  const downloadBtn = document.getElementById("btn-download");
  const drawBtn = document.getElementById("btn-draw");
  const finishBtn = document.getElementById("btn-finish");
  const clearBtn = document.getElementById("btn-clear");
  const statusEl = document.getElementById("status");
  const formatSelect = document.getElementById("output-format");
  const layerCountEl = document.getElementById("layer-count");

  let currentPolygon = null;
  let allLayers = [];

  function updateDownloadButton() {
    const anyChecked = [...layerListEl.querySelectorAll("input[type=checkbox]:checked")].some((cb) => cb.checked);
    downloadBtn.disabled = !(currentPolygon && anyChecked);
  }
  layerListEl.addEventListener("change", updateDownloadButton);

  drawBtn.addEventListener("click", () => {
    statusEl.textContent = "Klik op de kaart om punten te plaatsen...";
    drawing.startDrawing((polygon) => {
      currentPolygon = polygon;
      statusEl.textContent = polygon ? "Polygoon voltooid. Kies kaartlagen en klik op Download." : "";
      updateDownloadButton();
    });
  });
  finishBtn.addEventListener("click", () => drawing.finish());
  clearBtn.addEventListener("click", () => {
    drawing.clear((polygon) => {
      currentPolygon = polygon;
      statusEl.textContent = "";
      updateDownloadButton();
    });
  });

  downloadBtn.addEventListener("click", async () => {
    const selectedKeys = [...layerListEl.querySelectorAll("input[type=checkbox]:checked")].map((cb) => cb.value);
    if (!currentPolygon || selectedKeys.length === 0) return;
    downloadBtn.disabled = true;
    statusEl.textContent = "Job aanmaken...";
    try {
      const { job_id } = await createJob(currentPolygon, selectedKeys, formatSelect.value);
      await pollJob(job_id);
    } catch (err) {
      statusEl.textContent = `Fout: ${err.message}`;
      updateDownloadButton();
    }
  });

  async function pollJob(jobId) {
    for (;;) {
      const job = await getJobStatus(jobId);
      const done = Object.values(job.progress).filter((v) => v === "done").length;
      const total = Object.keys(job.progress).length;
      statusEl.textContent = `Status: ${job.status} (${done}/${total} lagen klaar)`;
      if (job.status === "done") {
        if (job.error_detail) statusEl.textContent += `\nWaarschuwing: ${job.error_detail}`;
        window.location.href = downloadUrl(jobId);
        updateDownloadButton();
        return;
      }
      if (job.status === "error") {
        statusEl.textContent += `\nFout: ${job.error_detail}`;
        updateDownloadButton();
        return;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
  }

  function renderLayers(filter) {
    const q = (filter || "").toLowerCase();
    layerListEl.innerHTML = "";
    for (const layer of allLayers) {
      if (q && !layer.label.toLowerCase().includes(q)) continue;
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = layer.key;
      label.appendChild(checkbox);
      const text = document.createElement("span");
      text.textContent = layer.label;
      text.title = layer.notes || layer.description;
      label.appendChild(text);
      layerListEl.appendChild(label);
    }
    updateDownloadButton();
  }

  if (layerSearchEl) layerSearchEl.addEventListener("input", () => renderLayers(layerSearchEl.value));
  if (selectAllBtn) {
    selectAllBtn.addEventListener("click", () => {
      layerListEl.querySelectorAll("input[type=checkbox]").forEach((cb) => (cb.checked = true));
      updateDownloadButton();
    });
  }
  if (deselectAllBtn) {
    deselectAllBtn.addEventListener("click", () => {
      layerListEl.querySelectorAll("input[type=checkbox]").forEach((cb) => (cb.checked = false));
      updateDownloadButton();
    });
  }

  try {
    allLayers = await getLayers();
    if (layerCountEl) layerCountEl.textContent = `(${allLayers.length})`;
    renderLayers("");
  } catch (err) {
    layerListEl.textContent = `Kon kaartlagen niet laden: ${err.message}`;
  }
}
