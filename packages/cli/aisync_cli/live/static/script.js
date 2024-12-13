// Configuration constants
const CONFIG = {
  ZOOM: {
    MIN: 0.7,
    MAX: 2.5,
    STEP: 1.2,
  },
  WEBSOCKET: {
    URL: "ws://localhost:8402/ws/file_changes/subscribe",
    MAX_RECONNECT_ATTEMPTS: 5,
    RECONNECT_DELAY: 3000,
  },
};

// State management
const state = {
  zoom: {
    current: 1,
    translate: { x: 0, y: 0, lastX: 0, lastY: 0 },
  },
  drag: {
    active: false,
    start: { x: 0, y: 0 },
  },
  websocket: {
    connection: null,
    reconnectAttempts: 0,
  },
};

// DOM Elements cache
const elements = {
  init() {
    this.container = document.querySelector(".preview-container");
    this.wrapper = document.querySelector(".preview-wrapper");
    this.mermaidDiv = document.querySelector(".mermaid");
    this.zoomLevel = document.querySelector(".zoom-level");
    this.codeArea = document.getElementById("codeArea");
    this.graphDiv = document.getElementById("graph");
    this.wsStatus = {
      dot: document.getElementById("wsStatus"),
      text: document.getElementById("wsStatusText"),
    };
  },
};

// Mermaid initialization
function initializeMermaid(theme = "default") {
  mermaid.initialize({
    startOnLoad: true,
    theme: theme,
    darkMode: true,
  });
  centerDiagram();
}

// Transform handling
const transform = {
  update() {
    if (elements.wrapper) {
      const {
        current: zoom,
        translate: { x, y },
      } = state.zoom;
      elements.wrapper.style.transform = `translate(${x}px, ${y}px) scale(${zoom})`;
      elements.zoomLevel.textContent = `${Math.round(zoom * 100)}%`;
    }
  },

  updateZoom(newZoom, cursorPos = null) {
    const zoom = state.zoom;
    newZoom = Math.max(CONFIG.ZOOM.MIN, Math.min(CONFIG.ZOOM.MAX, newZoom));

    if (cursorPos && newZoom !== zoom.current) {
      const scale = newZoom / zoom.current;
      zoom.translate.x = cursorPos.x - (cursorPos.x - zoom.translate.x) * scale;
      zoom.translate.y = cursorPos.y - (cursorPos.y - zoom.translate.y) * scale;
      zoom.translate.lastX = zoom.translate.x;
      zoom.translate.lastY = zoom.translate.y;
    }

    zoom.current = newZoom;
    this.update();
  },
};

