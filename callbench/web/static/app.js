const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pct = (x) => `${Math.round(x * 100)}%`;
const LANG = {en: "English", es: "Spanish", zh: "Mandarin", hinglish: "Hinglish"};

// ---------- tabs
document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.setAttribute("aria-selected", x === b));
  document.querySelectorAll("main > section").forEach((s) => (s.hidden = s.id !== b.dataset.tab));
}));

// ---------- sliders
const bind = (id, fmt) => { const el = $("#" + id), v = $("#" + id + "V"); const f = () => (v.textContent = fmt(el.value)); el.addEventListener("input", f); f(); };
bind("runs", (v) => v); bind("budget", (v) => `${v} ms`); bind("noise", (v) => (+v).toFixed(2));
bind("ints", (v) => (+v).toFixed(2)); bind("cnoise", (v) => (+v).toFixed(2));

// ---------- personas
async function loadPersonas() {
  const sc = await (await fetch("/api/scenario")).json();
  $("#plist").innerHTML = sc.personas.map((p) => `
    <label class="persona"><input type="checkbox" value="${esc(p.name)}" checked>
      <div><div>${esc(p.name.replaceAll("_", " "))}</div>
      <div class="meta">${LANG[p.language] || p.language} · ${esc(p.style)} · expects <b>${esc(p.expect)}</b></div></div></label>`).join("");
}
$("#all").onclick = () => document.querySelectorAll("#plist input").forEach((i) => (i.checked = true));
$("#none").onclick = () => document.querySelectorAll("#plist input").forEach((i) => (i.checked = false));

// ---------- run suite
const tone = (r) => (r >= 0.8 ? "ok" : r >= 0.5 ? "warn" : "bad");
function bars(obj, label = (k) => k) {
  return `<div class="bars">${Object.entries(obj).map(([k, v]) => `
    <div class="bar"><div>${esc(label(k))}</div><div class="track"><div class="fill ${tone(v)}" style="width:${Math.max(2, v * 100)}%"></div></div><div class="pct">${pct(v)}</div></div>`).join("")}</div>`;
}
function bubble(t) {
  const who = t.speaker === "agent" ? "Agent" : "Caller";
  const heard = t.speaker === "caller" && t.heard_as && t.heard_as !== t.text ? `<div class="heard">STT heard: ${esc(t.heard_as)}</div>` : "";
  const lat = t.latency_ms != null ? `<div class="lat">${Math.round(t.latency_ms)} ms${t.barge_in ? " · caller interrupted" : ""}${t.action && t.action !== "continue" ? " · " + esc(t.action) : ""}</div>` : "";
  return `<div class="bub ${t.speaker}"><div class="who">${who}</div>${esc(t.text)}${heard}${lat}</div>`;
}
function callCard(c, i) {
  const checks = Object.entries(c.checks).map(([k, ok]) => `<span class="chip ${ok ? "ok" : "bad"}">${ok ? "✓" : "✕"} ${esc(k.replaceAll("_", " "))}</span>`).join("");
  const notes = c.notes.length ? `<div class="muted" style="font-size:13px;margin-bottom:8px">${esc(c.notes.join("; "))}</div>` : "";
  return `<details class="call" data-pass="${c.passed}"><summary>
      <span class="chip ${c.passed ? "ok" : "bad"}">${c.passed ? "PASS" : "FAIL"}</span>
      <span class="name">${esc(c.persona.replaceAll("_", " "))}</span><span class="muted">#${i + 1} · ${LANG[c.language] || c.language}</span>
      <span class="right"><span class="chip">expected ${esc(c.expected.outcome)}</span><span class="chip ${c.actual_outcome === c.expected.outcome ? "ok" : "bad"}">got ${esc(c.actual_outcome)}</span>
      <span class="chip">p95 ${Math.round(c.latency_p95_ms)} ms</span><span class="chip">WER ${pct(c.wer)}</span></span></summary>
      <div class="body"><div class="checks">${checks}</div>${notes}<div class="bubbles">${c.transcript.map(bubble).join("")}</div></div></details>`;
}
function render(data) {
  const s = data.summary;
  const failed = Object.entries(s.failed_checks).map(([k, n]) => `<span class="chip bad">${esc(k.replaceAll("_", " "))}: ${n}</span>`).join("") || `<span class="chip ok">none</span>`;
  $("#results").innerHTML = `
    <div class="tiles">
      <div class="tile"><div class="k">Calls</div><div class="n">${s.calls}</div></div>
      <div class="tile"><div class="k">Pass rate</div><div class="n ${tone(s.pass_rate)}">${pct(s.pass_rate)}</div></div>
      <div class="tile"><div class="k">p50 latency</div><div class="n">${Math.round(s.latency_p50_ms)}<small class="muted"> ms</small></div></div>
      <div class="tile"><div class="k">p95 latency</div><div class="n">${Math.round(s.latency_p95_ms)}<small class="muted"> ms</small></div></div>
      <div class="tile"><div class="k">Mean STT error</div><div class="n">${pct(s.mean_wer)}</div></div>
      <div class="tile"><div class="k">Interruptions</div><div class="n">${s.barge_ins}</div></div>
    </div>
    <div class="two">
      <div class="card"><h2>Pass rate by persona</h2>${bars(s.by_persona, (k) => k.replaceAll("_", " "))}</div>
      <div class="card"><h2>Pass rate by language</h2>${bars(s.by_language, (k) => LANG[k] || k)}
        <h3>Failed checks</h3><div class="row">${failed}</div></div>
    </div>
    <div class="card"><div class="row" style="justify-content:space-between"><h2 style="margin:0">Calls</h2>
      <div class="filter"><button class="btn sm" data-f="all">All</button><button class="btn sm" data-f="fail">Failures only</button></div></div>
      <div id="calls">${data.calls.map(callCard).join("")}</div></div>`;
  document.querySelectorAll("[data-f]").forEach((b) => (b.onclick = () =>
    document.querySelectorAll("#calls .call").forEach((c) => (c.hidden = b.dataset.f === "fail" && c.dataset.pass === "true"))));
  $("#runinfo").textContent = `Ran ${s.calls} calls in ${Math.round(data.elapsed_ms)} ms.`;
}
$("#run").onclick = async () => {
  const personas = [...document.querySelectorAll("#plist input:checked")].map((i) => i.value);
  if (!personas.length) { $("#runinfo").textContent = "Pick at least one persona."; return; }
  const btn = $("#run"); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Running…';
  try {
    const r = await fetch("/api/run", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
      personas, seed: +$("#seed").value, runs_per_persona: +$("#runs").value, latency_budget_ms: +$("#budget").value,
      extra_noise: +$("#noise").value, extra_interrupts: +$("#ints").value})});
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    render(data);
  } catch (e) { $("#runinfo").textContent = "Error: " + e.message; }
  finally { btn.disabled = false; btn.textContent = "Run suite"; }
};

