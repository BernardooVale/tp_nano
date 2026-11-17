/* BP-FET Studio — Frontend Interativo (Editor, Animação Temporal, Osciloscópio e Raio-X) */

const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
  mode: "high", // "high" | "low"
  tuples: {},
  templates: [],
  circuit: { nodes: [], edges: [], durationNs: 25.0 },
  selectedNodeId: null,
  selectedEdgeId: null,
  compareKeys: true,
  activeKeyView: 0, // 0 ou 1
  simResult: null,
  isSimulating: false,

  // Transformação de viewport (pan/zoom)
  zoom: 1.0,
  panX: 30,
  panY: 20,

  // Estado de interação no canvas
  draggingNode: null,
  panning: null,
  wiringFrom: null,

  // Player de animação
  isPlaying: false,
  frameFloat: 0.0,
  speed: 1.0,
  dashOffset: 0.0,
  lastTickMs: 0,
  rafId: null,

  // Modal Raio-X
  xrayGateId: null,
};

// Elementos DOM principais
const el = {
  btnModeHigh: document.getElementById("btnModeHigh"),
  btnModeLow: document.getElementById("btnModeLow"),
  templateSelect: document.getElementById("templateSelect"),
  chkCompareKeys: document.getElementById("chkCompareKeys"),
  btnSimulate: document.getElementById("btnSimulate"),
  simStatusBadge: document.getElementById("simStatusBadge"),

  paletteModeTag: document.getElementById("paletteModeTag"),
  paletteContainer: document.getElementById("paletteContainer"),
  btnFitView: document.getElementById("btnFitView"),
  btnClearCanvas: document.getElementById("btnClearCanvas"),
  inspectorTypeTag: document.getElementById("inspectorTypeTag"),
  inspectorContent: document.getElementById("inspectorContent"),

  circuitCanvas: document.getElementById("circuitCanvas"),
  canvasBg: document.getElementById("canvasBg"),
  viewportLayer: document.getElementById("viewportLayer"),
  edgesLayer: document.getElementById("edgesLayer"),
  wirePreviewLayer: document.getElementById("wirePreviewLayer"),
  nodesLayer: document.getElementById("nodesLayer"),
  btnZoomIn: document.getElementById("btnZoomIn"),
  btnZoomOut: document.getElementById("btnZoomOut"),
  zoomLabel: document.getElementById("zoomLabel"),
  toastBanner: document.getElementById("toastBanner"),

  btnPlayerStart: document.getElementById("btnPlayerStart"),
  btnPlayerPlay: document.getElementById("btnPlayerPlay"),
  btnPlayerStep: document.getElementById("btnPlayerStep"),
  speedSelect: document.getElementById("speedSelect"),
  keyViewGroup: document.getElementById("keyViewGroup"),
  btnViewK0: document.getElementById("btnViewK0"),
  btnViewK1: document.getElementById("btnViewK1"),
  timeSlider: document.getElementById("timeSlider"),
  timeText: document.getElementById("timeText"),
  vectorText: document.getElementById("vectorText"),

  analysisDock: document.getElementById("analysisDock"),
  btnToggleDock: document.getElementById("btnToggleDock"),
  dockSummaryPill: document.getElementById("dockSummaryPill"),
  canvasScopeV: document.getElementById("canvasScopeV"),
  canvasScopeI: document.getElementById("canvasScopeI"),
  scopeVoltageLegend: document.getElementById("scopeVoltageLegend"),
  metricsCards: document.getElementById("metricsCards"),
  truthTableWrap: document.getElementById("truthTableWrap"),
  netlistCode: document.getElementById("netlistCode"),
  btnCopyNetlist: document.getElementById("btnCopyNetlist"),

  xrayModal: document.getElementById("xrayModal"),
  xrayTitle: document.getElementById("xrayTitle"),
  xraySubtitle: document.getElementById("xraySubtitle"),
  xraySvg: document.getElementById("xraySvg"),
  xrayTransistorTable: document.getElementById("xrayTransistorTable"),
  xrayPlayBtn: document.getElementById("xrayPlayBtn"),
  xrayKey0Btn: document.getElementById("xrayKey0Btn"),
  xrayKey1Btn: document.getElementById("xrayKey1Btn"),
  xrayTimeBadge: document.getElementById("xrayTimeBadge"),
  btnCloseXray: document.getElementById("btnCloseXray"),
};

// Paleta de cores para osciloscópio
const TRACE_COLORS = [
  "#38bdf8",
  "#22c55e",
  "#f59e0b",
  "#a855f7",
  "#f43f5e",
  "#14b8a6",
  "#eab308",
];

// ---------------------------------------------------------------------------
// Utilitários de Geometria e Cores
// ---------------------------------------------------------------------------

function svgEl(tag, attrs = {}, text = null) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    node.setAttribute(k, String(v));
  }
  if (text !== null) {
    node.textContent = text;
  }
  return node;
}

function lerpColor(c1, c2, t) {
  const clamp = Math.max(0, Math.min(1, t));
  const r = Math.round(c1[0] + (c2[0] - c1[0]) * clamp);
  const g = Math.round(c1[1] + (c2[1] - c1[1]) * clamp);
  const b = Math.round(c1[2] + (c2[2] - c1[2]) * clamp);
  return `rgb(${r}, ${g}, ${b})`;
}

function voltageToColor(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "#475569";
  const stops = [
    [-1.5, [147, 51, 234]],  // Roxo (-1.5V)
    [0.0, [71, 85, 105]],    // Azul-ardósia (0V)
    [0.4, [34, 150, 120]],   // Transição
    [0.8, [34, 197, 94]],    // Verde neon (0.8V)
    [1.1, [34, 211, 238]],   // Ciano vivo (1.1V)
    [1.5, [245, 158, 11]],   // Âmbar brilhante (1.5V+)
  ];
  if (v <= stops[0][0]) return `rgb(${stops[0][1].join(",")})`;
  for (let i = 0; i < stops.length - 1; i++) {
    const [v0, c0] = stops[i];
    const [v1, c1] = stops[i + 1];
    if (v >= v0 && v <= v1) {
      return lerpColor(c0, c1, (v - v0) / (v1 - v0));
    }
  }
  return `rgb(${stops[stops.length - 1][1].join(",")})`;
}

function showToast(msg, durationMs = 4500) {
  el.toastBanner.textContent = msg;
  el.toastBanner.classList.remove("hidden");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    el.toastBanner.classList.add("hidden");
  }, durationMs);
}

function uid(prefix = "n") {
  return `${prefix}_${Math.random().toString(36).slice(2, 8)}`;
}

// ---------------------------------------------------------------------------
// Definição de Caixas e Pinos dos Componentes
// ---------------------------------------------------------------------------

function getTupleDef(tupleId) {
  return state.tuples[tupleId] || state.tuples.NAND_NOR || {
    id: "NAND_NOR",
    name: "(NAND, NOR)",
    inputs: ["A", "B"],
    outputs: ["Y"],
    core_transistors: 4,
    total_transistors: 4,
    sum_w: 6.0,
    vdd: 0.8,
    key0_fn: "NAND",
    key1_fn: "NOR",
  };
}

function getNodeBox(node) {
  switch (node.type) {
    case "INPUT":
    case "KEY":
    case "OUTPUT":
      return { w: 112, h: 60 };
    case "POLY_GATE": {
      const tdef = getTupleDef(node.props?.tupleId || "NAND_NOR");
      return { w: 214, h: tdef.inputs.length >= 3 ? 132 : 114 };
    }
    case "ARI_FET":
      return { w: 126, h: 102 };
    case "VDC":
    case "VPWL":
      return { w: 104, h: 62 };
    case "CAP":
    case "RES":
      return { w: 86, h: 66 };
    case "GND":
      return { w: 66, h: 46 };
    case "PROBE":
      return { w: 94, h: 48 };
    default:
      return { w: 100, h: 60 };
  }
}

function getNodePorts(node) {
  const { w, h } = getNodeBox(node);
  switch (node.type) {
    case "INPUT":
    case "KEY":
      return [{ name: "out", dir: "out", lx: w, ly: h / 2, label: "Out" }];
    case "OUTPUT":
      return [{ name: "in", dir: "in", lx: 0, ly: h / 2, label: "In" }];
    case "POLY_GATE": {
      const tdef = getTupleDef(node.props?.tupleId || "NAND_NOR");
      const ports = [];
      const nIn = tdef.inputs.length;
      const topY = 38;
      const span = h - 68;
      tdef.inputs.forEach((inp, idx) => {
        const ly = nIn === 1 ? topY + span / 2 : topY + (idx * span) / (nIn - 1);
        ports.push({ name: inp, dir: "in", lx: 0, ly, label: inp });
      });
      ports.push({ name: "K", dir: "in", lx: 28, ly: h, label: "Key" });
      ports.push({ name: "Y", dir: "out", lx: w, ly: h / 2 - 4, label: "Y" });
      return ports;
    }
    case "ARI_FET":
      return [
        { name: "d", dir: "bi", lx: w / 2, ly: 0, label: "d" },
        { name: "s", dir: "bi", lx: w / 2, ly: h, label: "s" },
        { name: "g", dir: "bi", lx: 0, ly: 36, label: "g" },
        { name: "g1", dir: "bi", lx: 0, ly: 72, label: "g1" },
        { name: "g2", dir: "bi", lx: w, ly: 52, label: "g2" },
      ];
    case "VDC":
    case "VPWL":
      return [
        { name: "pos", dir: "bi", lx: w, ly: h / 2, label: "+" },
        { name: "neg", dir: "bi", lx: 0, ly: h / 2, label: "−" },
      ];
    case "CAP":
    case "RES":
      return [
        { name: "a", dir: "bi", lx: w / 2, ly: 0, label: "a" },
        { name: "b", dir: "bi", lx: w / 2, ly: h, label: "b" },
      ];
    case "GND":
      return [{ name: "gnd", dir: "bi", lx: w / 2, ly: 0, label: "0V" }];
    case "PROBE":
      return [{ name: "in", dir: "bi", lx: 0, ly: h / 2, label: "Probe" }];
    default:
      return [];
  }
}

