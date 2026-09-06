(() => {
  const countEl = document.getElementById("deathCount");
  const cardEl = document.getElementById("counterCard");

  let lastCount = null;
  let refreshMs = 250;
  let timer = null;
  let requestInFlight = false;

  function animateDeath() {
    cardEl.classList.remove("death-flash");
    // Force reflow, aby animacja odpalała się przy każdym kolejnym zgonie.
    void cardEl.offsetWidth;
    cardEl.classList.add("death-flash");
  }

  async function updateCounter() {
    if (requestInFlight) return;
    requestInFlight = true;

    try {
      const response = await fetch(`/api/counter?t=${Date.now()}`, {
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const next = Math.max(0, Number.parseInt(data.deaths, 10) || 0);

      if (lastCount !== null && next > lastCount) {
        animateDeath();
      }

      if (next !== lastCount) {
        countEl.textContent = String(next);
        lastCount = next;
      }

      if (Number.isFinite(data.refresh_ms)) {
        refreshMs = Math.max(100, Number(data.refresh_ms));
      }
    } catch (error) {
      console.error("Dawnwalker overlay: nie udało się pobrać licznika", error);
    } finally {
      requestInFlight = false;
      clearTimeout(timer);
      timer = setTimeout(updateCounter, refreshMs);
    }
  }

  updateCounter();
})();
