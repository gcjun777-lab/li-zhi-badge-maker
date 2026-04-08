const CANVAS_WIDTH = 319;
const CANVAS_HEIGHT = 508;
const PERSON_BOX = [44, 22, 275, 344];
const TEXT_COLOR = "#ffffff";
const UPPER_OFFSET_Y = 212;
const DEFAULT_SUBHEADLINE = "感恩有您  前程似锦";

const NAME_BLOCK = { top: 299, height: 72, left: 24, right: CANVAS_WIDTH - 24, fontSize: 42, minFontSize: 22, letterSpacing: 2, spaceExtra: 0 };
const HEADLINE_BLOCK = { top: 386, height: 34, left: 24, right: CANVAS_WIDTH - 24, fontSize: 22, minFontSize: 12, letterSpacing: 3, spaceExtra: 0 };
const SUBHEADLINE_BLOCK = { top: 428, height: 26, left: 24, right: CANVAS_WIDTH - 24, fontSize: 16, minFontSize: 10, letterSpacing: 2, spaceExtra: 2 };

function inferNameFromPath(imagePath) {
  const fileName = imagePath.replace(/^.*[\\/]/, "").replace(/\.[^.]+$/, "").trim();
  const stem = fileName.replace(/^[0-9\-_ ]+/, "");
  return stem || "未命名";
}

function buildHeadline(days) {
  return `和奥马一起走过${days}天`;
}

function calculateDaysFromJoinDate(joinDate, today = null) {
  if (!joinDate) {
    return "";
  }

  const current = today ? new Date(today) : new Date();
  const start = new Date(`${joinDate}T00:00:00`);
  if (Number.isNaN(start.getTime())) {
    return "";
  }

  const currentDay = new Date(current.getFullYear(), current.getMonth(), current.getDate());
  if (start > currentDay) {
    return "0";
  }

  const diffMs = currentDay.getTime() - start.getTime();
  return String(Math.floor(diffMs / 86400000));
}

function ensureRecordDefaults(record) {
  const next = { ...record };

  if (!next.name) {
    next.name = inferNameFromPath(next.imagePath || "");
  }

  if (!next.days && next.joinDate) {
    next.days = calculateDaysFromJoinDate(next.joinDate);
  }

  if (!next.outputName) {
    next.outputName = `${next.name || "未命名"}-离职厂牌-.png`;
  }

  return next;
}

function fontFamily(size) {
  return `${size}px "BadgeText", "Alibaba PuHuiTi", "Microsoft YaHei UI", sans-serif`;
}

function measureText(ctx, text, fontSize, letterSpacing = 0, spaceExtra = 0) {
  if (!text) {
    return { width: 0, height: 0 };
  }

  ctx.font = fontFamily(fontSize);

  if (letterSpacing <= 0) {
    const metrics = ctx.measureText(text);
    const ascent = metrics.actualBoundingBoxAscent || fontSize * 0.72;
    const descent = metrics.actualBoundingBoxDescent || fontSize * 0.24;
    return {
      width: Math.ceil(metrics.width),
      height: Math.ceil(ascent + descent)
    };
  }

  let width = 0;
  let height = 0;
  for (const char of text) {
    const metrics = ctx.measureText(char);
    let charWidth = metrics.width;
    if (char === " ") {
      charWidth += spaceExtra;
    }
    width += charWidth;
    height = Math.max(height, (metrics.actualBoundingBoxAscent || fontSize * 0.72) + (metrics.actualBoundingBoxDescent || fontSize * 0.24));
  }

  width += letterSpacing * Math.max(text.length - 1, 0);
  return { width: Math.ceil(width), height: Math.ceil(height) };
}

function fitFont(ctx, text, maxWidth, startSize, minSize, letterSpacing = 0, spaceExtra = 0) {
  if (!text) {
    return minSize;
  }

  for (let size = startSize; size >= minSize; size -= 1) {
    const metrics = measureText(ctx, text, size, letterSpacing, spaceExtra);
    if (metrics.width <= maxWidth) {
      return size;
    }
  }

  return minSize;
}

function drawSpacedText(ctx, text, x, y, fontSize, color, letterSpacing = 0, spaceExtra = 0) {
  ctx.font = fontFamily(fontSize);
  ctx.fillStyle = color;
  ctx.textBaseline = "top";

  if (letterSpacing <= 0) {
    ctx.fillText(text, x, y);
    return;
  }

  let cursorX = x;
  for (const char of text) {
    ctx.fillText(char, cursorX, y);
    let charWidth = ctx.measureText(char).width;
    if (char === " ") {
      charWidth += spaceExtra;
    }
    cursorX += charWidth + letterSpacing;
  }
}

