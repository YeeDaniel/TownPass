const MANIFEST_URL = "../assets/floorplans/taipei_main_station/manifest.json";

const kindLabels = {
  elevator: "電梯",
  stairs: "樓梯",
  platform: "月台",
  entrance: "出入口",
  junction: "通道／岔路",
};

const state = {
  data: null,
  mode: "2d",
  activeFloor: "B1",
  visibleFloors: new Set(),
  showBase: true,
  showMask: true,
  showNodes: true,
  showLabels: false,
  baseOpacity: 0.92,
  spacing: 112,
  zoom2d: 0.82,
  zoom3d: 0.56,
  panX: 0,
  panY: 0,
  rotationX: 57,
  rotationZ: -17,
  selectedNode: null,
  dragging: false,
  pointerX: 0,
  pointerY: 0,
};

const elements = {
  scene: document.querySelector("#scene"),
  world: document.querySelector("#world"),
  loading: document.querySelector("#loadingState"),
  error: document.querySelector("#errorState"),
  floorButtons: document.querySelector("#floorButtons"),
  stationName: document.querySelector("#stationName"),
  dataStatus: document.querySelector("#dataStatus"),
  floorCount: document.querySelector("#floorCount"),
  nodeCount: document.querySelector("#nodeCount"),
  facilityCount: document.querySelector("#facilityCount"),
  floorHelp: document.querySelector("#floorHelp"),
  spacingControl: document.querySelector("#spacingControl"),
  floorSpacing: document.querySelector("#floorSpacing"),
  floorSpacingValue: document.querySelector("#floorSpacingValue"),
  baseOpacity: document.querySelector("#baseOpacity"),
  baseOpacityValue: document.querySelector("#baseOpacityValue"),
  viewEyebrow: document.querySelector("#viewEyebrow"),
  viewTitle: document.querySelector("#viewTitle"),
  legend: document.querySelector("#legend"),
  inspector: document.querySelector("#nodeInspector"),
};

function resolveAsset(path) {
  return `../${path}`;
}

function localizedName(names) {
  return names?.["zh-TW"] || names?.en || "未命名";
}

function kindClass(kind) {
  return `kind-${kind in kindLabels ? kind : "junction"}`;
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function populateSummary() {
  const data = state.data;
  elements.stationName.textContent = localizedName(data.stationNames);
  elements.dataStatus.textContent = "原型資料";
  elements.floorCount.textContent = data.floors.length;
  elements.nodeCount.textContent = data.nodes.length;
  elements.facilityCount.textContent = data.nodes.filter((node) =>
    ["elevator", "stairs", "entrance", "platform"].includes(node.kind),
  ).length;
}

function renderLegend() {
  elements.legend.replaceChildren();
  Object.entries(kindLabels).forEach(([kind, label]) => {
    const item = createElement("div", "legend-item");
    item.append(createElement("i", `legend-dot ${kindClass(kind)}`));
    item.append(createElement("span", "", label));
    elements.legend.append(item);
  });
}

function renderFloorButtons() {
  elements.floorButtons.replaceChildren();
  state.data.floors.forEach((floor) => {
    const button = createElement("button", "floor-button", floor.id);
    button.type = "button";
    button.dataset.floor = floor.id;
    button.title =
      state.mode === "2d" ? `切換至 ${floor.id}` : `顯示／隱藏 ${floor.id}`;
    if (state.mode === "2d" && state.activeFloor === floor.id) {
      button.classList.add("is-active");
    }
    if (state.mode === "3d" && state.visibleFloors.has(floor.id)) {
      button.classList.add("is-active");
    }
    if (state.mode === "3d" && !state.visibleFloors.has(floor.id)) {
      button.classList.add("is-hidden-floor");
    }
    button.addEventListener("click", () => {
      if (state.mode === "2d") {
        state.activeFloor = floor.id;
      } else if (state.visibleFloors.has(floor.id)) {
        state.visibleFloors.delete(floor.id);
      } else {
        state.visibleFloors.add(floor.id);
      }
      renderFloorButtons();
      renderWorld();
      updateViewHeading();
    });
    elements.floorButtons.append(button);
  });
}

function createNode(node) {
  const button = createElement("button", `node-button ${kindClass(node.kind)}`);
  button.type = "button";
  button.style.left = `${node.position.x * 100}%`;
  button.style.top = `${node.position.y * 100}%`;
  button.dataset.nodeId = node.id;
  button.setAttribute("aria-label", localizedName(node.names));
  button.title = localizedName(node.names);
  if (state.selectedNode === node.id) button.classList.add("is-selected");

  button.append(createElement("span", "node-label", localizedName(node.names)));
  button.addEventListener("pointerdown", (event) => event.stopPropagation());
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    state.selectedNode = node.id;
    renderInspector(node);
    document
      .querySelectorAll(".node-button")
      .forEach((item) => item.classList.toggle("is-selected", item.dataset.nodeId === node.id));
  });
  return button;
}