// ---------- chat with the agent
let sid = null;
const QUICK = ["The employee's name is Priya Sharma.", "They worked here from March 2019 to June 2023.",
  "Their job title was Senior Data Analyst.", "Yes, that's right.", "What company is this?", "Can I speak to a real person?"];
$("#quick").innerHTML = QUICK.map((q) => `<button class="btn sm" type="button">${esc(q)}</button>`).join("");
$("#quick").onclick = (e) => { if (e.target.tagName === "BUTTON" && sid) { $("#say").value = e.target.textContent; send(); } };
function showTurn(heardAs, said, turn) {
  const box = $("#chatbox");
  if (said != null) box.insertAdjacentHTML("beforeend", bubble({speaker: "caller", text: said, heard_as: heardAs}));
  box.insertAdjacentHTML("beforeend", bubble({speaker: "agent", text: turn.text, latency_ms: turn.latency_ms, action: turn.action}));
  box.scrollTop = box.scrollHeight;
  const ex = turn.extracted || {};
  const done = turn.action !== "continue";
  $("#captured").innerHTML = `<dt>Status</dt><dd>${done ? `<span class="chip ${turn.action === "hangup" && ex.job_title ? "ok" : "warn"}">${esc(turn.action)}</span>` : "in call"}</dd>` +
    ["employee_name", "start_date", "end_date", "job_title"].map((k) => `<dt>${k.replace("_", " ")}</dt><dd>${esc(ex[k] || "—")}</dd>`).join("");
  $("#say").disabled = $("#send").disabled = done;
  if (done) { box.insertAdjacentHTML("beforeend", `<div class="muted" style="text-align:center;font-size:13px">Call ended — press Start call to try again.</div>`); sid = null; }
}
$("#dial").onclick = async () => {
  $("#chatbox").innerHTML = "";
  const opening = $("#opening").value;
  const r = await (await fetch("/api/chat/start", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({opening, noise: +$("#cnoise").value, seed: Math.floor(Math.random() * 1e6)})})).json();
  sid = r.session_id;
  $("#chatbox").insertAdjacentHTML("beforeend", bubble({speaker: "caller", text: opening, heard_as: r.heard_as}));
  showTurn(null, null, r.turn);
  $("#say").focus();
};
async function send() {
  const text = $("#say").value.trim(); if (!text || !sid) return;
  $("#say").value = "";
  const r = await fetch(`/api/chat/${sid}`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({text})});
  const d = await r.json();
  if (!r.ok) { $("#chatbox").insertAdjacentHTML("beforeend", `<div class="banner">${esc(d.detail)}</div>`); return; }
  showTurn(d.heard_as, text, d.turn);
}
$("#composer").onsubmit = (e) => { e.preventDefault(); send(); };

loadPersonas();
