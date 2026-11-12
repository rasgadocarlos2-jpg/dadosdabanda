const API_BASE = "";
const API_KEY_STORAGE = "ddb_api_key";

export function getApiKey() {
  return localStorage.getItem(API_KEY_STORAGE) || "";
}
export function setApiKey(k) {
  localStorage.setItem(API_KEY_STORAGE, k);
}

async function apiGet(path, { auth = true } = {}) {
  const headers = {};
  const k = auth ? getApiKey() : "";
  if (k) headers["X-API-Key"] = k;
  const r = await fetch(API_BASE + path, { headers });
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      const body = await r.json();
      if (body.detail) msg = `${r.status}: ${body.detail}`;
    } catch (_) {}
    throw new Error(msg);
  }
  return r.json();
}

export const sem = (s) => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

const redesenhos = new Map();
let temporizador;
window.addEventListener("resize", () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(() => redesenhos.forEach((fn, el) => { if (el.clientWidth !== fn.largura) fn(); }), 200);
});
export function aoRedimensionar(el, fn) {
  fn.largura = el.clientWidth;
  redesenhos.set(el, fn);
}

export const api = {
  fontes: () => apiGet("/v1/fontes", { auth: false }),
  series: (fonte) => apiGet("/v1/series" + (fonte ? `?fonte=${encodeURIComponent(fonte)}` : "")),
  observacoes: (id, de, ate) => {
    const qs = new URLSearchParams();
    if (de) qs.set("de", de);
    if (ate) qs.set("ate", ate);
    const q = qs.toString();
    return apiGet(`/v1/series/${encodeURIComponent(id)}/observacoes${q ? "?" + q : ""}`);
  },
  lote: (ids, de) => {
    const qs = new URLSearchParams();
    ids.forEach(i => qs.append("series", i));
    if (de) qs.set("de", de);
    return apiGet("/v1/lote?" + qs.toString());
  },
  comparar: (ids, de, ate) => {
    const qs = new URLSearchParams();
    ids.forEach(i => qs.append("series", i));
    if (de) qs.set("de", de);
    if (ate) qs.set("ate", ate);
    return apiGet("/v1/comparar?" + qs.toString());
  },
};

