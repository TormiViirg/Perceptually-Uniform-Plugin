const W = 4096, H = 4096;         
const TILE = 256;                 
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
const viewport = document.getElementById('viewport');

const pxSlider = document.getElementById('px');
const pxVal = document.getElementById('pxVal');
const info = document.getElementById('info');
const hover = document.getElementById('hover');

canvas.width = W;
canvas.height = H;

function applyScale() {
    const px = Number(pxSlider.value);
    pxVal.textContent = String(px);
    canvas.style.width = (W * px) + 'px';
    canvas.style.height = (H * px) + 'px';
    info.textContent = `Logical: ${W}×${H} | Displayed: ${W*px}×${H*px} px | Tile: ${TILE}×${TILE}`;
}

const drawn = new Set();

function drawTile(tx, ty) {
    const x0 = tx * TILE;
    const y0 = ty * TILE;
    const tw = Math.min(TILE, W - x0);
    const th = Math.min(TILE, H - y0);

    const img = ctx.createImageData(tw, th);
    const d = img.data;

    let p = 0;
    for (let y = 0; y < th; y++) {
    const yy = y0 + y;
    let v = (yy << 12) + x0; 
    for (let x = 0; x < tw; x++) {
        d[p++] = (v >> 16) & 255; 
        d[p++] = (v >> 8) & 255;  
        d[p++] = v & 255;         
        d[p++] = 255;             
        v++;
    }
    }

    ctx.putImageData(img, x0, y0);
}

let rafPending = false;
function requestRenderVisible() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
    rafPending = false;
    renderVisibleTiles();
    });
}

function renderVisibleTiles() {
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
    const visR = Math.min(W*px, visL + vw);
    const visB = Math.min(H*px, visT + vh);

    const lpx = Math.max(0, Math.floor(visL / px) - TILE);
    const tpx = Math.max(0, Math.floor(visT / px) - TILE);
    const rpx = Math.min(W-1, Math.ceil(visR / px) + TILE);
    const bpx = Math.min(H-1, Math.ceil(visB / px) + TILE);

    const tx0 = Math.floor(lpx / TILE);
    const ty0 = Math.floor(tpx / TILE);
    const tx1 = Math.floor(rpx / TILE);
    const ty1 = Math.floor(bpx / TILE);

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

canvas.addEventListener('mousemove', (e) => {
    const px = Number(pxSlider.value);
    const rect = canvas.getBoundingClientRect();
    const lx = Math.floor((e.clientX - rect.left) / px);
    const ly = Math.floor((e.clientY - rect.top) / px);
    if (lx < 0 || ly < 0 || lx >= W || ly >= H) return;

    const v = (ly << 12) + lx; 
    const r = (v >> 16) & 255;
    const g = (v >> 8) & 255;
    const b = v & 255;

    hover.textContent = `Hover: x=${lx}, y=${ly} | RGB(${r}, ${g}, ${b}) | #${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`.toUpperCase();
});

pxSlider.addEventListener('input', () => {
    applyScale();
    requestRenderVisible();
});

viewport.addEventListener('scroll', requestRenderVisible);
window.addEventListener('resize', requestRenderVisible);

applyScale();

requestRenderVisible();