function renderInspector(node) {
  const card = createElement("div", "inspector-card");
  card.append(createElement("p", "section-kicker", `${node.floorId} · ${node.kind.toUpperCase()}`));
  card.append(createElement("h3", "", localizedName(node.names)));
  card.append(createElement("p", "empty-inspector", node.names.en || node.id));
  const meta = createElement("div", "inspector-meta");
  meta.append(createElement("span", "", `x ${node.position.x.toFixed(3)}`));
  meta.append(createElement("span", "", `y ${node.position.y.toFixed(3)}`));
  meta.append(createElement("span", "", node.verified ? "已驗證" : "待驗證"));
  card.append(meta);
  elements.inspector.replaceChildren(card);
}

function renderWorld() {
  if (!state.data) return;
  elements.world.replaceChildren();
  elements.world.classList.toggle("show-labels", state.showLabels);

  const viewportWidth = elements.scene.clientWidth;
  const mapWidth = Math.min(790, Math.max(540, viewportWidth * 0.67));

  state.data.floors.forEach((floor, index) => {
    const plane = createElement("article", "floor-plane");
    const mapHeight = mapWidth * (floor.height / floor.width);
    plane.style.width = `${mapWidth}px`;
    plane.style.height = `${mapHeight}px`;

    const is2dInactive = state.mode === "2d" && state.activeFloor !== floor.id;
    const is3dHidden = state.mode === "3d" && !state.visibleFloors.has(floor.id);
    plane.classList.toggle("is-inactive-2d", is2dInactive);
    plane.classList.toggle("is-hidden-3d", is3dHidden);

    const z = state.mode === "3d" ? (state.data.floors.length - 1 - index) * state.spacing : 0;
    plane.style.transform = `translate3d(-50%, -50%, ${z}px)`;

    const image = createElement("img", "floor-image");
    image.src = resolveAsset(floor.image);
    image.alt = `${floor.id} ${floor.label}樓層圖`;
    image.draggable = false;
    image.style.opacity = state.showBase ? state.baseOpacity : 0;
    plane.append(image);

    const mask = createElement("div", "walkable-overlay");
    const maskUrl = `url("${resolveAsset(floor.walkableMask)}")`;
    mask.style.maskImage = maskUrl;
    mask.style.webkitMaskImage = maskUrl;
    mask.style.display = state.showMask ? "block" : "none";
    plane.append(mask);

    const nodeLayer = createElement("div", "node-layer");
    nodeLayer.style.display = state.showNodes ? "block" : "none";
    state.data.nodes
      .filter((node) => node.floorId === floor.id)
      .forEach((node) => nodeLayer.append(createNode(node)));
    plane.append(nodeLayer);

    plane.append(createElement("div", "floor-tag", `${floor.id} · ${floor.label}`));
    elements.world.append(plane);
  });

  applyWorldTransform();
}

function applyWorldTransform() {
  if (state.mode === "2d") {
    elements.world.style.transform =
      `translate3d(${state.panX}px, ${state.panY}px, 0) scale(${state.zoom2d})`;
  } else {
    elements.world.style.transform =
      `translate3d(${state.panX}px, ${state.panY}px, 0) ` +
      `rotateX(${state.rotationX}deg) rotateZ(${state.rotationZ}deg) scale(${state.zoom3d})`;
  }
}

function updateViewHeading() {
  if (!state.data) return;
  if (state.mode === "2d") {
    const floor = state.data.floors.find((item) => item.id === state.activeFloor);
    elements.viewEyebrow.textContent = "2D FLOOR PLAN";
    elements.viewTitle.textContent = `${floor.id} · ${floor.label}`;
    elements.floorHelp.textContent = "2D 模式一次檢視一個樓層。";
  } else {
    elements.viewEyebrow.textContent = "3D STACKED MODEL";
    elements.viewTitle.textContent = "B1–B4 · 分層空間模型";
    elements.floorHelp.textContent = "點擊樓層按鈕可顯示或隱藏該層。";
  }
}