export function fmt(n, decimals = 2) {
  if (n == null || Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  if (abs >= 1e9) return (n / 1e9).toFixed(decimals).replace(".", ",") + " mM";
  if (abs >= 1e6) return (n / 1e6).toFixed(decimals).replace(".", ",") + " M";
  if (abs < 0.01 && abs > 0) return n.toFixed(4).replace(".", ",");
  return n.toFixed(decimals).replace(".", ",");
}

function periodoNum(p) {
  // "2024"      → 2024
  // "2024-03"   → 2024 + 2/12 = 2024.1667
  // "2024-03-15" → aproxima mês+dia
  const [a, m = "1", d = "1"] = String(p).split("-");
  return parseInt(a, 10) + (parseInt(m, 10) - 1) / 12 + (parseInt(d, 10) - 1) / 365;
}

export function drawLineChart(svg, observacoes, { unidade = "", color = "#B80F2D", previsaoDesde = null } = {}) {
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!observacoes.length) {
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", 20); t.setAttribute("y", 40); t.setAttribute("fill", "#4B5563");
    t.textContent = "Sem dados.";
    svg.appendChild(t);
    return;
  }
  const W = Math.max(280, Math.round(svg.clientWidth || 1100));
  const estreito = W < 600, H = estreito ? 240 : 320, L = estreito ? 46 : 60, R = estreito ? 10 : 20, T = 30, B = 40;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.style.touchAction = "pan-y";

  const xs = observacoes.map(o => periodoNum(o.periodo));
  const ys = observacoes.map(o => o.valor);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const yPad = (yMax - yMin) * 0.1 || 1;
  const yLo = yMin - yPad, yHi = yMax + yPad;

  const sx = x => L + (W - L - R) * ((x - xMin) / Math.max(1e-9, xMax - xMin));
  const sy = y => T + (H - T - B) * (1 - (y - yLo) / (yHi - yLo));

  const NS = "http://www.w3.org/2000/svg";
  const el = (name, attrs = {}, text) => {
    const n = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (text != null) n.textContent = text;
    return n;
  };

  // Y grid lines + labels
  for (let i = 0; i <= 4; i++) {
    const yv = yLo + (yHi - yLo) * (i / 4);
    const y = sy(yv);
    svg.appendChild(el("line", { x1: L, y1: y, x2: W - R, y2: y, stroke: "#E3E6EA", "stroke-width": 1 }));
    svg.appendChild(el("text", { x: 8, y: y + 4, "font-size": 12, fill: "#4B5563", "font-family": "IBM Plex Sans,sans-serif" }, fmt(yv, 1)));
  }

  // X labels
  const xLabelCount = Math.min(estreito ? 3 : 6, observacoes.length);
  for (let i = 0; i < xLabelCount; i++) {
    const idx = Math.round((observacoes.length - 1) * (i / Math.max(1, xLabelCount - 1)));
    svg.appendChild(el("text", { x: Math.max(L, Math.min(W - 60, sx(xs[idx]) - 20)), y: H - 12, "font-size": 12, fill: "#4B5563", "font-family": "IBM Plex Sans,sans-serif" }, observacoes[idx].periodo));
  }

  // Linha
  const pontos = observacoes.map((o, i) => `${sx(xs[i])},${sy(o.valor)}`);
  const corte = previsaoDesde ? observacoes.findIndex(o => parseInt(o.periodo, 10) >= previsaoDesde) : -1;
  const fim = corte > 0 ? corte : pontos.length;
  svg.appendChild(el("polyline", { points: pontos.slice(0, fim).join(" "), fill: "none", stroke: color, "stroke-width": 2.5, "stroke-linejoin": "round" }));
  if (corte > 0) {
    svg.appendChild(el("polyline", { points: pontos.slice(corte - 1).join(" "), fill: "none", stroke: color, "stroke-width": 2.5, "stroke-dasharray": "7 6" }));
    svg.appendChild(el("text", { x: W - R, y: 16, "text-anchor": "end", "font-size": 12, "font-weight": 600, fill: "#7A4B00", "font-family": "IBM Plex Sans,sans-serif" }, `Tracejado: previsão do FMI desde ${previsaoDesde}`));
  }

  // Grupo interativo: crosshair, ponto, caixa com valor
  const cross = el("line", { x1: 0, y1: T, x2: 0, y2: H - B, stroke: "#9AA3AE", "stroke-width": 1, "stroke-dasharray": "4 4", opacity: 0 });
  const dot = el("circle", { r: 6, fill: color, opacity: 0 });
  const boxBg = el("rect", { rx: 6, ry: 6, fill: "#111827", opacity: 0 });
  const boxVal = el("text", { fill: "#fff", "font-size": 14, "font-weight": 700, "font-family": "IBM Plex Mono,ui-monospace,monospace", opacity: 0 });
  const boxSub = el("text", { fill: "#CBD2D9", "font-size": 11, "font-family": "IBM Plex Sans,sans-serif", opacity: 0 });
  svg.appendChild(cross); svg.appendChild(dot); svg.appendChild(boxBg); svg.appendChild(boxVal); svg.appendChild(boxSub);

  // Último ponto visível por omissão
  const last = observacoes.length - 1;
  function mostrar(i) {
    const o = observacoes[i];
    const x = sx(xs[i]), y = sy(o.valor);
    cross.setAttribute("x1", x); cross.setAttribute("x2", x); cross.setAttribute("opacity", 1);
    dot.setAttribute("cx", x); dot.setAttribute("cy", y); dot.setAttribute("opacity", 1);
    const txtVal = `${fmt(o.valor)}${unidade ? " " + unidade : ""}${previsaoDesde && parseInt(o.periodo, 10) >= previsaoDesde ? " (previsão)" : ""}`;
    boxVal.textContent = txtVal;
    boxSub.textContent = o.periodo;
    const bw = Math.max(txtVal.length * 9.2 + 20, 90), bh = 44;
    let bx = x + 12, by = y - bh - 10;
    if (bx + bw > W - R) bx = x - bw - 12;
    if (by < T) by = y + 14;
    boxBg.setAttribute("x", bx); boxBg.setAttribute("y", by);
    boxBg.setAttribute("width", bw); boxBg.setAttribute("height", bh); boxBg.setAttribute("opacity", 0.92);
    boxVal.setAttribute("x", bx + 10); boxVal.setAttribute("y", by + 22); boxVal.setAttribute("opacity", 1);
    boxSub.setAttribute("x", bx + 10); boxSub.setAttribute("y", by + 38); boxSub.setAttribute("opacity", 1);
  }
  mostrar(last);

  function indiceNoCursor(ev) {
    const rect = svg.getBoundingClientRect();
    const pt = ev.touches ? ev.touches[0] : ev;
    const cx = ((pt.clientX - rect.left) / rect.width) * W;
    const xVal = xMin + (cx - L) * (xMax - xMin) / (W - L - R);
    let best = 0, bestD = Infinity;
    for (let i = 0; i < xs.length; i++) {
      const d = Math.abs(xs[i] - xVal);
      if (d < bestD) { bestD = d; best = i; }
    }
    return best;
  }

  function onMove(ev) { mostrar(indiceNoCursor(ev)); if (ev.cancelable && ev.touches) ev.preventDefault(); }
  svg._eventos?.abort();
  svg._eventos = new AbortController();
  const signal = svg._eventos.signal;
  svg.addEventListener("mousemove", onMove, { signal });
  svg.addEventListener("touchstart", onMove, { passive: false, signal });
  svg.addEventListener("touchmove", onMove, { passive: false, signal });
  svg.addEventListener("mouseleave", () => mostrar(last), { signal });
  aoRedimensionar(svg, () => drawLineChart(svg, observacoes, { unidade, color, previsaoDesde }));
}