// Event handlers
const handlers = {
  wheel(e) {
    e.preventDefault();
    const { translate } = state.zoom;

    if (e.ctrlKey || e.metaKey) {
      // Zoom
      const delta = e.deltaY > 0 ? 1 / CONFIG.ZOOM.STEP : CONFIG.ZOOM.STEP;
      const rect = e.currentTarget.getBoundingClientRect();
      transform.updateZoom(state.zoom.current * delta, {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    } else {
      // Pan
      translate.x += -e.deltaX;
      translate.y += -e.deltaY;
      translate.lastX = translate.x;
      translate.lastY = translate.y;
      transform.update();
    }
  },

  dragStart(e) {
    if (e.button !== 0) return; // Only left mouse button
    const { translate } = state.zoom;
    state.drag.active = true;
    state.drag.start.x = e.clientX - translate.lastX;
    state.drag.start.y = e.clientY - translate.lastY;
    elements.container.classList.add("dragging");
  },

  drag(e) {
    if (!state.drag.active) return;
    e.preventDefault();

    const { translate } = state.zoom;
    translate.x = e.clientX - state.drag.start.x;
    translate.y = e.clientY - state.drag.start.y;
    transform.update();
  },

  dragEnd() {
    if (!state.drag.active) return;
    state.drag.active = false;
    const { translate } = state.zoom;
    translate.lastX = translate.x;
    translate.lastY = translate.y;
    elements.container.classList.remove("dragging");
  },
};

// WebSocket handling
const websocket = {
  connect() {
    if (state.websocket.reconnectAttempts >= CONFIG.WEBSOCKET.MAX_RECONNECT_ATTEMPTS) {
      this.updateStatus("disconnected", "Disconnected");
      return;
    }

    state.websocket.connection = new WebSocket(CONFIG.WEBSOCKET.URL);
    this.attachEventListeners();
  },

  attachEventListeners() {
    const ws = state.websocket.connection;

    ws.onopen = () => {
      this.updateStatus("connected", "Connected");
      state.websocket.reconnectAttempts = 0;
      this.reload();
    };

    ws.onmessage = (event) => {
      if (JSON.parse(event.data).channel === "file_changes") {
        this.reload();
      }
    };

    ws.onclose = () => {
      this.updateStatus("reconnect", `Reconnecting... Please Wait (Attempt ${state.websocket.reconnectAttempts + 1})`);

      setTimeout(() => {
        state.websocket.reconnectAttempts++;
        this.connect();
      }, CONFIG.WEBSOCKET.RECONNECT_DELAY);
    };

    ws.onerror = (error) => console.error("WebSocket error:", error);
  },

  updateStatus(className, text) {
    elements.wsStatus.dot.className = `status-dot ${className}`;
    elements.wsStatus.text.textContent = text;
  },

  async reload() {
    try {
      const response = await fetch("/graph");
      const data = await response.json();
      elements.codeArea.textContent = data.code;

      const theme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "default";
      initializeMermaid(theme);

      const result = await mermaid.render("graphDiv", elements.codeArea.textContent);
      elements.graphDiv.innerHTML = result.svg;
    } catch (error) {
      console.error("Failed to reload graph:", error);
    }
  },
};

// Initialize application
function initializeApp() {
  elements.init();

  // Set up event listeners
  elements.container.addEventListener("wheel", handlers.wheel, { passive: false });
  elements.container.addEventListener("mousedown", handlers.dragStart);
  elements.container.addEventListener("dragstart", (e) => e.preventDefault());
  document.addEventListener("mousemove", handlers.drag);
  document.addEventListener("mouseup", handlers.dragEnd);

  // Initialize WebSocket
  websocket.connect();

  // Clean up on page unload
  window.addEventListener("beforeunload", () => {
    if (state.websocket.connection) {
      state.websocket.connection.close();
    }
  });
}

// Export public functions
window.togglePanel = () => document.querySelector(".main-content").classList.toggle("expanded");

window.copyCode = (elementId) => {
  const codeArea = document.getElementById(elementId);
  navigator.clipboard.writeText(codeArea.textContent).then(() => {
    const button = codeArea.closest(".code-section").querySelector(".copy-button");
    const originalText = button.textContent;
    button.textContent = "Copied!";
    setTimeout(() => (button.textContent = originalText), 2000);
  });
};

window.toggleTheme = () => {
  const html = document.documentElement;
  const icon = document.querySelector(".theme-toggle");
  const newTheme = html.getAttribute("data-theme") === "light" ? "dark" : "light";

  initializeMermaid(newTheme === "dark" ? "dark" : "default");
  html.setAttribute("data-theme", newTheme);
  icon.textContent = newTheme === "light" ? "🌙" : "☀️";
  websocket.reload();
};

const centerDiagram = (newZoom = state.zoom.current) => {
  requestAnimationFrame(() => {
    const container = elements.container;
    const mermaidDiv = elements.mermaidDiv;

    if (!container || !mermaidDiv) return;

    const svg = mermaidDiv.querySelector("svg");
    if (!svg) return;

    // Get base dimensions (before zoom)
    const containerRect = container.getBoundingClientRect();
    const svgRect = svg.getBoundingClientRect();

    // Get the base dimensions of the SVG (without current zoom)
    const baseWidth = svgRect.width / state.zoom.current;
    const baseHeight = svgRect.height / state.zoom.current;

    // Calculate scaled dimensions
    const scaledWidth = baseWidth * newZoom;
    const scaledHeight = baseHeight * newZoom;

    // Calculate center position
    const centerX = (containerRect.width - scaledWidth) / 2;
    const centerY = (containerRect.height - scaledHeight) / 2 - 40; // Account for zoom controls

    // Update state
    state.zoom.current = newZoom;
    state.zoom.translate = {
      x: centerX,
      y: centerY,
      lastX: centerX,
      lastY: centerY,
    };

    transform.update();
  });
};

// Zoom controls
window.zoomIn = () => {
  transform.updateZoom(state.zoom.current * CONFIG.ZOOM.STEP);
  centerDiagram(newZoom);
};

window.zoomOut = () => {
  transform.updateZoom(state.zoom.current / CONFIG.ZOOM.STEP);
  centerDiagram(newZoom);
};

window.resetZoom = () => {
  // state.zoom.current = 1;
  centerDiagram(1);
};

// Start the application
initializeApp();