function updateModeButtons(mode) {
  document.querySelectorAll(".mode-button").forEach((button) => {
    const isActive = button.getAttribute("data-mode") === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function setMode(mode) {
  state.mode = mode;
  state.panX = 0;
  state.panY = mode === "2d" ? 0 : 48;
  updateModeButtons(mode);
  elements.scene.classList.toggle("mode-2d", mode === "2d");
  elements.scene.classList.toggle("mode-3d", mode === "3d");
  elements.spacingControl.classList.toggle("is-hidden", mode !== "3d");
  renderFloorButtons();
  renderWorld();
  updateViewHeading();
}

function resetView() {
  state.panX = 0;
  state.panY = state.mode === "2d" ? 0 : 48;
  state.zoom2d = 0.82;
  state.zoom3d = 0.56;
  state.rotationX = 57;
  state.rotationZ = -17;
  applyWorldTransform();
}

function bindControls() {
  document.querySelectorAll(".mode-button").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });
  document.querySelector("#resetView").addEventListener("click", resetView);

  const toggleBindings = [
    ["#showBase", "showBase"],
    ["#showMask", "showMask"],
    ["#showNodes", "showNodes"],
    ["#showLabels", "showLabels"],
  ];
  toggleBindings.forEach(([selector, key]) => {
    document.querySelector(selector).addEventListener("change", (event) => {
      state[key] = event.target.checked;
      renderWorld();
    });
  });

  elements.baseOpacity.addEventListener("input", (event) => {
    state.baseOpacity = Number(event.target.value) / 100;
    elements.baseOpacityValue.textContent = `${event.target.value}%`;
    document.querySelectorAll(".floor-image").forEach((image) => {
      image.style.opacity = state.showBase ? state.baseOpacity : 0;
    });
  });

  elements.floorSpacing.addEventListener("input", (event) => {
    state.spacing = Number(event.target.value);
    elements.floorSpacingValue.textContent = event.target.value;
    renderWorld();
  });

  elements.scene.addEventListener("pointerdown", (event) => {
    state.dragging = true;
    state.pointerX = event.clientX;
    state.pointerY = event.clientY;
    elements.scene.setPointerCapture(event.pointerId);
  });

  elements.scene.addEventListener("pointermove", (event) => {
    if (!state.dragging) return;
    const deltaX = event.clientX - state.pointerX;
    const deltaY = event.clientY - state.pointerY;
    state.pointerX = event.clientX;
    state.pointerY = event.clientY;
    if (state.mode === "3d") {
      state.rotationZ += deltaX * 0.22;
      state.rotationX = Math.max(20, Math.min(82, state.rotationX - deltaY * 0.16));
    } else {
      state.panX += deltaX;
      state.panY += deltaY;
    }
    applyWorldTransform();
  });

  const stopDrag = () => {
    state.dragging = false;
  };
  elements.scene.addEventListener("pointerup", stopDrag);
  elements.scene.addEventListener("pointercancel", stopDrag);

  elements.scene.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      const delta = event.deltaY > 0 ? -0.06 : 0.06;
      if (state.mode === "2d") {
        state.zoom2d = Math.max(0.28, Math.min(2.2, state.zoom2d + delta));
      } else {
        state.zoom3d = Math.max(0.25, Math.min(1.35, state.zoom3d + delta));
      }
      applyWorldTransform();
    },
    { passive: false },
  );

  window.addEventListener("resize", () => renderWorld());
}

async function initialize() {
  bindControls();
  renderLegend();
  const requestedMode = new URLSearchParams(window.location.search).get("mode");
  const initialMode = requestedMode === "3d" ? "3d" : "2d";
  state.mode = initialMode;
  updateModeButtons(initialMode);
  try {
    const response = await fetch(MANIFEST_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    state.visibleFloors = new Set(state.data.floors.map((floor) => floor.id));
    state.activeFloor = state.data.floors[0]?.id || "B1";
    populateSummary();
    setMode(initialMode);
    elements.loading.classList.add("is-hidden");
  } catch (error) {
    elements.loading.classList.add("is-hidden");
    elements.error.classList.remove("is-hidden");
    elements.error.innerHTML =
      "無法載入 manifest.json。<br>請從專案根目錄啟動本機 HTTP server，" +
      "不要直接用 file:// 開啟 HTML。<br><small>" +
      String(error) +
      "</small>";
  }
}

initialize();