export function drawSparkline(svg, observacoes, { color = "#B80F2D" } = {}) {
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!observacoes?.length) return;
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a={}) => { const e = document.createElementNS(NS, n); for (const [k,v] of Object.entries(a)) e.setAttribute(k,v); return e; };
  const W = 240, H = 60, P = 4;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const xs = observacoes.map((_, i) => i);
  const ys = observacoes.map(o => o.valor);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const yRange = (yMax - yMin) || 1;
  const sx = i => P + (W - 2*P) * (i / Math.max(1, xs.length - 1));
  const sy = y => P + (H - 2*P) * (1 - (y - yMin) / yRange);
  const pts = observacoes.map((o, i) => `${sx(i)},${sy(o.valor)}`).join(" ");
  svg.appendChild(el("polyline", { points: pts, fill: "none", stroke: color, "stroke-width": 1.8, "stroke-linejoin": "round" }));
  const last = observacoes.length - 1;
  svg.appendChild(el("circle", { cx: sx(last), cy: sy(observacoes[last].valor), r: 2.5, fill: color }));
}

export function initHeader() {
  const btn = document.querySelector("[data-econ-toggle]");
  if (btn) {
    if (localStorage.getItem("ddb_econ") === "1") document.body.classList.add("econ");
    btn.addEventListener("click", () => {
      document.body.classList.toggle("econ");
      localStorage.setItem("ddb_econ", document.body.classList.contains("econ") ? "1" : "0");
    });
  }
  const keyInput = document.querySelector("[data-api-key]");
  if (keyInput) {
    keyInput.value = getApiKey();
    keyInput.addEventListener("change", () => setApiKey(keyInput.value.trim()));
  }
}
