const PRAYER_ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"];
const PRAYER_LABELS = { Fajr: "Subuh", Sunrise: "Terbit", Dhuhr: "Dzuhur", Asr: "Ashar", Maghrib: "Maghrib", Isha: "Isya" };
const PRAYER_ICONS = { Fajr: "🌅", Sunrise: "☀️", Dhuhr: "🌞", Asr: "🌤️", Maghrib: "🌇", Isha: "🌙" };

const citySel = document.getElementById("city");
const locateBtn = document.getElementById("locate");
const errorEl = document.getElementById("error");
const heroEl = document.getElementById("hero");
const gridEl = document.getElementById("grid");
const themeToggle = document.getElementById("themeToggle");

let state = null, nextPrayer = null;

// Theme
function applyTheme(t) {
  document.body.classList.toggle("light", t === "light");
  themeToggle.textContent = t === "light" ? "☀️" : "🌙";
}
let theme = localStorage.getItem("prayer_theme") || "dark";
applyTheme(theme);
themeToggle.addEventListener("click", () => {
  theme = theme === "dark" ? "light" : "dark";
  localStorage.setItem("prayer_theme", theme);
  applyTheme(theme);
});

function toMinutes(t) { const [h, m] = (t || "").split(" ")[0].split(":").map(Number); return h * 60 + m; }
function getNextPrayer(timings) {
  const now = new Date();
  const nowMin = now.getHours() * 60 + now.getMinutes();
  const ordered = PRAYER_ORDER.filter(p => p !== "Sunrise").map(p => ({ key: p, minutes: toMinutes(timings[p]) }));
  let next = ordered.find(p => p.minutes != null && p.minutes > nowMin);
  if (next) return next;
  return { ...ordered[0], tomorrow: true };
}
function countdown(next) {
  const now = new Date();
  let target = next.minutes * 60;
  let cur = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  if (next.tomorrow) target += 24 * 3600;
  let diff = target - cur; if (diff < 0) diff += 24 * 3600;
  return { h: Math.floor(diff / 3600), m: Math.floor((diff % 3600) / 60), s: diff % 60 };
}

async function load(params) {
  errorEl.classList.add("hidden");
  heroEl.innerHTML = '<div class="spinner"></div><p class="muted">Memuat jadwal sholat…</p>';
  gridEl.innerHTML = "";
  const qs = new URLSearchParams(params).toString();
  try {
    const res = await fetch("/api/timings?" + qs);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Gagal");
    state = data;
    render(); tick();
  } catch (e) {
    errorEl.textContent = e.message; errorEl.classList.remove("hidden"); heroEl.innerHTML = "";
  }
}

function render() {
  const d = state;
  nextPrayer = getNextPrayer(d.timings);
  heroEl.innerHTML = `
    <div class="label">🌅 Sholat Berikutnya</div>
    <h2>${PRAYER_LABELS[nextPrayer.key]}</h2>
    <div id="countdown" class="countdown"></div>
    <div class="dates">
      ${d.gregorian.weekday}, ${d.gregorian.day} ${d.gregorian.month} ${d.gregorian.year}
      <span class="sep">•</span>
      ${d.hijri.day} ${d.hijri.month} ${d.hijri.year} H
    </div>
    <div class="city-tag">📍 ${d.city || citySel.value || "Lokasi Anda"}</div>`;
  gridEl.innerHTML = PRAYER_ORDER.map(key => `
    <div class="card ${nextPrayer.key === key ? "next" : ""}">
      ${nextPrayer.key === key ? '<span class="badge">Berikutnya</span>' : ""}
      <div class="icon">${PRAYER_ICONS[key]}</div>
      <div class="name">${PRAYER_LABELS[key]}</div>
      <div class="time">${(d.timings[key] || "").split(" ")[0]}</div>
    </div>`).join("");
}

function tick() {
  if (!nextPrayer) return;
  const cd = countdown(nextPrayer);
  const el = document.getElementById("countdown");
  if (el) el.innerHTML = `
    <div class="block"><div class="num">${String(cd.h).padStart(2,"0")}</div><div class="unit">Jam</div></div>
    <div class="sep">:</div>
    <div class="block"><div class="num">${String(cd.m).padStart(2,"0")}</div><div class="unit">Menit</div></div>
    <div class="sep">:</div>
    <div class="block"><div class="num">${String(cd.s).padStart(2,"0")}</div><div class="unit">Detik</div></div>`;
  if (cd.h === 0 && cd.m === 0 && cd.s === 0) render();
}
setInterval(tick, 1000);

citySel.addEventListener("change", () => {
  localStorage.setItem("prayer_city", citySel.value);
  load({ city: citySel.value });
});
locateBtn.addEventListener("click", () => {
  if (!navigator.geolocation) { errorEl.textContent = "Geolokasi tidak didukung"; errorEl.classList.remove("hidden"); return; }
  navigator.geolocation.getCurrentPosition(
    pos => load({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
    () => { errorEl.textContent = "Izin lokasi ditolak"; errorEl.classList.remove("hidden"); },
    { timeout: 8000 }
  );
});

const saved = localStorage.getItem("prayer_city");
if (saved) { citySel.value = saved; load({ city: saved }); } else load({ city: citySel.value });
