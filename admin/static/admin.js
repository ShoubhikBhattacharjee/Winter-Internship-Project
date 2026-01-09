let allEntries = [];
let filteredEntries = [];

// Ordered list of sort keys
let sortState = [];

document.addEventListener("DOMContentLoaded", loadEntries);

async function loadEntries() {
  const res = await fetch("/api/data");
  allEntries = await res.json();
  console.log("Loaded entries:", allEntries.length);
  filteredEntries = [...allEntries];
  applySort();
  renderTable();
}

document.getElementById("searchBox").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();

  filteredEntries = allEntries.filter((entry) => {
    return (
      (entry.id || "").toLowerCase().includes(q) ||
      (entry.question || "").toLowerCase().includes(q) ||
      (entry.answer || "").toLowerCase().includes(q) ||
      (entry.tags || []).join(",").toLowerCase().includes(q)
    );
  });

  applySort();
  renderTable();
});

function toggleSort(field) {
  const existing = sortState.find((s) => s.field === field);

  if (!existing) {
    sortState.push({ field, dir: "asc" });
  } else if (existing.dir === "asc") {
    existing.dir = "desc";
  } else {
    sortState = sortState.filter((s) => s.field !== field);
  }

  applySort();
  renderTable();
}

function applySort() {
  filteredEntries.sort((a, b) => {
    for (const { field, dir } of sortState) {
      let av = a[field] ?? "";
      let bv = b[field] ?? "";

      if (field === "created_at" || field === "modified") {
        av = new Date(av || 0);
        bv = new Date(bv || 0);
      }

      if (av < bv) return dir === "asc" ? -1 : 1;
      if (av > bv) return dir === "asc" ? 1 : -1;
    }
    return 0;
  });
}

function renderTable() {
  const tbody = document.getElementById("entryTable");
  tbody.innerHTML = "";

  for (const entry of filteredEntries) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${(entry.created_at || "").split("T")[0]}</td>
      <td>${entry.id || ""}</td>
      <td class="truncate" title="${escapeHtml(entry.question)}">
        ${escapeHtml(entry.question)}
      </td>
      <td class="truncate">${(entry.tags || []).join(", ")}</td>
      <td>${entry.source?.type || ""}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary"
          onclick="openEdit('${entry.id}')">✏️</button>
        <button class="btn btn-sm btn-outline-danger"
          onclick="confirmDelete('${entry.id}')">🗑</button>
      </td>
    `;

    tbody.appendChild(tr);
  }
}

function openEdit(id) {
  // Will work once edit route exists
  //window.open(`/entry?id=${id}`, "_blank");
  window.location.href = `/edit/${id}`;
}

async function confirmDelete(id) {
  if (!confirm(`Delete entry ${id}?`)) return;

  const res = await fetch(`/api/entry/${id}`, { method: "DELETE" });

  if (res.ok) {
    allEntries = allEntries.filter((e) => e.id !== id);
    filteredEntries = filteredEntries.filter((e) => e.id !== id);
    renderTable();
  } else {
    alert("Delete failed");
  }
}

function escapeHtml(text = "") {
  return String(text).replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[c])
  );
}