function getPortWorldCoords(node, portName) {
  const port = getNodePorts(node).find((p) => p.name === portName);
  if (!port) return { x: node.x, y: node.y };
  return { x: node.x + port.lx, y: node.y + port.ly };
}

function clientToWorld(clientX, clientY) {
  const rect = el.circuitCanvas.getBoundingClientRect();
  return {
    x: (clientX - rect.left - state.panX) / state.zoom,
    y: (clientY - rect.top - state.panY) / state.zoom,
  };
}

function applyViewportTransform() {
  el.viewportLayer.setAttribute("transform", `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);
  el.zoomLabel.textContent = `${Math.round(state.zoom * 100)}%`;
}

function fitView() {
  if (!state.circuit.nodes.length) {
    state.zoom = 1.0;
    state.panX = 40;
    state.panY = 30;
    applyViewportTransform();
    return;
  }
  const rect = el.circuitCanvas.getBoundingClientRect();
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of state.circuit.nodes) {
    const box = getNodeBox(n);
    minX = Math.min(minX, n.x);
    minY = Math.min(minY, n.y);
    maxX = Math.max(maxX, n.x + box.w);
    maxY = Math.max(maxY, n.y + box.h);
  }
  const pad = 60;
  const cw = Math.max(rect.width - pad * 2, 200);
  const ch = Math.max(rect.height - pad * 2, 150);
  const bw = Math.max(maxX - minX, 100);
  const bh = Math.max(maxY - minY, 100);
  state.zoom = Math.max(0.45, Math.min(1.25, Math.min(cw / bw, ch / bh)));
  state.panX = (rect.width - bw * state.zoom) / 2 - minX * state.zoom;
  state.panY = (rect.height - bh * state.zoom) / 2 - minY * state.zoom;
  applyViewportTransform();
}

// ---------------------------------------------------------------------------
// Paleta e Inspetor de Propriedades
// ---------------------------------------------------------------------------

function renderPalette() {
  el.paletteModeTag.textContent = state.mode === "high" ? "Alto Nível" : "Baixo Nível";
  const items = state.mode === "high"
    ? [
        { type: "POLY_GATE", title: "Porta Lógica Polimórfica", sub: "Configurável entre as 7 tuplas BP-FET" },
        { type: "INPUT", title: "Entrada Digital (A, B, C...)", sub: "Fonte PWL automática ou customizada" },
        { type: "KEY", title: "Chave Polimórfica (Key)", sub: "Alterna polaridade Key=0 ↔ Key=1" },
        { type: "OUTPUT", title: "Saída / Ponta de Prova", sub: "Extrai tabela-verdade e formas de onda" },
      ]
    : [
        { type: "ARI_FET", title: "Transistor BP SB-FET (ARI)", sub: "5 terminais: d, g, s, g1, g2" },
        { type: "VDC", title: "Fonte DC / Polaridade", sub: "Suporta tensão fixa ou dependente de Key" },
        { type: "VPWL", title: "Fonte de Pulso (VPWL)", sub: "Onda temporal PWL em nanossegundos" },
        { type: "CAP", title: "Capacitor (Cload)", sub: "Carga capacitiva ou nó parasita" },
        { type: "RES", title: "Resistor (RES)", sub: "Elemento resistivo" },
        { type: "GND", title: "Terra (GND 0V)", sub: "Referência 0 V do circuito" },
        { type: "PROBE", title: "Ponta de Prova (Probe)", sub: "Mede V(t) no osciloscópio" },
      ];

  el.paletteContainer.innerHTML = "";
  for (const item of items) {
    const btn = document.createElement("button");
    btn.className = "palette-btn";
    btn.innerHTML = `
      <div>
        <span class="p-title">${item.title}</span>
        <span class="p-sub">${item.sub}</span>
      </div>
      <span class="p-plus">+</span>
    `;
    btn.addEventListener("click", () => addComponentToCenter(item.type));
    el.paletteContainer.appendChild(btn);
  }
}

function addComponentToCenter(type) {
  const rect = el.circuitCanvas.getBoundingClientRect();
  const center = clientToWorld(rect.left + rect.width / 2, rect.top + rect.height / 2);
  const jitter = ((state.circuit.nodes.length % 5) - 2) * 22;

  const countOfType = state.circuit.nodes.filter((n) => n.type === type).length + 1;
  const defaultLabels = {
    INPUT: String.fromCharCode(64 + Math.min(countOfType, 26)),
    KEY: `K${countOfType - 1}`,
    POLY_GATE: `Porta ${countOfType}`,
    OUTPUT: `Out${countOfType}`,
    ARI_FET: `X${countOfType}`,
    VDC: `V${countOfType}`,
    VPWL: `Vin${countOfType}`,
    CAP: `C${countOfType}`,
    RES: `R${countOfType}`,
    GND: "GND",
    PROBE: `Out${countOfType}`,
  };

  const defaultProps = {
    INPUT: { pattern: "auto" },
    KEY: { value: 0 },
    POLY_GATE: { tupleId: "NAND_NOR", localKey: 0 },
    OUTPUT: {},
    ARI_FET: { w: 1.0 },
    VDC: { voltage: 0.8, keyDependent: false, vKey0: 0.8, vKey1: 0.0, isSupply: false },
    VPWL: { pwl: "0n 0 9.9n 0 10n 0.8 19.9n 0.8 20n 0 25n 0" },
    CAP: { cap: "0.3f" },
    RES: { res: "10k" },
    GND: {},
    PROBE: {},
  };

  const node = {
    id: uid(type.toLowerCase()),
    type,
    label: defaultLabels[type] || type,
    x: Math.round(center.x - 60 + jitter),
    y: Math.round(center.y - 40 + jitter),
    props: { ...(defaultProps[type] || {}) },
  };
  state.circuit.nodes.push(node);
  state.selectedNodeId = node.id;
  state.selectedEdgeId = null;
  renderCircuitGraph();
  renderInspector();
}

function renderInspector() {
  const node = state.circuit.nodes.find((n) => n.id === state.selectedNodeId);
  if (!node) {
    if (state.selectedEdgeId) {
      el.inspectorTypeTag.textContent = "Fio";
      el.inspectorContent.innerHTML = `
        <p class="empty-hint">Fio selecionado no esquemático.</p>
        <button id="btnDeleteEdge" class="btn-danger">Remover Fio Selecionado</button>
      `;
      document.getElementById("btnDeleteEdge").addEventListener("click", () => {
        state.circuit.edges = state.circuit.edges.filter((e) => e.id !== state.selectedEdgeId);
        state.selectedEdgeId = null;
        renderCircuitGraph();
        renderInspector();
      });
      return;
    }

    el.inspectorTypeTag.textContent = "Nenhum";
    el.inspectorContent.innerHTML = `
      <p class="empty-hint">
        Clique em um bloco no circuito para configurar sua tupla polimórfica, entradas ou parâmetros.<br/><br/>
        <strong>Fiação:</strong> clique em um pino e depois no pino de destino (ou arraste de um pino ao outro). Clique em um fio para removê-lo.
      </p>
    `;
    return;
  }

  el.inspectorTypeTag.textContent = node.type;
  const wrap = document.createElement("div");
  wrap.className = "inspector-body";

  // Campo Nome / Rótulo comum
  const lblGroup = document.createElement("div");
  lblGroup.className = "field-group";
  lblGroup.innerHTML = `<label>Rótulo do Componente</label><input type="text" id="inpLabel" value="${node.label || ""}" />`;
  wrap.appendChild(lblGroup);

  if (node.type === "POLY_GATE") {
    const tupleId = node.props?.tupleId || "NAND_NOR";
    const tdef = getTupleDef(tupleId);
    const localKey = Number(node.props?.localKey ?? 0);

    const tupleGroup = document.createElement("div");
    tupleGroup.className = "field-group";
    const optsHtml = Object.values(state.tuples)
      .map((t) => `<option value="${t.id}" ${t.id === tupleId ? "selected" : ""}>${t.name} — ${t.core_transistors}T (${t.vdd}V)</option>`)
      .join("");
    tupleGroup.innerHTML = `<label>Tupla Polimórfica Configurável</label><select id="inpTuple">${optsHtml}</select>`;
    wrap.appendChild(tupleGroup);

    const keyGroup = document.createElement("div");
    keyGroup.className = "field-group";
    keyGroup.innerHTML = `
      <label>Chave Local (quando pino Key está livre)</label>
      <select id="inpLocalKey">
        <option value="0" ${localKey === 0 ? "selected" : ""}>Key = 0 → ${tdef.key0_fn}</option>
        <option value="1" ${localKey === 1 ? "selected" : ""}>Key = 1 → ${tdef.key1_fn}</option>
      </select>
    `;
    wrap.appendChild(keyGroup);

    const infoBox = document.createElement("div");
    infoBox.className = "tuple-info-box";
    infoBox.innerHTML = `
      <strong>${tdef.category}</strong> · ${tdef.core_transistors}T núcleo (${tdef.total_transistors}T total) · ΣW = ${tdef.sum_w} µm<br/>
      <strong>Key=0:</strong> ${tdef.key0_fn} &nbsp;|&nbsp; <strong>Key=1:</strong> ${tdef.key1_fn}<br/>
      <span>${tdef.description}</span>
    `;
    wrap.appendChild(infoBox);

    const xrayBtn = document.createElement("button");
    xrayBtn.className = "xray-cta-btn";
    xrayBtn.textContent = "🔍 Abrir Raio-X (Ver Transistores ARI Internos)";
    xrayBtn.addEventListener("click", () => openXrayModal(node.id));
    wrap.appendChild(xrayBtn);
  } else if (node.type === "INPUT") {
    const patGroup = document.createElement("div");
    patGroup.className = "field-group";
    patGroup.innerHTML = `
      <label>Padrão de Bits ("auto" ou ex: "0110")</label>
      <input type="text" id="inpPattern" value="${node.props?.pattern || "auto"}" />
    `;
    wrap.appendChild(patGroup);
  } else if (node.type === "KEY") {
    const val = Number(node.props?.value ?? 0);
    const kGroup = document.createElement("div");
    kGroup.className = "field-group";
    kGroup.innerHTML = `
      <label>Estado da Chave (Key)</label>
      <select id="inpKeyVal">
        <option value="0" ${val === 0 ? "selected" : ""}>0 (Modo Nominal / Key=0)</option>
        <option value="1" ${val === 1 ? "selected" : ""}>1 (Modo Alternativo / Key=1)</option>
      </select>
    `;
    wrap.appendChild(kGroup);
  } else if (node.type === "ARI_FET") {
    const wGroup = document.createElement("div");
    wGroup.className = "field-group";
    wGroup.innerHTML = `
      <label>Largura do Canal W (µm)</label>
      <input type="number" step="0.5" min="0.5" max="20" id="inpWidth" value="${node.props?.w ?? 1.0}" />
    `;
    wrap.appendChild(wGroup);
  } else if (node.type === "VDC") {
    const props = node.props || {};
    const vGroup = document.createElement("div");
    vGroup.className = "field-group";
    vGroup.innerHTML = `<label>Tensão Nominal (V)</label><input type="number" step="0.1" id="inpVdc" value="${props.voltage ?? 0.8}" />`;
    wrap.appendChild(vGroup);

    const chkKd = document.createElement("label");
    chkKd.className = "checkbox-row";
    chkKd.innerHTML = `<input type="checkbox" id="inpKeyDep" ${props.keyDependent ? "checked" : ""} /> <span>Varia entre Key=0 e Key=1</span>`;
    wrap.appendChild(chkKd);

    if (props.keyDependent) {
      const row = document.createElement("div");
      row.className = "field-row";
      row.innerHTML = `
        <div class="field-group"><label>V (Key=0)</label><input type="number" step="0.1" id="inpVk0" value="${props.vKey0 ?? props.voltage ?? 0.8}" /></div>
        <div class="field-group"><label>V (Key=1)</label><input type="number" step="0.1" id="inpVk1" value="${props.vKey1 ?? 0.0}" /></div>
      `;
      wrap.appendChild(row);
    }

    const chkSup = document.createElement("label");
    chkSup.className = "checkbox-row";
    chkSup.innerHTML = `<input type="checkbox" id="inpIsSupply" ${props.isSupply ? "checked" : ""} /> <span>Medir corrente de alimentação (I_VDD)</span>`;
    wrap.appendChild(chkSup);
  } else if (node.type === "VPWL") {
    const pGroup = document.createElement("div");
    pGroup.className = "field-group";
    pGroup.innerHTML = `<label>Pontos PWL (tempo tensão ...)</label><input type="text" id="inpPwl" value="${node.props?.pwl || ""}" />`;
    wrap.appendChild(pGroup);
  } else if (node.type === "CAP") {
    const cGroup = document.createElement("div");
    cGroup.className = "field-group";
    cGroup.innerHTML = `<label>Capacitância (ex: 0.3f, 1f, 10p)</label><input type="text" id="inpCap" value="${node.props?.cap || "0.3f"}" />`;
    wrap.appendChild(cGroup);
  } else if (node.type === "RES") {
    const rGroup = document.createElement("div");
    rGroup.className = "field-group";
    rGroup.innerHTML = `<label>Resistência (ex: 10k, 1M)</label><input type="text" id="inpRes" value="${node.props?.res || "10k"}" />`;
    wrap.appendChild(rGroup);
  }

  const delBtn = document.createElement("button");
  delBtn.className = "btn-danger";
  delBtn.textContent = "Remover Componente";
  delBtn.addEventListener("click", () => deleteSelected());
  wrap.appendChild(delBtn);

  el.inspectorContent.innerHTML = "";
  el.inspectorContent.appendChild(wrap);

  // Listeners dos campos
  document.getElementById("inpLabel")?.addEventListener("input", (e) => {
    node.label = e.target.value;
    renderCircuitGraph();
  });

  document.getElementById("inpTuple")?.addEventListener("change", (e) => {
    node.props.tupleId = e.target.value;
    const allowed = new Set([...getTupleDef(node.props.tupleId).inputs, "K", "Y"]);
    state.circuit.edges = state.circuit.edges.filter(
      (ed) => (ed.to !== node.id || allowed.has(ed.toPort)) && (ed.from !== node.id || allowed.has(ed.fromPort))
    );
    renderCircuitGraph();
    renderInspector();
  });

  document.getElementById("inpLocalKey")?.addEventListener("change", (e) => {
    node.props.localKey = Number(e.target.value);
    renderCircuitGraph();
  });

  document.getElementById("inpPattern")?.addEventListener("input", (e) => {
    node.props.pattern = e.target.value;
  });

  document.getElementById("inpKeyVal")?.addEventListener("change", (e) => {
    node.props.value = Number(e.target.value);
    if (state.simResult && state.compareKeys) {
      setActiveKeyView(node.props.value);
    }
    renderCircuitGraph();
  });

  document.getElementById("inpWidth")?.addEventListener("input", (e) => {
    node.props.w = parseFloat(e.target.value) || 1.0;
    renderCircuitGraph();
  });

  document.getElementById("inpVdc")?.addEventListener("input", (e) => {
    node.props.voltage = parseFloat(e.target.value) || 0.0;
    if (!node.props.keyDependent) node.props.vKey0 = node.props.voltage;
    renderCircuitGraph();
  });

  document.getElementById("inpKeyDep")?.addEventListener("change", (e) => {
    node.props.keyDependent = e.target.checked;
    if (node.props.keyDependent && node.props.vKey0 === undefined) {
      node.props.vKey0 = node.props.voltage ?? 0.8;
      node.props.vKey1 = 0.0;
    }
    renderInspector();
    renderCircuitGraph();
  });

  document.getElementById("inpVk0")?.addEventListener("input", (e) => {
    node.props.vKey0 = parseFloat(e.target.value) || 0.0;
    node.props.voltage = node.props.vKey0;
    renderCircuitGraph();
  });

  document.getElementById("inpVk1")?.addEventListener("input", (e) => {
    node.props.vKey1 = parseFloat(e.target.value) || 0.0;
    renderCircuitGraph();
  });

  document.getElementById("inpIsSupply")?.addEventListener("change", (e) => {
    node.props.isSupply = e.target.checked;
  });

  document.getElementById("inpPwl")?.addEventListener("input", (e) => {
    node.props.pwl = e.target.value;
  });

  document.getElementById("inpCap")?.addEventListener("input", (e) => {
    node.props.cap = e.target.value;
    renderCircuitGraph();
  });

  document.getElementById("inpRes")?.addEventListener("input", (e) => {
    node.props.res = e.target.value;
    renderCircuitGraph();
  });
}

function deleteSelected() {
  if (state.selectedNodeId) {
    const id = state.selectedNodeId;
    state.circuit.nodes = state.circuit.nodes.filter((n) => n.id !== id);
    state.circuit.edges = state.circuit.edges.filter((e) => e.from !== id && e.to !== id);
    state.selectedNodeId = null;
  } else if (state.selectedEdgeId) {
    const eid = state.selectedEdgeId;
    state.circuit.edges = state.circuit.edges.filter((e) => e.id !== eid);
    state.selectedEdgeId = null;
  }
  renderCircuitGraph();
  renderInspector();
}

// ---------------------------------------------------------------------------
// Renderização do Grafo SVG (com cache de elementos para 60fps na animação)
// ---------------------------------------------------------------------------

const animRefs = {
  wires: [], // { edge, baseEl, flowEl }
  nodes: {}, // nodeId -> refs
};

function bezierPath(x1, y1, x2, y2) {
  const dx = Math.max(Math.abs(x2 - x1) * 0.48, 36);
  const c1x = x1 + (x2 >= x1 ? dx : -dx);
  const c2x = x2 - (x2 >= x1 ? dx : -dx);
  return `M ${x1} ${y1} C ${c1x} ${y1}, ${c2x} ${y2}, ${x2} ${y2}`;
}

function renderCircuitGraph() {
  el.edgesLayer.innerHTML = "";
  el.nodesLayer.innerHTML = "";
  animRefs.wires = [];
  animRefs.nodes = {};

  const nodeMap = Object.fromEntries(state.circuit.nodes.map((n) => [n.id, n]));

  // 1) Desenha fios
  for (const edge of state.circuit.edges) {
    const src = nodeMap[edge.from];
    const dst = nodeMap[edge.to];
    if (!src || !dst) continue;
    const p1 = getPortWorldCoords(src, edge.fromPort);
    const p2 = getPortWorldCoords(dst, edge.toPort);
    const d = bezierPath(p1.x, p1.y, p2.x, p2.y);

    const g = svgEl("g");
    const hit = svgEl("path", { d, class: "wire-hit" });
    const base = svgEl("path", {
      d,
      class: `wire-base ${state.selectedEdgeId === edge.id ? "wire-selected" : ""}`,
      stroke: "#475569",
    });
    const flow = svgEl("path", {
      d,
      class: "wire-flow",
      opacity: "0",
    });

    hit.addEventListener("click", (ev) => {
      ev.stopPropagation();
      state.selectedEdgeId = edge.id;
      state.selectedNodeId = null;
      renderCircuitGraph();
      renderInspector();
    });

    g.appendChild(base);
    g.appendChild(flow);
    g.appendChild(hit);
    el.edgesLayer.appendChild(g);
    animRefs.wires.push({ edge, baseEl: base, flowEl: flow });
  }

  // 2) Desenha nós
  for (const node of state.circuit.nodes) {
    const { w, h } = getNodeBox(node);
    const isSel = state.selectedNodeId === node.id;
    const g = svgEl("g", {
      class: `node-group ${isSel ? "selected" : ""}`,
      transform: `translate(${node.x}, ${node.y})`,
    });

    const card = svgEl("rect", { class: "node-card", width: w, height: h });
    g.appendChild(card);

    // Conteúdo visual específico de cada tipo
    const refs = { type: node.type, node };

    if (node.type === "POLY_GATE") {
      const tdef = getTupleDef(node.props?.tupleId || "NAND_NOR");
      const hdr = svgEl("rect", { class: "node-header-bar", x: 1, y: 1, width: w - 2, height: 24, rx: 9 });
      g.appendChild(hdr);
      g.appendChild(svgEl("text", { x: 10, y: 17, fill: "#f1f5f9", "font-size": 11, "font-weight": 700 }, node.label || "Porta"));

      // Botão Raio-X inline no bloco
      const xrayBtn = svgEl("g", { class: "xray-mini-btn", transform: `translate(${w - 64}, 4)` });
      xrayBtn.appendChild(svgEl("rect", { width: 56, height: 17, rx: 5, fill: "rgba(168,85,247,0.22)", stroke: "rgba(168,85,247,0.55)", "stroke-width": 1 }));
      xrayBtn.appendChild(svgEl("text", { x: 28, y: 12, "text-anchor": "middle", fill: "#e9d5ff", "font-size": 9.5, "font-weight": 700 }, "🔍 Raio-X"));
      xrayBtn.addEventListener("mousedown", (ev) => ev.stopPropagation());
      xrayBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        openXrayModal(node.id);
      });
      g.appendChild(xrayBtn);

      g.appendChild(svgEl("text", { x: w / 2, y: 42, "text-anchor": "middle", fill: "#94a3b8", "font-size": 10.5, "font-weight": 600 }, `${tdef.name} · ${tdef.core_transistors}T`));

      const modePill = svgEl("rect", { x: 24, y: 50, width: w - 48, height: 22, rx: 6, fill: "rgba(34,211,238,0.14)", stroke: "rgba(34,211,238,0.4)" });
      const modeTxt = svgEl("text", { x: w / 2, y: 65, "text-anchor": "middle", fill: "#67e8f9", "font-size": 11, "font-weight": 800 }, `${tdef.key0_fn}`);
      g.appendChild(modePill);
      g.appendChild(modeTxt);

      const vTxt = svgEl("text", { x: w - 12, y: h - 10, "text-anchor": "end", fill: "#cbd5e1", "font-size": 10, "font-family": "monospace" }, "— V");
      const iTxt = svgEl("text", { x: 70, y: h - 10, "text-anchor": "start", fill: "#94a3b8", "font-size": 10, "font-family": "monospace" }, "— µA");
      g.appendChild(vTxt);
      g.appendChild(iTxt);

      refs.modePill = modePill;
      refs.modeTxt = modeTxt;
      refs.vTxt = vTxt;
      refs.iTxt = iTxt;
      refs.tdef = tdef;
    } else if (node.type === "INPUT" || node.type === "OUTPUT" || node.type === "PROBE") {
      const badgeColor = node.type === "INPUT" ? "#38bdf8" : "#22c55e";
      g.appendChild(svgEl("rect", { x: 1, y: 1, width: w - 2, height: 20, rx: 8, fill: "#1b2840" }));
      g.appendChild(svgEl("text", { x: 10, y: 15, fill: badgeColor, "font-size": 10.5, "font-weight": 700 }, node.type === "INPUT" ? "ENTRADA" : "SAÍDA"));
      g.appendChild(svgEl("text", { x: w / 2, y: 36, "text-anchor": "middle", fill: "#f1f5f9", "font-size": 13, "font-weight": 700 }, node.label || node.type));
      const vTxt = svgEl("text", { x: w / 2, y: 52, "text-anchor": "middle", fill: "#94a3b8", "font-size": 10.5, "font-family": "monospace" }, "0.00 V");
      if (node.type === "PROBE") {
        vTxt.setAttribute("y", 40);
      }
      g.appendChild(vTxt);
      refs.vTxt = vTxt;
    } else if (node.type === "KEY") {
      const keyVal = Number(node.props?.value ?? 0);
      g.appendChild(svgEl("rect", { x: 1, y: 1, width: w - 2, height: 20, rx: 8, fill: "#1b2840" }));
      g.appendChild(svgEl("text", { x: 10, y: 15, fill: "#f59e0b", "font-size": 10.5, "font-weight": 700 }, "CHAVE KEY"));
      g.appendChild(svgEl("text", { x: 12, y: 42, fill: "#f1f5f9", "font-size": 12, "font-weight": 700 }, node.label || "Key"));

      const kBtn = svgEl("g", { class: "key-toggle-btn", transform: `translate(${w - 46}, 27)` });
      const kRect = svgEl("rect", { width: 36, height: 22, rx: 6, fill: keyVal ? "rgba(244,63,94,0.25)" : "rgba(34,211,238,0.2)", stroke: keyVal ? "#f43f5e" : "#22d3ee" });
      const kTxt = svgEl("text", { x: 18, y: 15, "text-anchor": "middle", fill: "#f8fafc", "font-size": 11, "font-weight": 800 }, `K=${keyVal}`);
      kBtn.appendChild(kRect);
      kBtn.appendChild(kTxt);
      kBtn.addEventListener("mousedown", (ev) => ev.stopPropagation());
      kBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        node.props.value = Number(node.props.value ?? 0) === 0 ? 1 : 0;
        if (state.simResult && state.compareKeys) {
          setActiveKeyView(node.props.value);
        }
        renderCircuitGraph();
        renderInspector();
      });
      g.appendChild(kBtn);
      refs.kRect = kRect;
      refs.kTxt = kTxt;
    } else if (node.type === "ARI_FET") {
      g.appendChild(svgEl("text", { x: w / 2, y: 18, "text-anchor": "middle", fill: "#e2e8f0", "font-size": 11, "font-weight": 700 }, `${node.label || "ARI"} (W=${node.props?.w ?? 1})`));
      // Símbolo do transistor BP SB-FET
      const chBg = svgEl("line", { x1: 63, y1: 24, x2: 63, y2: 80, stroke: "#334155", "stroke-width": 5, "stroke-linecap": "round" });
      const chGlow = svgEl("line", { x1: 63, y1: 24, x2: 63, y2: 80, stroke: "#22d3ee", "stroke-width": 4, "stroke-linecap": "round", opacity: 0.1 });
      const gateBar = svgEl("line", { x1: 45, y1: 30, x2: 45, y2: 74, stroke: "#94a3b8", "stroke-width": 2.5 });
      g.appendChild(chBg);
      g.appendChild(chGlow);
      g.appendChild(gateBar);
      g.appendChild(svgEl("line", { x1: 0, y1: 36, x2: 45, y2: 36, stroke: "#64748b", "stroke-width": 1.6 }));
      g.appendChild(svgEl("line", { x1: 0, y1: 72, x2: 45, y2: 72, stroke: "#64748b", "stroke-width": 1.6 }));
      g.appendChild(svgEl("line", { x1: 63, y1: 52, x2: w, y2: 52, stroke: "#64748b", "stroke-width": 1.6 }));

      const polBadge = svgEl("rect", { x: 70, y: 26, width: 46, height: 17, rx: 4, fill: "rgba(34,211,238,0.16)", stroke: "rgba(34,211,238,0.45)" });
      const polTxt = svgEl("text", { x: 93, y: 38, "text-anchor": "middle", fill: "#67e8f9", "font-size": 9.5, "font-weight": 800 }, "ARI");
      g.appendChild(polBadge);
      g.appendChild(polTxt);

      refs.chGlow = chGlow;
      refs.polBadge = polBadge;
      refs.polTxt = polTxt;
    } else if (node.type === "VDC" || node.type === "VPWL") {
      g.appendChild(svgEl("text", { x: w / 2, y: 18, "text-anchor": "middle", fill: "#f59e0b", "font-size": 10.5, "font-weight": 700 }, node.label || node.type));
      const subTxt = node.type === "VDC"
        ? (node.props?.keyDependent ? `K0:${node.props.vKey0} K1:${node.props.vKey1}` : `${node.props?.voltage ?? 0} V`)
        : "PWL";
      const vTxt = svgEl("text", { x: w / 2, y: 42, "text-anchor": "middle", fill: "#e2e8f0", "font-size": 11, "font-family": "monospace" }, subTxt);
      g.appendChild(vTxt);
      refs.vTxt = vTxt;
    } else if (node.type === "CAP") {
      g.appendChild(svgEl("line", { x1: 28, y1: 28, x2: 58, y2: 28, stroke: "#94a3b8", "stroke-width": 2.5 }));
      g.appendChild(svgEl("line", { x1: 28, y1: 38, x2: 58, y2: 38, stroke: "#94a3b8", "stroke-width": 2.5 }));
      g.appendChild(svgEl("line", { x1: w / 2, y1: 0, x2: w / 2, y2: 28, stroke: "#64748b", "stroke-width": 1.6 }));
      g.appendChild(svgEl("line", { x1: w / 2, y1: 38, x2: w / 2, y2: h, stroke: "#64748b", "stroke-width": 1.6 }));
      g.appendChild(svgEl("text", { x: w / 2, y: 55, "text-anchor": "middle", fill: "#cbd5e1", "font-size": 10 }, `${node.label} ${node.props?.cap || "0.3f"}`));
    } else if (node.type === "RES") {
      g.appendChild(svgEl("polyline", { points: "43,0 43,16 33,22 53,28 33,34 53,40 43,46 43,66", fill: "none", stroke: "#94a3b8", "stroke-width": 2 }));
      g.appendChild(svgEl("text", { x: w / 2, y: 58, "text-anchor": "middle", fill: "#cbd5e1", "font-size": 10 }, `${node.label} ${node.props?.res || "10k"}`));
    } else if (node.type === "GND") {
      g.appendChild(svgEl("line", { x1: w / 2, y1: 0, x2: w / 2, y2: 18, stroke: "#94a3b8", "stroke-width": 2 }));
      g.appendChild(svgEl("line", { x1: 16, y1: 18, x2: w - 16, y2: 18, stroke: "#94a3b8", "stroke-width": 2.5 }));
      g.appendChild(svgEl("line", { x1: 23, y1: 25, x2: w - 23, y2: 25, stroke: "#94a3b8", "stroke-width": 2 }));
      g.appendChild(svgEl("line", { x1: 29, y1: 32, x2: w - 29, y2: 32, stroke: "#94a3b8", "stroke-width": 2 }));
      g.appendChild(svgEl("text", { x: w / 2, y: 43, "text-anchor": "middle", fill: "#94a3b8", "font-size": 9 }, "GND (0V)"));
    }

    // Pinos do componente
    const ports = getNodePorts(node);
    for (const p of ports) {
      const isActivePin = state.wiringFrom && state.wiringFrom.nodeId === node.id && state.wiringFrom.portName === p.name;
      const dotColor = p.dir === "out" ? "#22d3ee" : p.name === "K" ? "#f59e0b" : "#94a3b8";
      const dot = svgEl("circle", {
        cx: p.lx,
        cy: p.ly,
        r: 5.5,
        fill: dotColor,
        stroke: "#0b111b",
        "stroke-width": 1.6,
        class: `port-dot ${isActivePin ? "active-pin" : ""}`,
      });

      // Rótulo do pino
      let tx = p.lx + 9;
      let ty = p.ly + 3.5;
      let anchor = "start";
      if (p.lx >= w - 1) {
        tx = p.lx - 9;
        anchor = "end";
      } else if (p.ly === 0) {
        tx = p.lx + 8;
        ty = 13;
      } else if (p.ly >= h - 1) {
        tx = p.lx + 8;
        ty = h - 7;
      }
      if (node.type === "POLY_GATE" || node.type === "ARI_FET") {
        g.appendChild(svgEl("text", { x: tx, y: ty, "text-anchor": anchor, fill: "#94a3b8", "font-size": 9.5, "font-weight": 600, "pointer-events": "none" }, p.label));
      }

      dot.addEventListener("mousedown", (ev) => {
        ev.stopPropagation();
        handlePinMouseDown(node, p, ev);
      });
      dot.addEventListener("mouseup", (ev) => {
        ev.stopPropagation();
        handlePinMouseUp(node, p, ev);
      });
      g.appendChild(dot);
    }

    // Arrastar nó
    g.addEventListener("mousedown", (ev) => {
      if (ev.button !== 0) return;
      ev.stopPropagation();
      state.selectedNodeId = node.id;
      state.selectedEdgeId = null;
      const pt = clientToWorld(ev.clientX, ev.clientY);
      state.draggingNode = { node, offsetX: pt.x - node.x, offsetY: pt.y - node.y };
      renderCircuitGraph();
      renderInspector();
    });

    g.addEventListener("dblclick", (ev) => {
      ev.stopPropagation();
      if (node.type === "POLY_GATE") openXrayModal(node.id);
    });

    el.nodesLayer.appendChild(g);
    animRefs.nodes[node.id] = refs;
  }

  updateAnimationFrame();
}

// ---------------------------------------------------------------------------
// Fiação Interativa (Click-to-Click e Drag-and-Drop entre Pinos)
// ---------------------------------------------------------------------------

function handlePinMouseDown(node, port, ev) {
  const world = getPortWorldCoords(node, port.name);
  if (state.wiringFrom) {
    // Completa conexão se clicou em um pino diferente
    if (state.wiringFrom.nodeId !== node.id || state.wiringFrom.portName !== port.name) {
      connectPorts(state.wiringFrom.nodeId, state.wiringFrom.portName, node.id, port.name);
      cancelWiring();
      return;
    }
    cancelWiring();
    return;
  }
  state.wiringFrom = {
    nodeId: node.id,
    portName: port.name,
    startX: world.x,
    startY: world.y,
    startClientX: ev.clientX,
    startClientY: ev.clientY,
  };
  renderCircuitGraph();
}

function handlePinMouseUp(node, port, ev) {
  if (!state.wiringFrom) return;
  const dist = Math.hypot(ev.clientX - state.wiringFrom.startClientX, ev.clientY - state.wiringFrom.startClientY);
  if (dist > 6 && (state.wiringFrom.nodeId !== node.id || state.wiringFrom.portName !== port.name)) {
    connectPorts(state.wiringFrom.nodeId, state.wiringFrom.portName, node.id, port.name);
    cancelWiring();
  }
}

function connectPorts(n1Id, p1Name, n2Id, p2Name) {
  if (n1Id === n2Id) return;
  const n1 = state.circuit.nodes.find((n) => n.id === n1Id);
  const n2 = state.circuit.nodes.find((n) => n.id === n2Id);
  if (!n1 || !n2) return;

  const port1 = getNodePorts(n1).find((p) => p.name === p1Name);
  const port2 = getNodePorts(n2).find((p) => p.name === p2Name);
  if (!port1 || !port2) return;

  let from = n1Id, fromPort = p1Name, to = n2Id, toPort = p2Name;
  if (state.mode === "high") {
    if (port1.dir === port2.dir) {
      showToast("Conecte uma saída (azul) a uma entrada (cinza/âmbar).");
      return;
    }
    if (port1.dir === "in" && port2.dir === "out") {
      from = n2Id;
      fromPort = p2Name;
      to = n1Id;
      toPort = p1Name;
    }
    // Substitui conexão anterior no mesmo pino de entrada
    state.circuit.edges = state.circuit.edges.filter((e) => !(e.to === to && e.toPort === toPort));
  } else {
    // Evita duplicata exata em baixo nível
    const exists = state.circuit.edges.some(
      (e) =>
        (e.from === from && e.fromPort === fromPort && e.to === to && e.toPort === toPort) ||
        (e.from === to && e.fromPort === toPort && e.to === from && e.toPort === fromPort)
    );
    if (exists) return;
  }

  state.circuit.edges.push({ id: uid("e"), from, fromPort, to, toPort });
  renderCircuitGraph();
}

function cancelWiring() {
  state.wiringFrom = null;
  el.wirePreviewLayer.innerHTML = "";
  renderCircuitGraph();
}

function setupCanvasInteractions() {
  el.circuitCanvas.addEventListener("mousedown", (ev) => {
    if (ev.target === el.circuitCanvas || ev.target === el.canvasBg) {
      if (state.wiringFrom) {
        cancelWiring();
        return;
      }
      state.selectedNodeId = null;
      state.selectedEdgeId = null;
      state.panning = { startX: ev.clientX - state.panX, startY: ev.clientY - state.panY };
      renderCircuitGraph();
      renderInspector();
    }
  });

  window.addEventListener("mousemove", (ev) => {
    if (state.draggingNode) {
      const pt = clientToWorld(ev.clientX, ev.clientY);
      state.draggingNode.node.x = Math.round(pt.x - state.draggingNode.offsetX);
      state.draggingNode.node.y = Math.round(pt.y - state.draggingNode.offsetY);
      renderCircuitGraph();
    } else if (state.panning) {
      state.panX = ev.clientX - state.panning.startX;
      state.panY = ev.clientY - state.panning.startY;
      applyViewportTransform();
    } else if (state.wiringFrom) {
      const pt = clientToWorld(ev.clientX, ev.clientY);
      el.wirePreviewLayer.innerHTML = "";
      el.wirePreviewLayer.appendChild(
        svgEl("path", { d: bezierPath(state.wiringFrom.startX, state.wiringFrom.startY, pt.x, pt.y), class: "wire-preview" })
      );
    }
  });

  window.addEventListener("mouseup", () => {
    state.draggingNode = null;
    state.panning = null;
  });

  el.circuitCanvas.addEventListener("wheel", (ev) => {
    ev.preventDefault();
    const factor = ev.deltaY < 0 ? 1.1 : 0.9;
    const newZoom = Math.max(0.35, Math.min(2.2, state.zoom * factor));
    const rect = el.circuitCanvas.getBoundingClientRect();
    const mx = ev.clientX - rect.left;
    const my = ev.clientY - rect.top;
    state.panX = mx - ((mx - state.panX) / state.zoom) * newZoom;
    state.panY = my - ((my - state.panY) / state.zoom) * newZoom;
    state.zoom = newZoom;
    applyViewportTransform();
  }, { passive: false });

  window.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      if (!el.xrayModal.classList.contains("hidden")) {
        closeXrayModal();
      } else if (state.wiringFrom) {
        cancelWiring();
      }
    } else if ((ev.key === "Delete" || ev.key === "Backspace") && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
      deleteSelected();
    }
  });

  el.btnZoomIn.addEventListener("click", () => {
    state.zoom = Math.min(2.2, state.zoom * 1.15);
    applyViewportTransform();
  });
  el.btnZoomOut.addEventListener("click", () => {
    state.zoom = Math.max(0.35, state.zoom / 1.15);
    applyViewportTransform();
  });
  el.btnFitView.addEventListener("click", fitView);
  el.btnClearCanvas.addEventListener("click", () => {
    state.circuit = { nodes: [], edges: [], durationNs: 25.0 };
    state.selectedNodeId = null;
    state.selectedEdgeId = null;
    state.simResult = null;
    stopPlayback();
    renderCircuitGraph();
    renderInspector();
  });
}

// ---------------------------------------------------------------------------
// Simulação no ngspice e Atualização dos Resultados
// ---------------------------------------------------------------------------

async function simulateCircuit() {
  if (state.isSimulating) return;
  state.isSimulating = true;
  el.btnSimulate.disabled = true;
  el.simStatusBadge.className = "status-badge running";
  el.simStatusBadge.textContent = "Compilando & rodando ngspice...";

  try {
    const resp = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: state.mode,
        compareKeys: state.compareKeys,
        circuit: state.circuit,
      }),
    });
    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || "Falha ao simular circuito.");
    }

    state.simResult = data;
    if (!data.compareKeys) {
      state.activeKeyView = 0;
    }
    el.keyViewGroup.classList.toggle("hidden", !data.compareKeys);
    updateKeyViewButtons();

    el.simStatusBadge.className = "status-badge ok";
    el.simStatusBadge.textContent = `ngspice-47: ${data.elapsedMs} ms`;
    el.dockSummaryPill.textContent = `DPA Pico: ${data.metrics.dpaPeakPct}% | ${data.metrics.coreTransistors}T núcleo | Simulado em ${data.elapsedMs} ms`;

    if (data.warnings?.length) {
      showToast(data.warnings[0], 4000);
    }

    el.timeSlider.max = String(Math.max(data.tGridNs.length - 1, 1));
    state.frameFloat = 0;
    el.timeSlider.value = "0";

    renderTruthAndMetrics(data);
    el.netlistCode.textContent = data.netlist || "";
    drawOscilloscopes();
    updateAnimationFrame();
    startPlayback();
  } catch (err) {
    el.simStatusBadge.className = "status-badge error";
    el.simStatusBadge.textContent = "Erro na simulação";
    showToast(err.message, 6000);
  } finally {
    state.isSimulating = false;
    el.btnSimulate.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Motor de Animação Temporal
// ---------------------------------------------------------------------------

function getCurrentFrameIndex() {
  if (!state.simResult?.tGridNs?.length) return 0;
  return Math.max(0, Math.min(state.simResult.tGridNs.length - 1, Math.round(state.frameFloat)));
}

function setActiveKeyView(keyVal) {
  state.activeKeyView = Number(keyVal) === 1 ? 1 : 0;
  updateKeyViewButtons();
  updateAnimationFrame();
  if (!el.xrayModal.classList.contains("hidden")) {
    renderXrayFrame();
  }
}

function updateKeyViewButtons() {
  el.btnViewK0.classList.toggle("active", state.activeKeyView === 0);
  el.btnViewK1.classList.toggle("active", state.activeKeyView === 1);
  el.xrayKey0Btn.classList.toggle("active", state.activeKeyView === 0);
  el.xrayKey1Btn.classList.toggle("active", state.activeKeyView === 1);
}

function updateAnimationFrame() {
  const res = state.simResult;
  if (!res) {
    el.timeText.textContent = "0.00 / 25.00 ns";
    el.vectorText.textContent = "Clique em ▶ Compilar e Simular";
    return;
  }

  const idx = getCurrentFrameIndex();
  const tNs = res.tGridNs[idx] ?? 0;
  el.timeText.textContent = `${tNs.toFixed(2)} / ${res.durationNs.toFixed(2)} ns`;
  el.timeSlider.value = String(idx);
  el.xrayTimeBadge.textContent = `${tNs.toFixed(2)} ns`;

  // Vetor de entrada atual
  if (res.vectorLabels?.length) {
    const vec = res.vectorLabels.find((v) => tNs >= v.tStart && tNs <= v.tEnd) || res.vectorLabels[res.vectorLabels.length - 1];
    el.vectorText.textContent = `Vetor: ${vec.text}`;
  } else {
    el.vectorText.textContent = `Modo Elétrico (${res.compareKeys ? `Key=${state.activeKeyView}` : "Simulação Única"})`;
  }

  const useK1 = res.compareKeys && state.activeKeyView === 1;
  const nodeVolts = useK1 ? res.nodeVoltagesK1 : res.nodeVoltagesK0;
  const gateCurrs = useK1 ? res.gateCurrentsK1_uA : res.gateCurrentsK0_uA;
  const totCurrSeries = useK1 ? res.totalCurrentK1_uA : res.totalCurrentK0_uA;
  const currentTotalUa = totCurrSeries?.[idx] ?? 0;

  // Atualiza fios no canvas
  for (const wref of animRefs.wires) {
    const ed = wref.edge;
    let v = null;
    if (res.mode === "high") {
      v = nodeVolts?.[ed.from]?.[idx] ?? null;
    } else {
      v = nodeVolts?.[`${ed.from}:${ed.fromPort}`]?.[idx] ?? nodeVolts?.[ed.from]?.[idx] ?? nodeVolts?.[ed.to]?.[idx] ?? null;
    }
    const col = voltageToColor(v);
    wref.baseEl.setAttribute("stroke", col);

    // Intensidade de fluxo nos fios
    const prevIdx = Math.max(0, idx - 1);
    const dv = v !== null && nodeVolts?.[ed.from] ? Math.abs(v - (nodeVolts[ed.from][prevIdx] ?? v)) : 0;
    const flowActive = Math.abs(v || 0) > 0.15 || dv > 0.03 || currentTotalUa > 0.05;
    wref.flowEl.setAttribute("opacity", flowActive ? (dv > 0.03 || currentTotalUa > 0.2 ? "0.9" : "0.35") : "0");
    wref.flowEl.setAttribute("stroke-dashoffset", String(-state.dashOffset));
  }

  // Atualiza blocos no canvas
  for (const [nid, refs] of Object.entries(animRefs.nodes)) {
    if (refs.type === "POLY_GATE") {
      const gm = res.gateMetrics?.[nid];
      const vOut = nodeVolts?.[nid]?.[idx];
      const iGate = gateCurrs?.[nid]?.[idx];
      const activeFn = gm ? (useK1 ? gm.fnK1 : gm.fnK0) : refs.tdef.key0_fn;
      const keyLabel = useK1 ? 1 : 0;
      refs.modeTxt.textContent = `MODO: ${activeFn} (K=${keyLabel})`;
      refs.modePill.setAttribute("fill", useK1 ? "rgba(244,63,94,0.18)" : "rgba(34,211,238,0.14)");
      refs.modePill.setAttribute("stroke", useK1 ? "rgba(244,63,94,0.48)" : "rgba(34,211,238,0.42)");
      refs.modeTxt.setAttribute("fill", useK1 ? "#fda4af" : "#67e8f9");
      if (vOut !== undefined) refs.vTxt.textContent = `${vOut.toFixed(2)} V`;
      if (iGate !== undefined) refs.iTxt.textContent = `|I|=${iGate.toFixed(2)} µA`;
    } else if (refs.type === "INPUT" || refs.type === "OUTPUT" || refs.type === "PROBE") {
      const v = nodeVolts?.[nid]?.[idx];
      if (v !== undefined) {
        refs.vTxt.textContent = `${v.toFixed(2)} V`;
        refs.vTxt.setAttribute("fill", voltageToColor(v));
      }
    } else if (refs.type === "ARI_FET") {
      const tr = (useK1 ? res.transistorsK1 : res.transistorsK0)?.[nid];
      if (tr) {
        const pol = tr.polarity[idx];
        const cond = tr.conduction[idx];
        const isP = pol === "p-FET";
        refs.polTxt.textContent = pol;
        refs.polTxt.setAttribute("fill", isP ? "#fcd34d" : "#67e8f9");
        refs.polBadge.setAttribute("fill", isP ? "rgba(245,158,11,0.22)" : "rgba(34,211,238,0.16)");
        refs.polBadge.setAttribute("stroke", isP ? "rgba(245,158,11,0.55)" : "rgba(34,211,238,0.45)");
        refs.chGlow.setAttribute("stroke", isP ? "#f59e0b" : "#22d3ee");
        refs.chGlow.setAttribute("opacity", String(0.1 + 0.9 * cond));
      }
    } else if (refs.type === "VDC" || refs.type === "VPWL") {
      const v = nodeVolts?.[nid]?.[idx];
      if (v !== undefined) {
        refs.vTxt.textContent = `${v.toFixed(2)} V`;
      }
    }
  }

  drawOscilloscopes();
  if (!el.xrayModal.classList.contains("hidden")) {
    renderXrayFrame();
  }
}

function startPlayback() {
  if (!state.simResult) return;
  state.isPlaying = true;
  el.btnPlayerPlay.textContent = "⏸";
  el.xrayPlayBtn.textContent = "⏸";
  state.lastTickMs = performance.now();
  if (!state.rafId) {
    state.rafId = requestAnimationFrame(animationLoop);
  }
}

function stopPlayback() {
  state.isPlaying = false;
  el.btnPlayerPlay.textContent = "▶";
  el.xrayPlayBtn.textContent = "▶";
  if (state.rafId) {
    cancelAnimationFrame(state.rafId);
    state.rafId = null;
  }
}

function animationLoop(nowMs) {
  if (!state.isPlaying || !state.simResult) {
    state.rafId = null;
    return;
  }
  const dt = Math.min((nowMs - state.lastTickMs) / 1000, 0.1);
  state.lastTickMs = nowMs;

  const totalFrames = state.simResult.tGridNs.length;
  const framesPerSec = 26 * state.speed;
  state.frameFloat = (state.frameFloat + dt * framesPerSec) % totalFrames;
  state.dashOffset = (state.dashOffset + dt * 55 * state.speed) % 18;

  updateAnimationFrame();
  state.rafId = requestAnimationFrame(animationLoop);
}

// ---------------------------------------------------------------------------
// Osciloscópios em Canvas HTML5 (Tensões & Corrente DPA)
// ---------------------------------------------------------------------------

function drawOscilloscopes() {
  const res = state.simResult;
  if (!res) return;
  drawVoltageScope(res);
  drawCurrentScope(res);
}

function setupHiDpiCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(Math.floor(rect.width), 200);
  const h = Math.max(Math.floor(rect.height), 90);
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

function drawVoltageScope(res) {
  const { ctx, w, h } = setupHiDpiCanvas(el.canvasScopeV);
  ctx.clearRect(0, 0, w, h);

  const pad = { l: 42, r: 12, t: 10, b: 22 };
  const pw = w - pad.l - pad.r;
  const ph = h - pad.t - pad.b;

  const traces = res.probeTraces || [];
  let minV = 0, maxV = 1.6;
  for (const tr of traces) {
    for (const v of tr.k0) { minV = Math.min(minV, v); maxV = Math.max(maxV, v); }
    for (const v of tr.k1) { minV = Math.min(minV, v); maxV = Math.max(maxV, v); }
  }
  minV = Math.floor((minV - 0.1) * 5) / 5;
  maxV = Math.ceil((maxV + 0.15) * 5) / 5;

  // Grade
  ctx.strokeStyle = "rgba(148,163,184,0.12)";
  ctx.lineWidth = 1;
  ctx.font = "10px monospace";
  ctx.fillStyle = "#94a3b8";
  for (let i = 0; i <= 4; i++) {
    const y = pad.t + (ph * i) / 4;
    const val = maxV - ((maxV - minV) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(pad.l, y);
    ctx.lineTo(pad.l + pw, y);
    ctx.stroke();
    ctx.fillText(`${val.toFixed(1)}V`, 4, y + 3);
  }

  const tArr = res.tGridNs;
  const maxT = res.durationNs || 25;
  const mapX = (t) => pad.l + (t / maxT) * pw;
  const mapY = (v) => pad.t + ph - ((v - minV) / Math.max(maxV - minV, 0.1)) * ph;

  // Empilha ligeiramente entradas/saídas ou sobrepõe com legenda limpa
  const legendItems = [];
  traces.forEach((tr, ti) => {
    const col = TRACE_COLORS[ti % TRACE_COLORS.length];
    legendItems.push(`<span><i class="leg-line" style="background:${col}"></i>${tr.label}</span>`);

    ctx.strokeStyle = col;
    ctx.lineWidth = tr.role === "output" ? 2.0 : 1.3;
    ctx.setLineDash([]);
    ctx.beginPath();
    tr.k0.forEach((v, i) => {
      const x = mapX(tArr[i]);
      const y = mapY(v);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    if (res.compareKeys && tr.role === "output") {
      ctx.strokeStyle = col;
      ctx.lineWidth = 1.6;
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      tr.k1.forEach((v, i) => {
        const x = mapX(tArr[i]);
        const y = mapY(v);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }
  });
  el.scopeVoltageLegend.innerHTML = legendItems.join("");

  // Eixo X e cursor de tempo
  for (let t = 0; t <= maxT; t += 5) {
    const x = mapX(t);
    ctx.fillText(`${t}ns`, x - 10, h - 5);
  }
  const curX = mapX(tArr[getCurrentFrameIndex()] ?? 0);
  ctx.strokeStyle = "#f8fafc";
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.moveTo(curX, pad.t);
  ctx.lineTo(curX, pad.t + ph);
  ctx.stroke();
}

function drawCurrentScope(res) {
  const { ctx, w, h } = setupHiDpiCanvas(el.canvasScopeI);
  ctx.clearRect(0, 0, w, h);

  const pad = { l: 48, r: 12, t: 10, b: 22 };
  const pw = w - pad.l - pad.r;
  const ph = h - pad.t - pad.b;

  const i0 = res.totalCurrentK0_uA || [];
  const i1 = res.totalCurrentK1_uA || [];
  let maxI = 0.2;
  for (const v of i0) maxI = Math.max(maxI, v);
  if (res.compareKeys) {
    for (const v of i1) maxI = Math.max(maxI, v);
  }
  maxI *= 1.15;

  ctx.strokeStyle = "rgba(148,163,184,0.12)";
  ctx.lineWidth = 1;
  ctx.font = "10px monospace";
  ctx.fillStyle = "#94a3b8";
  for (let i = 0; i <= 4; i++) {
    const y = pad.t + (ph * i) / 4;
    const val = maxI * (1 - i / 4);
    ctx.beginPath();
    ctx.moveTo(pad.l, y);
    ctx.lineTo(pad.l + pw, y);
    ctx.stroke();
    ctx.fillText(`${val.toFixed(2)}µA`, 2, y + 3);
  }

  const tArr = res.tGridNs;
  const maxT = res.durationNs || 25;
  const mapX = (t) => pad.l + (t / maxT) * pw;
  const mapY = (val) => pad.t + ph - (val / maxI) * ph;

  // Traço Key = 0
  ctx.strokeStyle = "#22d3ee";
  ctx.lineWidth = 1.8;
  ctx.setLineDash([]);
  ctx.beginPath();
  i0.forEach((v, idx) => {
    const x = mapX(tArr[idx]);
    const y = mapY(v);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Traço Key = 1
  if (res.compareKeys) {
    ctx.strokeStyle = "#f43f5e";
    ctx.lineWidth = 1.7;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    i1.forEach((v, idx) => {
      const x = mapX(tArr[idx]);
      const y = mapY(v);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }

  for (let t = 0; t <= maxT; t += 5) {
    ctx.fillText(`${t}ns`, mapX(t) - 10, h - 5);
  }
  const curX = mapX(tArr[getCurrentFrameIndex()] ?? 0);
  ctx.strokeStyle = "#f8fafc";
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.moveTo(curX, pad.t);
  ctx.lineTo(curX, pad.t + ph);
  ctx.stroke();
}

function bindScopeScrubbing(canvas, padLeft = 44, padRight = 12) {
  let scrubbing = false;
  const jumpToClientX = (clientX) => {
    if (!state.simResult?.tGridNs?.length) return;
    const rect = canvas.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (clientX - rect.left - padLeft) / Math.max(rect.width - padLeft - padRight, 20)));
    state.frameFloat = frac * (state.simResult.tGridNs.length - 1);
    updateAnimationFrame();
  };
  canvas.addEventListener("mousedown", (e) => {
    scrubbing = true;
    stopPlayback();
    jumpToClientX(e.clientX);
  });
  window.addEventListener("mousemove", (e) => {
    if (scrubbing) jumpToClientX(e.clientX);
  });
  window.addEventListener("mouseup", () => {
    scrubbing = false;
  });
}

// ---------------------------------------------------------------------------
// Tabela-Verdade e Cards de Métricas
// ---------------------------------------------------------------------------

function renderTruthAndMetrics(res) {
  const m = res.metrics;
  const cards = [
    { label: "DPA Pico (%)", val: `${m.dpaPeakPct.toFixed(2)}%`, hi: true },
    { label: "DPA Média (%)", val: `${m.dpaMeanPct.toFixed(2)}%`, hi: false },
    { label: "I_pico (K0 / K1)", val: `${m.iPeakK0_uA.toFixed(3)} / ${m.iPeakK1_uA.toFixed(3)} µA`, hi: false },
    { label: "Atraso Médio t_p", val: m.delayPs > 0 ? `${m.delayPs.toFixed(1)} ps` : "—", hi: false },
    { label: "Potência Média", val: `${m.powerNw.toFixed(1)} nW`, hi: false },
    { label: "PDP", val: m.pdpAj > 0 ? `${m.pdpAj.toFixed(2)} aJ` : "—", hi: false },
    { label: "Transistores ARI", val: `${m.coreTransistors}T / ${m.totalTransistors}T`, hi: false },
    { label: "Largura Total ΣW", val: `${m.sumW_um} µm`, hi: false },
    { label: "Dist. Hamming (HD)", val: `${m.hdPct.toFixed(1)}%`, hi: true },
  ];

  el.metricsCards.innerHTML = cards
    .map((c) => `<div class="metric-card ${c.hi ? "highlight" : ""}"><div class="m-label">${c.label}</div><div class="m-val">${c.val}</div></div>`)
    .join("");

  if (!res.truthTable?.length) {
    el.truthTableWrap.innerHTML = `<p class="empty-hint" style="padding:12px;">Modo Elétrico (Baixo Nível): acompanhe as tensões nodais no Osciloscópio e a polaridade p-FET/n-FET nos transistores ARI.</p>`;
    return;
  }

  const outHeaders = res.truthTable[0].outputs.map((o) => o.label);
  let html = `<table class="data-table"><thead><tr><th>Entradas</th>`;
  for (const oh of outHeaders) {
    html += `<th>${oh} (Key=0)</th><th>${oh} (Key=1)</th><th>Locking</th>`;
  }
  html += `</tr></thead><tbody>`;

  for (const row of res.truthTable) {
    html += `<tr><td><strong>${row.inputs}</strong></td>`;
    for (const o of row.outputs) {
      html += `<td><strong>${o.bitK0}</strong> (${o.vK0.toFixed(2)}V)</td>`;
      html += `<td><strong>${o.bitK1}</strong> (${o.vK1.toFixed(2)}V)</td>`;
      html += `<td><span class="diff-badge ${o.diff ? "changed" : "same"}">${o.diff ? "Inverte" : "Igual"}</span></td>`;
    }
    html += `</tr>`;
  }
  html += `</tbody></table>`;
  el.truthTableWrap.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Modal Raio-X (Esquemático Interno dos Transistores ARI)
// ---------------------------------------------------------------------------

function openXrayModal(gateId) {
  const node = state.circuit.nodes.find((n) => n.id === gateId && n.type === "POLY_GATE");
  if (!node) return;
  state.xrayGateId = gateId;
  const tdef = getTupleDef(node.props?.tupleId || "NAND_NOR");
  el.xrayTitle.textContent = `Raio-X: ${node.label || "Porta"} — ${tdef.name}`;
  el.xraySubtitle.textContent = tdef.internal_schematic?.subtitle || tdef.description;
  el.xrayModal.classList.remove("hidden");
  renderXrayFrame();
}

function closeXrayModal() {
  state.xrayGateId = null;
  el.xrayModal.classList.add("hidden");
}

function renderXrayFrame() {
  const gateId = state.xrayGateId;
  const node = state.circuit.nodes.find((n) => n.id === gateId);
  if (!node) return;

  const tdef = getTupleDef(node.props?.tupleId || "NAND_NOR");
  const sch = tdef.internal_schematic;
  if (!sch) return;

  const idx = getCurrentFrameIndex();
  const useK1 = state.simResult?.compareKeys && state.activeKeyView === 1;
  const xrayData = state.simResult?.gateXray?.[gateId];
  const nodeVolts = xrayData ? (useK1 ? xrayData.nodeVoltagesK1 : xrayData.nodeVoltagesK0) : null;
  const trStates = xrayData ? (useK1 ? xrayData.transistorsK1 : xrayData.transistorsK0) : null;

  el.xraySvg.setAttribute("viewBox", `0 0 ${sch.width} ${sch.height}`);
  el.xraySvg.innerHTML = "";

  const nodePos = Object.fromEntries(sch.nodes.map((nd) => [nd.id, nd]));
  const trPos = Object.fromEntries(sch.transistors.map((t) => [t.id, t]));

  const endpointPos = (ref) => {
    if (ref.includes(".")) {
      const [tid, term] = ref.split(".");
      const t = trPos[tid];
      if (!t) return { x: 0, y: 0 };
      if (term === "d") return { x: t.x, y: t.y - 24 };
      if (term === "s") return { x: t.x, y: t.y + 24 };
      if (term === "g") return { x: t.x - 24, y: t.y - 8 };
      if (term === "g1") return { x: t.x - 24, y: t.y + 8 };
      if (term === "g2") return { x: t.x + 22, y: t.y };
      return { x: t.x, y: t.y };
    }
    const nd = nodePos[ref];
    return nd ? { x: nd.x, y: nd.y } : { x: 0, y: 0 };
  };

  // Fios internos coloridos pela tensão real do ngspice
  for (const [a, b] of sch.wires) {
    const p1 = endpointPos(a);
    const p2 = endpointPos(b);
    const sigKey = !a.includes(".") ? a : !b.includes(".") ? b : null;
    const v = sigKey && nodeVolts?.[sigKey] ? nodeVolts[sigKey][idx] : null;
    el.xraySvg.appendChild(
      svgEl("line", {
        x1: p1.x,
        y1: p1.y,
        x2: p2.x,
        y2: p2.y,
        stroke: voltageToColor(v),
        "stroke-width": 2.4,
        "stroke-linecap": "round",
      })
    );
  }

  // Transistores ARI internos
  let tableRows = `<table class="data-table"><thead><tr><th>FET</th><th>Tipo</th><th>Canal</th><th>Vd / Vg / Vs</th><th>Vg2</th></tr></thead><tbody>`;

  for (const tr of sch.transistors) {
    const st = trStates?.[tr.id];
    const pol = st ? st.polarity[idx] : (useK1 ? "n-FET" : "p-FET");
    const cond = st ? st.conduction[idx] : 0;
    const isP = pol === "p-FET";

    const g = svgEl("g", { transform: `translate(${tr.x}, ${tr.y})` });
    g.appendChild(svgEl("rect", { x: -34, y: -26, width: 68, height: 52, rx: 8, fill: "#131c2e", stroke: isP ? "rgba(245,158,11,0.55)" : "rgba(34,211,238,0.55)", "stroke-width": 1.4 }));
    g.appendChild(svgEl("line", { x1: 0, y1: -24, x2: 0, y2: 24, stroke: isP ? "#f59e0b" : "#22d3ee", "stroke-width": 3.5, opacity: 0.25 + 0.75 * cond }));
    g.appendChild(svgEl("line", { x1: -12, y1: -16, x2: -12, y2: 16, stroke: "#cbd5e1", "stroke-width": 2 }));
    g.appendChild(svgEl("text", { x: 0, y: -30, "text-anchor": "middle", fill: "#e2e8f0", "font-size": 10, "font-weight": 700 }, `${tr.id} W=${tr.w}`));
    g.appendChild(svgEl("text", { x: 16, y: 4, "text-anchor": "middle", fill: isP ? "#fcd34d" : "#67e8f9", "font-size": 9.5, "font-weight": 800 }, isP ? "p" : "n"));
    el.xraySvg.appendChild(g);

    if (st) {
      tableRows += `<tr>
        <td><strong>${tr.id}</strong></td>
        <td><span class="pol-pill ${isP ? "pfet" : "nfet"}">${pol}</span></td>
        <td>${cond > 0.45 ? "ON" : "OFF"} (${Math.round(cond * 100)}%)</td>
        <td>${st.v_d[idx].toFixed(2)} / ${st.v_g[idx].toFixed(2)} / ${st.v_s[idx].toFixed(2)}</td>
        <td>${st.v_g2[idx].toFixed(2)}V</td>
      </tr>`;
    } else {
      tableRows += `<tr><td><strong>${tr.id}</strong></td><td colspan="4">Simule para ver tensões</td></tr>`;
    }
  }
  tableRows += `</tbody></table>`;
  el.xrayTransistorTable.innerHTML = tableRows;

  // Nós e rótulos de tensão
  for (const nd of sch.nodes) {
    const v = nodeVolts?.[nd.id]?.[idx];
    const col = voltageToColor(v);
    el.xraySvg.appendChild(svgEl("circle", { cx: nd.x, cy: nd.y, r: 5.5, fill: col, stroke: "#0b111b", "stroke-width": 1.5 }));
    const labelTxt = v !== undefined ? `${nd.label} (${v.toFixed(2)}V)` : nd.label;
    el.xraySvg.appendChild(svgEl("text", { x: nd.x, y: nd.y - 10, "text-anchor": "middle", fill: "#f1f5f9", "font-size": 10, "font-weight": 700 }, labelTxt));
  }
}

// ---------------------------------------------------------------------------
// Carregamento de Templates e Inicialização
// ---------------------------------------------------------------------------

function loadTemplate(templateId) {
  const tpl = state.templates.find((t) => t.id === templateId);
  if (!tpl) return;

  stopPlayback();
  state.mode = tpl.mode;
  updateModeButtons();
  state.circuit = JSON.parse(JSON.stringify({
    nodes: tpl.nodes,
    edges: tpl.edges,
    durationNs: tpl.durationNs || 25.0,
  }));
  state.selectedNodeId = null;
  state.selectedEdgeId = null;
  state.simResult = null;

  renderPalette();
  renderCircuitGraph();
  renderInspector();
  setTimeout(fitView, 20);
  simulateCircuit();
}

function updateModeButtons() {
  el.btnModeHigh.classList.toggle("active", state.mode === "high");
  el.btnModeLow.classList.toggle("active", state.mode === "low");
}

function populateTemplateSelect() {
  const highTpls = state.templates.filter((t) => t.mode === "high");
  const lowTpls = state.templates.filter((t) => t.mode === "low");
  el.templateSelect.innerHTML = `
    <optgroup label="Alto Nível (Portas Polimórficas)">
      ${highTpls.map((t) => `<option value="${t.id}">${t.name}</option>`).join("")}
    </optgroup>
    <optgroup label="Baixo Nível (Transistores ARI)">
      ${lowTpls.map((t) => `<option value="${t.id}">${t.name}</option>`).join("")}
    </optgroup>
  `;
}

async function init() {
  setupCanvasInteractions();
  bindScopeScrubbing(el.canvasScopeV, 42, 12);
  bindScopeScrubbing(el.canvasScopeI, 48, 12);

  el.btnModeHigh.addEventListener("click", () => {
    if (state.mode === "high") return;
    state.mode = "high";
    updateModeButtons();
    state.circuit = { nodes: [], edges: [], durationNs: 25.0 };
    state.selectedNodeId = null;
    state.simResult = null;
    stopPlayback();
    renderPalette();
    renderCircuitGraph();
    renderInspector();
  });

  el.btnModeLow.addEventListener("click", () => {
    if (state.mode === "low") return;
    state.mode = "low";
    updateModeButtons();
    state.circuit = { nodes: [], edges: [], durationNs: 25.0 };
    state.selectedNodeId = null;
    state.simResult = null;
    stopPlayback();
    renderPalette();
    renderCircuitGraph();
    renderInspector();
  });

  el.templateSelect.addEventListener("change", (e) => loadTemplate(e.target.value));
  el.chkCompareKeys.addEventListener("change", (e) => {
    state.compareKeys = e.target.checked;
  });
  el.btnSimulate.addEventListener("click", simulateCircuit);

  // Controles do Player
  el.btnPlayerPlay.addEventListener("click", () => (state.isPlaying ? stopPlayback() : startPlayback()));
  el.xrayPlayBtn.addEventListener("click", () => (state.isPlaying ? stopPlayback() : startPlayback()));
  el.btnPlayerStart.addEventListener("click", () => {
    stopPlayback();
    state.frameFloat = 0;
    updateAnimationFrame();
  });
  el.btnPlayerStep.addEventListener("click", () => {
    stopPlayback();
    if (!state.simResult) return;
    state.frameFloat = (Math.round(state.frameFloat) + 5) % state.simResult.tGridNs.length;
    updateAnimationFrame();
  });
  el.speedSelect.addEventListener("change", (e) => {
    state.speed = parseFloat(e.target.value) || 1.0;
  });
  el.timeSlider.addEventListener("input", (e) => {
    stopPlayback();
    state.frameFloat = Number(e.target.value);
    updateAnimationFrame();
  });

  el.btnViewK0.addEventListener("click", () => setActiveKeyView(0));
  el.btnViewK1.addEventListener("click", () => setActiveKeyView(1));
  el.xrayKey0Btn.addEventListener("click", () => setActiveKeyView(0));
  el.xrayKey1Btn.addEventListener("click", () => setActiveKeyView(1));
  el.btnCloseXray.addEventListener("click", closeXrayModal);

  // Abas do dock inferior
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const target = btn.dataset.tab;
      if (target === "scope") {
        document.getElementById("tabScope").classList.add("active");
        setTimeout(drawOscilloscopes, 10);
      } else if (target === "truth") {
        document.getElementById("tabTruth").classList.add("active");
      } else {
        document.getElementById("tabNetlist").classList.add("active");
      }
    });
  });

  el.btnToggleDock.addEventListener("click", () => {
    el.analysisDock.classList.toggle("minimized");
    el.btnToggleDock.textContent = el.analysisDock.classList.contains("minimized") ? "Expandir" : "Minimizar";
    setTimeout(drawOscilloscopes, 200);
  });

  el.btnCopyNetlist.addEventListener("click", () => {
    navigator.clipboard?.writeText(el.netlistCode.textContent || "");
    showToast("Netlist SPICE copiado para a área de transferência!", 2200);
  });

  window.addEventListener("resize", () => drawOscilloscopes());

  // Carrega definições de tuplas e templates do backend
  try {
    const [tupResp, tplResp] = await Promise.all([fetch("/api/tuples"), fetch("/api/templates")]);
    const tupData = await tupResp.json();
    const tplData = await tplResp.json();
    state.tuples = tupData.tuples || {};
    state.templates = tplData.templates || [];
    populateTemplateSelect();
    if (state.templates.length) {
      loadTemplate(state.templates[0].id);
    }
  } catch (err) {
    showToast(`Erro ao conectar ao servidor: ${err.message}`);
  }
}

init();
