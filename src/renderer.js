import {
  CANVAS_HEIGHT,
  CANVAS_WIDTH,
  calculateDaysFromJoinDate,
  ensureRecordDefaults,
  renderBadge
} from "./badge-renderer.js";

const imageCache = new Map();
const assets = {
  lowerTemplateUrl: "./assets/templates/lower.png",
  upperTemplateUrl: "./assets/templates/upper.png",
  fontUrl: "./assets/fonts/Alibaba-PuHuiTi-Medium.otf"
};

const state = {
  record: null,
  renderToken: 0
};

const elements = {
  fileInput: document.querySelector("[data-input='image-file']"),
  chooseImageButton: document.querySelector("[data-action='choose-image']"),
  exportButton: document.querySelector("[data-action='export']"),
  imagePathText: document.querySelector("[data-field='image-name']"),
  nameInput: document.querySelector("[data-input='name']"),
  joinDateInput: document.querySelector("[data-input='join-date']"),
  daysValue: document.querySelector("[data-field='days']"),
  outputInput: document.querySelector("[data-input='output-name']"),
  scaleInput: document.querySelector("[data-input='scale']"),
  xInput: document.querySelector("[data-input='x-offset']"),
  yInput: document.querySelector("[data-input='y-offset']"),
  previewCanvas: document.querySelector("[data-canvas='preview']"),
  previewStage: document.querySelector("[data-preview-stage]"),
  previewCard: document.querySelector("[data-preview-card]"),
  lanyard: document.querySelector("[data-lanyard]"),
  status: document.querySelector("[data-preview-status]"),
  exportCanvas: document.createElement("canvas")
};

elements.exportCanvas.width = CANVAS_WIDTH;
elements.exportCanvas.height = CANVAS_HEIGHT;

function todayString() {
  const today = new Date();
  const month = `${today.getMonth() + 1}`.padStart(2, "0");
  const day = `${today.getDate()}`.padStart(2, "0");
  return `${today.getFullYear()}-${month}-${day}`;
}

function setStatus(message, kind = "info") {
  elements.status.textContent = message;
  elements.status.dataset.kind = kind;
}

function setEmptyPreview() {
  const ctx = elements.previewCanvas.getContext("2d");
  ctx.clearRect(0, 0, elements.previewCanvas.width, elements.previewCanvas.height);
  elements.previewStage.classList.add("is-empty");
}

function animateBadge() {
  elements.previewStage.classList.remove("is-animating");
  void elements.previewStage.offsetWidth;
  elements.previewStage.classList.add("is-animating");
}

function updateCardSize() {
  const rect = elements.previewStage.getBoundingClientRect();
  const availableWidth = Math.max(rect.width - 120, 180);
  const availableHeight = Math.max(rect.height - 96, 220);
  const scale = Math.min(availableWidth / CANVAS_WIDTH, availableHeight / CANVAS_HEIGHT);
  const cardWidth = Math.max(Math.floor(CANVAS_WIDTH * scale), 180);
  const cardHeight = Math.max(Math.floor(CANVAS_HEIGHT * scale), 280);
  const ribbonHeight = Math.max(Math.floor(cardHeight * 0.46), 118);
  const stageInset = Math.max(Math.floor(cardHeight * 0.1), 32);

  elements.previewCard.style.width = `${cardWidth}px`;
  elements.previewCard.style.height = `${cardHeight}px`;
  elements.lanyard.style.height = `${ribbonHeight}px`;
  elements.previewStage.style.setProperty("--stage-inset", `${stageInset}px`);
}

function setCardTilt(clientX, clientY) {
  if (elements.previewStage.classList.contains("is-animating")) {
    return;
  }

  const rect = elements.previewStage.getBoundingClientRect();
  const rx = ((clientY - rect.top) / rect.height - 0.5) * -6;
  const ry = ((clientX - rect.left) / rect.width - 0.5) * 7;
  elements.previewCard.style.setProperty("--tilt-x", `${rx.toFixed(2)}deg`);
  elements.previewCard.style.setProperty("--tilt-y", `${ry.toFixed(2)}deg`);
}

function resetCardTilt() {
  elements.previewCard.style.setProperty("--tilt-x", "0deg");
  elements.previewCard.style.setProperty("--tilt-y", "0deg");
}

function syncFormFromRecord() {
  const record = state.record;
  elements.imagePathText.textContent = record?.imageName || "尚未选择图片";
  elements.nameInput.value = record?.name || "";
  elements.joinDateInput.value = record?.joinDate || todayString();
  elements.daysValue.textContent = record?.days || "-";
  elements.outputInput.value = record?.outputName || "";
  elements.scaleInput.value = String(record?.scaleAdjust ?? 1);
  elements.xInput.value = String(record?.xOffset ?? 0);
  elements.yInput.value = String(record?.yOffset ?? 0);
}

