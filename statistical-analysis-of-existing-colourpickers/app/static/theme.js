function isHex6(s){
  return typeof s === "string" && /^#[0-9a-fA-F]{6}$/.test(s.trim());
}

function normalizeHex(s, fallback){
  if(!s) return fallback;
  s = s.trim();
  if(!s.startsWith("#")) s = "#" + s;
  if(isHex6(s)) return s.toLowerCase();
  return fallback;
}

function setCssVars(bg, text){
  document.documentElement.style.setProperty("--bg-color", bg);
  document.documentElement.style.setProperty("--text-color", text);
}

function themeSwatchStyle(bg, text){
  // split swatch: left half bg, right half text
  return `linear-gradient(90deg, ${bg} 0 50%, ${text} 50% 100%)`;
}

async function apiGet(){
  const res = await fetch(window.THEME_API.list, { headers: { "Accept": "application/json" } });
  if(!res.ok) throw new Error("Failed to load themes");
  return await res.json();
}

async function apiAdd(bg, text){
  const res = await fetch(window.THEME_API.add, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bg, text })
  });
  if(!res.ok) throw new Error("Failed to save theme");
  return await res.json();
}

async function apiSetCurrent(id){
  const res = await fetch(window.THEME_API.setCurrent, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id })
  });
  if(!res.ok) throw new Error("Failed to set current theme");
  return await res.json();
}

function wireColorPair(hexInput, colorInput, onChange){
  const syncFromHex = () => {
    const hex = normalizeHex(hexInput.value, colorInput.value || "#ffffff");
    hexInput.value = hex;
    if(isHex6(hex)) colorInput.value = hex;
    onChange();
  };

  const syncFromPicker = () => {
    const hex = normalizeHex(colorInput.value, hexInput.value || "#ffffff");
    colorInput.value = hex;
    hexInput.value = hex;
    onChange();
  };

  hexInput.addEventListener("input", syncFromHex);
  colorInput.addEventListener("input", syncFromPicker);

  syncFromHex();
}

function closeDropdown(dropdown){
  dropdown.classList.remove("open");
}

function buildDropdown(listEl, themes, currentId, onPick){
  listEl.innerHTML = "";

  themes.forEach(t => {
    const item = document.createElement("div");
    item.className = "dropdown-item";
    item.setAttribute("role", "option");
    item.dataset.id = t.id;

    const sw = document.createElement("span");
    sw.className = "swatch";
    sw.style.background = themeSwatchStyle(t.bg, t.text);

    const label = document.createElement("span");
    label.className = "mono";
    label.textContent = `${t.bg} / ${t.text}`;

    item.appendChild(sw);
    item.appendChild(label);

    item.addEventListener("click", () => onPick(t));

    if(t.id === currentId){
      item.style.outline = "2px solid rgba(0,0,0,0.25)";
    }

    listEl.appendChild(item);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const bgHex = document.getElementById("bgHex");
  const bgColor = document.getElementById("bgColor");
  const textHex = document.getElementById("textHex");
  const textColor = document.getElementById("textColor");
  const saveBtn = document.getElementById("saveThemeBtn");

  const dropdown = document.getElementById("themeDropdown");
  const dropdownBtn = document.getElementById("themeDropdownBtn");
  const dropdownList = document.getElementById("themeDropdownList");
  const dropdownSwatch = document.getElementById("themeDropdownSwatch");
  const dropdownLabel = document.getElementById("themeDropdownLabel");

  if(!bgHex || !bgColor || !textHex || !textColor || !saveBtn || !dropdown || !dropdownBtn || !dropdownList){
    return;
  }

  const livePreview = () => {
    const bg = normalizeHex(bgHex.value, "#ffffff");
    const text = normalizeHex(textHex.value, "#111111");
    setCssVars(bg, text);
    dropdownSwatch.style.background = themeSwatchStyle(bg, text);
    dropdownLabel.textContent = `${bg} / ${text}`;
  };

  wireColorPair(bgHex, bgColor, livePreview);
  wireColorPair(textHex, textColor, livePreview);

  dropdownBtn.addEventListener("click", (e) => {
    e.preventDefault();
    dropdown.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if(!dropdown.contains(e.target)) closeDropdown(dropdown);
  });

  async function refreshThemes(){
    const store = await apiGet();
    const themes = store.themes || [];
    const currentId = store.current_id;

    buildDropdown(dropdownList, themes, currentId, async (picked) => {
      const updated = await apiSetCurrent(picked.id);
      const cur = (updated.themes || []).find(x => x.id === updated.current_id) || picked;

      bgHex.value = cur.bg; bgColor.value = cur.bg;
      textHex.value = cur.text; textColor.value = cur.text;
      livePreview();
      closeDropdown(dropdown);
      await refreshThemes();
    });

    const current = themes.find(t => t.id === currentId) || themes[0];
    if(current){
      dropdownSwatch.style.background = themeSwatchStyle(current.bg, current.text);
      dropdownLabel.textContent = `${current.bg} / ${current.text}`;
    }
  }

  saveBtn.addEventListener("click", async () => {
    const bg = normalizeHex(bgHex.value, "#ffffff");
    const text = normalizeHex(textHex.value, "#111111");

    if(!isHex6(bg) || !isHex6(text)){
      alert("Please enter valid 6-digit hex colors like #ffffff");
      return;
    }

    await apiAdd(bg, text);      
    livePreview();                
    await refreshThemes();        
  });

  try{
    await refreshThemes();
    livePreview();
  }catch(err){
    console.error(err);
  }
});
