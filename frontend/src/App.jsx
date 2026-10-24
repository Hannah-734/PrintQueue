import { useEffect, useState, useCallback } from "react";
import { api } from "./api.js";

const COLUMNS = [
  ["queued", "Queued"],
  ["printing", "Printing"],
  ["post_processing", "Post-processing"],
  ["inspection", "Inspection"],
  ["shipped", "Shipped"],
];
const NEXT = { queued: "printing", printing: "post_processing", post_processing: "inspection" };
const EMPTY = { name: "", material: "", deadline: "", printer_id: "", layer_height: "", infill: "", nozzle_temp: "", bed_temp: "" };

function dueState(job) {
  if (job.status === "shipped") return null;
  const days = Math.ceil((new Date(job.deadline + "T00:00:00") - new Date().setHours(0, 0, 0, 0)) / 864e5);
  if (days < 0) return { cls: "overdue", text: `Overdue by ${-days}d` };
  if (days <= 2) return { cls: "soon", text: days === 0 ? "Due today" : `Due in ${days}d` };
  return null;
}

const num = (v, f = Number) => (v === "" ? null : f(v));

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [printers, setPrinters] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [j, p, all] = await Promise.all([api.jobs(filter), api.printers(), api.jobs()]);
      setJobs(j);
      setPrinters(p);
      setMaterials([...new Set(all.map((x) => x.material))].sort());
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const run = async (fn) => {
    try { await fn(); await load(); } catch (e) { setError(e.message); }
  };

  const submit = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createJob({
        name: form.name, material: form.material, deadline: form.deadline,
        printer_id: num(form.printer_id), layer_height: num(form.layer_height, parseFloat),
        infill: num(form.infill), nozzle_temp: num(form.nozzle_temp), bed_temp: num(form.bed_temp),
      });
      setForm(EMPTY);
    });
  };

  const field = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) });
  const printerName = (id) => printers.find((p) => p.id === id)?.name;

  const fail = (job) => {
    const note = window.prompt("What failed inspection?");
    if (note?.trim()) run(() => api.inspect(job.id, false, note));
  };

  return (
    <div className="app">
      <header>
        <h1>PrintQueue</h1>
        <label>Material
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">All materials</option>
            {materials.map((m) => <option key={m}>{m}</option>)}
          </select>
        </label>
      </header>

      {error && <p className="error" role="alert">{error}</p>}

      <form className="new-job" onSubmit={submit}>
        <input placeholder="Job name" required {...field("name")} />
        <input placeholder="Material (PETG)" required {...field("material")} />
        <input type="date" required aria-label="Deadline" {...field("deadline")} />
        <select aria-label="Printer" {...field("printer_id")}>
          <option value="">No printer yet</option>
          {printers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <input type="number" step="0.01" placeholder="Layer mm" {...field("layer_height")} />
        <input type="number" min="0" max="100" placeholder="Infill %" {...field("infill")} />
        <input type="number" placeholder="Nozzle °C" {...field("nozzle_temp")} />
        <input type="number" placeholder="Bed °C" {...field("bed_temp")} />
        <button type="submit">Add job</button>
      </form>

      <main className="board">
        {COLUMNS.map(([status, label]) => {
          const items = jobs.filter((j) => j.status === status);
          return (
            <section key={status} className={`col ${status}`}>
              <h2>{label} <span>{items.length}</span></h2>
              {items.length === 0 && <p className="empty">No jobs here.</p>}
              {items.map((job) => {
                const due = dueState(job);
                return (
                  <article key={job.id} className="job">
                    <h3>{job.name}</h3>
                    <p>{job.material} · due {job.deadline}</p>
                    {due && <p className={`badge ${due.cls}`}>{due.text}</p>}
                    {job.printer_id && <p>On {printerName(job.printer_id)}</p>}
                    <p className="settings">
                      {[job.layer_height && `${job.layer_height}mm`, job.infill != null && `${job.infill}% infill`,
                        job.nozzle_temp && `${job.nozzle_temp}°C nozzle`, job.bed_temp && `${job.bed_temp}°C bed`]
                        .filter(Boolean).join(", ")}
                    </p>
                    {job.inspection_note && status === "queued" && <p className="badge overdue">Reprint: {job.inspection_note}</p>}
                    <div className="actions">
                      {NEXT[status] && <button onClick={() => run(() => api.updateJob(job.id, { status: NEXT[status] }))}>Move forward</button>}
                      {status === "inspection" && <>
                        <button onClick={() => run(() => api.inspect(job.id, true, ""))}>Pass</button>
                        <button className="danger" onClick={() => fail(job)}>Fail</button>
                      </>}
                      <button className="quiet" onClick={() => window.confirm(`Delete ${job.name}?`) && run(() => api.deleteJob(job.id))}>Delete</button>
                    </div>
                  </article>
                );
              })}
            </section>
          );
        })}
      </main>

      <Printers printers={printers} run={run} />
    </div>
  );
}

function Printers({ printers, run }) {
  const [name, setName] = useState("");
  const [notes, setNotes] = useState({});
  return (
    <section className="printers">
      <h2>Printers and maintenance</h2>
      <form onSubmit={(e) => { e.preventDefault(); run(() => api.createPrinter(name)); setName(""); }}>
        <input placeholder="Printer name" required value={name} onChange={(e) => setName(e.target.value)} />
        <button type="submit">Add printer</button>
      </form>
      {printers.length === 0 && <p className="empty">Add a printer to start a maintenance log.</p>}
      {printers.map((p) => (
        <div key={p.id} className="printer">
          <h3>{p.name}</h3>
          <form onSubmit={(e) => { e.preventDefault(); run(() => api.addMaintenance(p.id, notes[p.id])); setNotes({ ...notes, [p.id]: "" }); }}>
            <input placeholder="What was done?" required value={notes[p.id] || ""} onChange={(e) => setNotes({ ...notes, [p.id]: e.target.value })} />
            <button type="submit">Log maintenance</button>
          </form>
          <ul>{p.logs.map((l) => <li key={l.id}>{new Date(l.performed_at + "Z").toLocaleDateString()}: {l.note}</li>)}</ul>
        </div>
      ))}
    </section>
  );
}
