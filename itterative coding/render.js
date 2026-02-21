const width = 4096, height = 4096;         
const TILE = 256; // doesn't have to render everything on boot                
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d', { willReadFrequently: true });//performance reasons because of the hover eyedropper
const viewport = document.getElementById('viewport');

const pxSlider = document.getElementById('px');
const pxVal = document.getElementById('pxVal');
const info = document.getElementById('info');
const hover = document.getElementById('hover');

canvas.width = width;
canvas.height = height;

function applyScale() {
    const px = Number(pxSlider.value);

    pxVal.textContent = String(px);

    canvas.style.width = (width * px) + 'px';
    canvas.style.height = (height * px) + 'px';

    info.textContent = `Logical(underlieing unique colour): ${width}×${height} | Displayed: ${width * px}×${height * px} px | Tile: ${TILE} × ${TILE}`;
}

const drawn = new Set();//keeps rendered ones in memory

function drawTile(tileOriginX, tileOriginY) {

    const x0 = tileOriginX * TILE;//canvas is 16*16 tiles this initializes the top left one for each
    const y0 = tileOriginY * TILE;
    const tileWidth = Math.min(TILE, width - x0);//how many pixels remain to the right starting at x staring coordinate(how long tile)
    const tileHeight = Math.min(TILE, height - y0);

    const img = ctx.createImageData(tileWidth, tileHeight);//contains alpha channel set to max 
    const rgbaData = img.data;

    let i = 0;

    for (let yRowinTile = 0; yRowinTile < tileHeight; yRowinTile++) {
        const yAbsolute = y0 + yRowinTile;

        let coordinateBucket = (yAbsolute << 12) + x0; 

        for (let xCollumninTile = 0; xCollumninTile < tileWidth; xCollumninTile++) {
            rgbaData[i++] = (coordinateBucket >> 16) & 255; 
            rgbaData[i++] = (coordinateBucket >> 8) & 255;  
            rgbaData[i++] = coordinateBucket & 255;         
            rgbaData[i++] = 255;             
            coordinateBucket++;
        }
    }

    ctx.putImageData(img, x0, y0);
}

let rafPending = false; //render spam prevention
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

    const visibleLeftEdge = Math.max(0, left - offsetX);//in relation to canvas not absolute
    const visibleTopEdge = Math.max(0, top  - offsetY);
    const visibleRightEdge = Math.min(width * px, visibleLeftEdge + vw);
    const visibleBottomEdge = Math.min(height * px, visibleTopEdge + vh);

    const leftpx = Math.max(0, Math.floor(visibleLeftEdge / px) - TILE);
    const toppx = Math.max(0, Math.floor(visibleTopEdge / px) - TILE);
    const rightpx = Math.min(width - 1, Math.ceil(visibleRightEdge / px) + TILE);
    const bottompx = Math.min(height - 1, Math.ceil(visibleBottomEdge / px) + TILE);

    const tilex0 = Math.floor(leftpx / TILE);//needed so the underlieing rectangle with the sRGB colours can be rendered with an arbitary visual size
    const tiley0 = Math.floor(toppx / TILE);//floor because coordinates work on integers
    const tilex1 = Math.floor(rightpx / TILE);
    const tiley1 = Math.floor(bottompx / TILE);
//tile index which tile is currently being rendered in first y then x coordinate
    for (let yTileIndex = tiley0; yTileIndex <= tiley1; yTileIndex++) {
        for (let xTileIndex = tilex0; xTileIndex <= tilex1; xTileIndex++) {
            const key = xTileIndex + "," + yTileIndex;// no rerenders or rendering things not shown yet on screen using coordinates

            if (!drawn.has(key)) {
                drawn.add(key);
                drawTile(xTileIndex, yTileIndex);
            }
        }
    }
}

canvas.addEventListener('mousemove', (e) => {
    const px = Number(pxSlider.value);//this uses fancy math to get the underlieing colour from before it took multible pixels because cors doesn't like eyepicker tools directly reading the screen 
    
    const rectangle = canvas.getBoundingClientRect();

    const xUnderlieingColour = Math.floor((e.clientX - rectangle.left) / px);
    const yUnderlieingColour = Math.floor((e.clientY - rectangle.top) / px);

    if (xUnderlieingColour < 0 || yUnderlieingColour < 0 || xUnderlieingColour >= width || yUnderlieingColour >= height) return;

    const colourBucket = (yUnderlieingColour << 12) + xUnderlieingColour; 
    const r = (colourBucket >> 16) & 255;
    const g = (colourBucket >> 8) & 255;
    const b = colourBucket & 255;

    hover.textContent = ` Hover: 
        x=${xUnderlieingColour},
        y=${yUnderlieingColour} | RGB(${r}, ${g}, ${b}) | #${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}
    `.toUpperCase();
});

pxSlider.addEventListener('input', () => {
    applyScale();
    requestRenderVisible();
});

viewport.addEventListener('scroll', requestRenderVisible);
window.addEventListener('resize', requestRenderVisible);

applyScale();

requestRenderVisible();