async function call(path, method = "GET", body) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = Array.isArray(err.detail) ? err.detail.map((d) => d.msg).join(", ") : err.detail;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  jobs: (material) => call(`/jobs${material ? `?material=${encodeURIComponent(material)}` : ""}`),
  createJob: (job) => call("/jobs", "POST", job),
  updateJob: (id, changes) => call(`/jobs/${id}`, "PATCH", changes),
  deleteJob: (id) => call(`/jobs/${id}`, "DELETE"),
  inspect: (id, passed, note) => call(`/jobs/${id}/inspection`, "POST", { passed, note }),
  printers: () => call("/printers"),
  createPrinter: (name) => call("/printers", "POST", { name }),
  addMaintenance: (id, note) => call(`/printers/${id}/maintenance`, "POST", { note }),
};
