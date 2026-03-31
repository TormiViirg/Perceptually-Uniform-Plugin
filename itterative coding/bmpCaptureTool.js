function clampRectToCanvas(x, y, w, h) {
  x = Math.max(0, Math.min(W, x | 0));
  y = Math.max(0, Math.min(H, y | 0));
  w = Math.max(0, Math.min(W - x, w | 0));
  h = Math.max(0, Math.min(H - y, h | 0));
  return { x, y, w, h };
}

function encodeBMP24FromImageData(imgData) {
  const w = imgData.width;
  const h = imgData.height;
  const src = imgData.data;

  const rowStride = (w * 3 + 3) & ~3; // 4-byte aligned
  const pixelBytes = rowStride * h;

  const fileHeaderSize = 14;
  const dibHeaderSize = 40;
  const pixelOffset = fileHeaderSize + dibHeaderSize;
  const fileSize = pixelOffset + pixelBytes;

  const buf = new ArrayBuffer(fileSize);
  const dv = new DataView(buf);
  let p = 0;

  dv.setUint8(p++, 0x42);
  dv.setUint8(p++, 0x4D);
  dv.setUint32(p, fileSize, true); p += 4;
  dv.setUint16(p, 0, true); p += 2;
  dv.setUint16(p, 0, true); p += 2;
  dv.setUint32(p, pixelOffset, true); p += 4;

  dv.setUint32(p, dibHeaderSize, true); p += 4;
  dv.setInt32(p, w, true); p += 4;
  dv.setInt32(p, h, true); p += 4;      
  dv.setUint16(p, 1, true); p += 2;      
  dv.setUint16(p, 24, true); p += 2;     
  dv.setUint32(p, 0, true); p += 4;     
  dv.setUint32(p, pixelBytes, true); p += 4;
  dv.setInt32(p, 2835, true); p += 4;   
  dv.setInt32(p, 2835, true); p += 4;
  dv.setUint32(p, 0, true); p += 4;
  dv.setUint32(p, 0, true); p += 4;

  const out = new Uint8Array(buf, pixelOffset);
  let outPos = 0;

  for (let y = h - 1; y >= 0; y--) {
    let inPos = y * w * 4;
    for (let x = 0; x < w; x++) {
      const r = src[inPos++];
      const g = src[inPos++];
      const b = src[inPos++];
      inPos++; 
      out[outPos++] = b;
      out[outPos++] = g;
      out[outPos++] = r;
    }
    while ((outPos % 4) !== 0) out[outPos++] = 0;
  }

  return buf;
}

function downloadArrayBuffer(buf, filename, mime = "image/bmp") {
  const blob = new Blob([buf], { type: mime });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function ensureTilesForRegion(x, y, w, h) {
  const tx0 = Math.floor(x / TILE), ty0 = Math.floor(y / TILE);
  const tx1 = Math.floor((x + w - 1) / TILE), ty1 = Math.floor((y + h - 1) / TILE);
  for (let ty = ty0; ty <= ty1; ty++) {
    for (let tx = tx0; tx <= tx1; tx++) {
      const key = tx + "," + ty;
      if (!drawn.has(key)) {
        drawn.add(key);
        drawTile(tx, ty);
      }
    }
  }
}

function saveCanvasRegionAsBMP(x, y, w, h, filename = "screenshot.bmp") {
  const r = clampRectToCanvas(x, y, w, h);
  ensureTilesForRegion(r.x, r.y, r.w, r.h);

  const img = ctx.getImageData(r.x, r.y, r.w, r.h);
  const bmpBuf = encodeBMP24FromImageData(img);
  downloadArrayBuffer(bmpBuf, filename);
}

function captureViewportBMP() {
  const px = Number(pxSlider.value);

  const left = viewport.scrollLeft;
  const top = viewport.scrollTop;
  const vw = viewport.clientWidth;
  const vh = viewport.clientHeight;

  const rectCanvas = canvas.getBoundingClientRect();
  const rectView = viewport.getBoundingClientRect();

  const offsetX = rectCanvas.left - rectView.left + viewport.scrollLeft;
  const offsetY = rectCanvas.top  - rectView.top  + viewport.scrollTop;

  const visL = Math.max(0, left - offsetX);
  const visT = Math.max(0, top  - offsetY);
  const visR = Math.min(W * px, visL + vw);
  const visB = Math.min(H * px, visT + vh);

  const x = Math.floor(visL / px);
  const y = Math.floor(visT / px);
  const w = Math.ceil((visR - visL) / px);
  const h = Math.ceil((visB - visT) / px);

  saveCanvasRegionAsBMP(x, y, w, h, `viewport_${w}x${h}.bmp`);
}

function captureFullBMP() {
  saveCanvasRegionAsBMP(0, 0, W, H, `full_${W}x${H}.bmp`);
}

document.getElementById("bmpView")?.addEventListener("click", captureViewportBMP);
document.getElementById("bmpFull")?.addEventListener("click", captureFullBMP);