function recordFromForm() {
  const previous = state.record || {};
  return ensureRecordDefaults({
    ...previous,
    name: elements.nameInput.value.trim(),
    joinDate: elements.joinDateInput.value,
    days: calculateDaysFromJoinDate(elements.joinDateInput.value),
    outputName: elements.outputInput.value.trim(),
    scaleAdjust: Number(elements.scaleInput.value || 1),
    xOffset: Number(elements.xInput.value || 0),
    yOffset: Number(elements.yInput.value || 0)
  });
}

async function renderCurrent({ animate = true } = {}) {
  if (!state.record?.imageDataUrl) {
    setEmptyPreview();
    return;
  }

  const token = ++state.renderToken;
  state.record = recordFromForm();

  try {
    const resolvedRecord = await renderBadge(state.record, elements.exportCanvas, assets, imageCache);
    if (token !== state.renderToken) {
      return;
    }

    state.record = resolvedRecord;
    syncFormFromRecord();

    const previewCtx = elements.previewCanvas.getContext("2d");
    elements.previewCanvas.width = CANVAS_WIDTH;
    elements.previewCanvas.height = CANVAS_HEIGHT;
    previewCtx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    previewCtx.drawImage(elements.exportCanvas, 0, 0);

    elements.previewStage.classList.remove("is-empty");
    resetCardTilt();
    if (animate) {
      animateBadge();
    }
    setStatus("预览已更新", "success");
  } catch (error) {
    setStatus(`渲染失败: ${error.message}`, "error");
  }
}

function handleFileSelection() {
  const file = elements.fileInput.files?.[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = async () => {
    state.record = ensureRecordDefaults({
      imagePath: file.name,
      imageName: file.name,
      imageDataUrl: reader.result,
      joinDate: state.record?.joinDate || todayString(),
      scaleAdjust: state.record?.scaleAdjust ?? 1,
      xOffset: state.record?.xOffset ?? 0,
      yOffset: state.record?.yOffset ?? 0
    });
    state.record.days = calculateDaysFromJoinDate(state.record.joinDate);
    syncFormFromRecord();
    await renderCurrent({ animate: true });
  };
  reader.readAsDataURL(file);
}

async function exportCurrent() {
  if (!state.record?.imageDataUrl) {
    setStatus("请先选择人物图片", "error");
    return;
  }

  await renderCurrent({ animate: false });

  const fileName = (elements.outputInput.value.trim() || state.record.outputName || "badge.png").replace(/[\\/:*?\"<>|]+/g, "-");
  const link = document.createElement("a");
  link.href = elements.exportCanvas.toDataURL("image/png");
  link.download = fileName.toLowerCase().endsWith(".png") ? fileName : `${fileName}.png`;
  link.click();
  setStatus("PNG 已导出", "success");
}

function attachEvents() {
  elements.chooseImageButton.addEventListener("click", () => elements.fileInput.click());
  elements.fileInput.addEventListener("change", handleFileSelection);
  elements.exportButton.addEventListener("click", exportCurrent);

  const rerender = () => {
    if (!state.record) {
      return;
    }
    renderCurrent({ animate: true });
  };

  elements.nameInput.addEventListener("input", rerender);
  elements.joinDateInput.addEventListener("change", rerender);
  elements.outputInput.addEventListener("input", () => {
    if (state.record) {
      state.record.outputName = elements.outputInput.value.trim();
    }
  });
  elements.scaleInput.addEventListener("input", rerender);
  elements.xInput.addEventListener("input", rerender);
  elements.yInput.addEventListener("input", rerender);

  elements.previewStage.addEventListener("pointermove", (event) => setCardTilt(event.clientX, event.clientY));
  elements.previewStage.addEventListener("pointerleave", resetCardTilt);
  new ResizeObserver(updateCardSize).observe(elements.previewStage);
  window.addEventListener("resize", updateCardSize);
}

async function bootstrap() {
  const fontFace = new FontFace("BadgeText", "url(./assets/fonts/Alibaba-PuHuiTi-Medium.otf)");
  await fontFace.load();
  document.fonts.add(fontFace);
  await document.fonts.ready;

  elements.joinDateInput.value = todayString();
  attachEvents();
  updateCardSize();
  setEmptyPreview();
  setStatus("选择人物图后即可生成工牌");
}

bootstrap().catch((error) => {
  setStatus(`初始化失败: ${error.message}`, "error");
});
