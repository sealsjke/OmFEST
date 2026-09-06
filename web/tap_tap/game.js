let points = 0;
let claiming = false;
let revealed = false;

async function renderScore() {
  document.getElementById("score").textContent = points.toLocaleString("ru-RU");
  document.getElementById("progress").value = points;
  if (points < 100000 || claiming || revealed) return;
  claiming = true;
  const status = document.getElementById("status");
  try {
    const response = await fetch("/api/claim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ score: points }),
    });
    if (!response.ok) throw new Error("Claim failed");
    const result = await response.json();
    document.getElementById("flag").textContent = result.flag;
    document.getElementById("reward").hidden = false;
    status.textContent = "";
    revealed = true;
  } catch {
    status.textContent = "Не удалось получить флаг. Нажми ещё раз.";
  } finally {
    claiming = false;
  }
}

// The score is intentionally writable from the browser console.
Object.defineProperty(window, "score", {
  get() { return points; },
  set(value) {
    points = Number(value);
    renderScore();
  },
});

window.setScore = function (value) { window.score = value; };
document.getElementById("tap").addEventListener("click", () => {
  window.score += 1;
});
renderScore();
