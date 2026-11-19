// Dhaka Weather Wager — demo page script.
// No wallet, no signing. This page only:
//   1. Shows the live Dhaka forecast from the same Open-Meteo API the
//      contract reads when a round is resolved.
//   2. Fills in tomorrow's date in the example commands.
//   3. Shows the deployed contract address (fill it in after deploy).

// TODO (after deploy): paste the deployed contract address here, e.g.
// const CONTRACT_ADDRESS = "0x1234...";
const CONTRACT_ADDRESS = "0x3720d28f28Be1e7e45AF701C6F7cc474816262C9";

const EXPLORER_BASE = "https://explorer-studio.genlayer.com/address/";

// Tomorrow's date in YYYY-MM-DD (Asia/Dhaka).
function dhakaDate(offsetDays) {
  const now = new Date(Date.now() + offsetDays * 24 * 60 * 60 * 1000);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Dhaka",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type).value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

function fillDates() {
  const tomorrow = dhakaDate(1);
  document.getElementById("tomorrow-date").textContent = tomorrow;
  document.querySelectorAll(".tomorrow").forEach((el) => {
    el.textContent = tomorrow;
  });
}

function showContract() {
  const addrEl = document.getElementById("contract-address");
  const linkEl = document.getElementById("explorer-link");
  if (CONTRACT_ADDRESS) {
    addrEl.textContent = CONTRACT_ADDRESS;
    linkEl.href = EXPLORER_BASE + CONTRACT_ADDRESS;
  } else {
    addrEl.textContent = "not deployed yet — deploy first, then paste the address into app.js";
    linkEl.href = "https://explorer-studio.genlayer.com/";
  }
}

async function loadWeather() {
  const box = document.getElementById("live-weather");
  const note = document.getElementById("weather-note");
  const url =
    "https://api.open-meteo.com/v1/forecast?latitude=23.81&longitude=90.41" +
    "&daily=precipitation_sum,precipitation_probability_max" +
    "&timezone=Asia%2FDhaka&forecast_days=3";
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    const days = data.daily.time.map((date, i) => ({
      date,
      rainMm: data.daily.precipitation_sum[i],
      prob: data.daily.precipitation_probability_max[i],
    }));
    box.innerHTML = days
      .map((d, i) => {
        const label = i === 0 ? "Today" : i === 1 ? "Tomorrow" : "Day after";
        const rainy = d.rainMm !== null && d.rainMm >= 0.1;
        return `<div class="stat">
          <div class="big">${rainy ? "🌧️" : "☀️"}</div>
          <div class="label">${label} · ${d.date}</div>
          <div style="margin-top:6px">Rain chance: <strong>${d.prob ?? "—"}%</strong></div>
          <div>Expected rain: <strong>${d.rainMm ?? "—"} mm</strong></div>
        </div>`;
      })
      .join("");
    note.textContent =
      "A day counts as rainy in the contract when Open-Meteo reports at least 0.1 mm of rain for Dhaka.";
  } catch (err) {
    box.innerHTML =
      '<div class="stat"><div class="big">⚠️</div>' +
      '<div class="label">Forecast could not be loaded (' + err.message +
      '). The contract reads the same API on-chain when a round is resolved.</div></div>';
  }
}

document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const text = document.getElementById(btn.dataset.copy).innerText;
    try {
      await navigator.clipboard.writeText(text);
      btn.textContent = "Copied ✓";
    } catch (err) {
      btn.textContent = "Copy failed — select the text manually";
    }
    setTimeout(() => { btn.textContent = "Copy"; }, 2000);
  });
});

fillDates();
showContract();
loadWeather();
