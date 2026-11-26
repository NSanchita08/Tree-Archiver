const $ = (s) => document.querySelector(s);
const state = { view: null, archive: null }; // view = display data; archive = saved text
let zoom = 1;

async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { ok: res.ok, data: await res.json() };
}

// Server messages can echo user input, so this always goes through textContent.
function describe(d) {
  return [
    d.error,
    d.position && `Token position ${d.position}.`,
    d.suggestion && `Suggested fix (not applied): ${d.suggestion}`,
  ].filter(Boolean).join(" ");
}

function report(el, data) {
  el.hidden = false;
  el.textContent = describe(data);
}

function go(tab) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === tab));
  document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
}
document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => go(b.dataset.tab)));

function drawTree(svg, view, scale = 1) {
  svg.innerHTML = "";
  if (!view || !view.nodes.length) return;
  const GX = 46, GY = 80, PAD = 48, R = 20;
  const px = (n) => PAD + n.x * GX;
  const py = (n) => PAD + n.y * GY;
  const W = PAD * 2 + Math.max(...view.nodes.map((n) => n.x)) * GX;
  const H = PAD * 2 + Math.max(...view.nodes.map((n) => n.y)) * GY + 60;
  let s = "";
  for (const n of view.nodes) {
    for (const [side, dx] of [["left", -1], ["right", 1]]) {
      const x = px(n), y = py(n);
      if (n[side] === null) {
        const ex = x + dx * 26, ey = y + 56;
        s += `<line class="stub" x1="${x}" y1="${y}" x2="${ex}" y2="${ey}"/>`;
        s += `<text class="stub-label" x="${ex}" y="${ey + 14}">null</text>`;
      } else {
        const c = view.nodes[n[side]];
        s += `<line class="edge-${side}" x1="${x}" y1="${y}" x2="${px(c)}" y2="${py(c)}"/>`;
      }
    }
  }
  for (const n of view.nodes) {
    s += `<circle cx="${px(n)}" cy="${py(n)}" r="${R}"/>`;
    s += `<text class="label" x="${px(n)}" y="${py(n) + 4}">${n.label}</text>`;
  }
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", W * scale);
  svg.setAttribute("height", H * scale);
  svg.innerHTML = s;
}

function setStats(view, status) {
  $("#stat-nodes").textContent = view ? view.count : 0;
  $("#stat-height").textContent = view ? view.height : 0;
  $("#stat-status").textContent = status;
}

async function loadTraversals(archive) {
  const { data } = await post("/api/tree/traversals", { serialized: archive });
  const hint = { preorder: "Root, left, right", inorder: "Left, root, right", postorder: "Left, right, root" };
  $("#traversals").innerHTML = Object.keys(hint).map((k) =>
    `<div class="glass card"><h3>${k[0].toUpperCase() + k.slice(1)}</h3>` +
    `<p class="muted">${hint[k]}</p><code>${data[k].join(" ")}</code></div>`).join("");
}

function showBuild() {
  zoom = 1;
  drawTree($("#tree"), state.view);
  $("#archive").textContent = state.archive || "";
  $("#download").disabled = !state.archive;
  setStats(state.view, state.view ? "Loaded" : "Cleared");
  if (state.view) loadTraversals(state.archive);
  else $("#traversals").innerHTML = "";
}

async function createTree(text) {
  const { ok, data } = await post("/api/tree/create", { text });
  if (!ok) return report($("#build-error"), data);
  $("#build-error").hidden = true;
  state.view = data.view;
  state.archive = data.serialized;
  showBuild();
}

async function restoreFrom(text) {
  const { ok, data } = await post("/api/tree/deserialize", { serialized: text });
  if (!ok) {
    report($("#restore-error"), data);
    return null;
  }
  $("#restore-error").hidden = true;
  drawTree($("#restored-tree"), data.view);
  const card = $("#verify-card");
  card.hidden = !state.archive;
  if (state.archive) {
    // Compare the saved archive snapshot with the restored tree, node by node.
    const v = await post("/api/tree/verify", { original: state.archive, restored: text });
    const h = document.createElement("h2");
    h.textContent = v.data.identical ? "Structurally identical" : "Not identical";
    const p = document.createElement("p");
    p.textContent = v.data.message;
    card.replaceChildren(h, p);
  }
  return data;
}

// Wiring
$("#create").onclick = () => createTree($("#input").value);
$("#zoom-in").onclick = () => { zoom = Math.min(zoom * 1.25, 4); drawTree($("#tree"), state.view, zoom); };
$("#zoom-out").onclick = () => { zoom = Math.max(zoom / 1.25, 0.3); drawTree($("#tree"), state.view, zoom); };
$("#clear").onclick = () => { state.view = null; showBuild(); };
$("#download").onclick = () => {
  const url = URL.createObjectURL(new Blob([state.archive], { type: "text/plain" }));
  Object.assign(document.createElement("a"), { href: url, download: "treevault-archive.txt" }).click();
  URL.revokeObjectURL(url);
};
$("#restore-btn").onclick = () => restoreFrom($("#restore-input").value);
$("#check-btn").onclick = async () => {
  const { data } = await post("/api/tree/validate", { serialized: $("#check-input").value });
  const box = $("#check-result");
  box.hidden = false;
  box.className = data.valid ? "ok" : "error";
  box.textContent = data.valid ? `Valid archive with ${data.nodes} nodes.` : describe(data);
};
document.querySelectorAll("input[type=file]").forEach((input) =>
  input.addEventListener("change", async () => {
    if (input.files[0]) $(input.dataset.target).value = await input.files[0].text();
  }));

// Demo: build, archive, clear the original, restore from text only, verify, reject damage.
$("#demo").onclick = async () => {
  const log = $("#demo-log");
  log.hidden = false;
  log.textContent = "";
  const say = (t) => { log.textContent += t + "\n"; };
  await createTree('["A", "B", "C", null, "D"]');
  say(`1. Built the example tree: ${state.view.count} nodes, height ${state.view.height}.`);
  say(`2. Archive: ${state.archive}`);
  state.view = null;
  showBuild();
  say("3. Original tree cleared from memory.");
  const restored = await restoreFrom(state.archive);
  say(`4. Restored from archive text: ${restored.view.count} nodes.`);
  say(`5. Verification: ${$("#verify-card h2").textContent}.`);
  const bad = await post("/api/tree/validate", { serialized: "A,B,#,D,#" });
  say(`6. Damaged archive A,B,#,D,#: ${describe(bad.data)}`);
};

setStats(null, "Empty");