function centerText(ctx, text, block) {
  if (!text) {
    return;
  }

  const width = block.right - block.left;
  const fontSize = fitFont(ctx, text, width, block.fontSize, block.minFontSize, block.letterSpacing, block.spaceExtra);
  const metrics = measureText(ctx, text, fontSize, block.letterSpacing, block.spaceExtra);
  const x = block.left + Math.max((width - metrics.width) / 2, 0);
  const y = block.top + Math.max((block.height - metrics.height) / 2, 0);

  drawSpacedText(ctx, text, x, y, fontSize, TEXT_COLOR, block.letterSpacing, block.spaceExtra);
}

function alphaBounds(canvas) {
  const { width, height } = canvas;
  const pixels = canvas.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, width, height).data;

  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const alpha = pixels[(y * width + x) * 4 + 3];
      if (!alpha) {
        continue;
      }
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
  }

  if (maxX < minX || maxY < minY) {
    return null;
  }

  return {
    x: minX,
    y: minY,
    width: maxX - minX + 1,
    height: maxY - minY + 1
  };
}

async function loadImage(url, cache) {
  if (!cache.has(url)) {
    cache.set(
      url,
      new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error(`无法加载图片: ${url}`));
        image.src = url;
      })
    );
  }

  return cache.get(url);
}

export async function renderBadge(record, targetCanvas, assets, cache) {
  const safeRecord = ensureRecordDefaults(record);
  const ctx = targetCanvas.getContext("2d");
  targetCanvas.width = CANVAS_WIDTH;
  targetCanvas.height = CANVAS_HEIGHT;
  ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  const [lowerTemplate, upperTemplate, sourceImage] = await Promise.all([
    loadImage(assets.lowerTemplateUrl, cache),
    loadImage(assets.upperTemplateUrl, cache),
    loadImage(safeRecord.imageDataUrl, cache)
  ]);

  ctx.drawImage(lowerTemplate, 0, 0);

  const sourceCanvas = document.createElement("canvas");
  sourceCanvas.width = sourceImage.naturalWidth || sourceImage.width;
  sourceCanvas.height = sourceImage.naturalHeight || sourceImage.height;
  sourceCanvas.getContext("2d").drawImage(sourceImage, 0, 0);

  const bounds = alphaBounds(sourceCanvas) || {
    x: 0,
    y: 0,
    width: sourceCanvas.width,
    height: sourceCanvas.height
  };

  const croppedCanvas = document.createElement("canvas");
  croppedCanvas.width = bounds.width;
  croppedCanvas.height = bounds.height;
  croppedCanvas.getContext("2d").drawImage(sourceCanvas, bounds.x, bounds.y, bounds.width, bounds.height, 0, 0, bounds.width, bounds.height);

  const [targetLeft, targetTop, targetRight, targetBottom] = PERSON_BOX;
  const targetWidth = targetRight - targetLeft;
  const targetHeight = targetBottom - targetTop;
  const scaleW = targetWidth / Math.max(croppedCanvas.width, 1);
  const scaleH = targetHeight / Math.max(croppedCanvas.height, 1);
  const baseScale = Math.min(scaleW, scaleH) * Math.max(Number(safeRecord.scaleAdjust) || 1, 0.1);
  const renderWidth = Math.max(Math.floor(croppedCanvas.width * baseScale), 1);
  const renderHeight = Math.max(Math.floor(croppedCanvas.height * baseScale), 1);
  const x = targetLeft + Math.floor((targetWidth - renderWidth) / 2) + Number(safeRecord.xOffset || 0);
  const y = targetBottom - renderHeight + Number(safeRecord.yOffset || 0);

  ctx.drawImage(croppedCanvas, x, y, renderWidth, renderHeight);
  ctx.drawImage(upperTemplate, 0, UPPER_OFFSET_Y);

  const headline = buildHeadline(safeRecord.days || "0");
  centerText(ctx, safeRecord.name, NAME_BLOCK);
  centerText(ctx, headline, HEADLINE_BLOCK);
  centerText(ctx, DEFAULT_SUBHEADLINE, SUBHEADLINE_BLOCK);

  return safeRecord;
}

export {
  CANVAS_HEIGHT,
  CANVAS_WIDTH,
  DEFAULT_SUBHEADLINE,
  buildHeadline,
  calculateDaysFromJoinDate,
  ensureRecordDefaults,
  inferNameFromPath
};
