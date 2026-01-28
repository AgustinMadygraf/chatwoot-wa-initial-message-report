const statusEl = document.getElementById("status");
const checkBtn = document.getElementById("checkBtn");

const okBadge = (ok) =>
  ok
    ? '<span class="badge bg-success">OK</span>'
    : '<span class="badge bg-danger">ERROR</span>';

const item = (name, result) => `
  <div class="d-flex justify-content-between align-items-center border rounded p-2 mb-2">
    <div>
      <strong>${name}</strong>
      <div class="text-muted small">${result.error || ""}</div>
    </div>
    ${okBadge(result.ok)}
  </div>`;

const render = (data) => {
  statusEl.innerHTML = `
    <div class="mb-2">${okBadge(data.ok)} Resultado general</div>
    ${item("Chatwoot API", data.chatwoot)}
    ${item("MySQL", data.mysql)}
  `;
};

checkBtn.addEventListener("click", async () => {
  statusEl.innerHTML = '<div class="text-muted">Verificando...</div>';
  try {
    const resp = await fetch("/api/status");
    const data = await resp.json();
    render(data);
  } catch (err) {
    statusEl.innerHTML = '<div class="text-danger">No se pudo verificar.</div>';
  }
});
