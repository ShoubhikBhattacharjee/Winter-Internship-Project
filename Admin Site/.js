let allEntries = [];
let filteredEntries = [];

// Ordered list of sort keys (click order preserved)
let sortState = [];

// Example:
// [ { field: 'created_at', dir: 'asc' }, { field: 'id', dir: 'desc' } ]

async function loadEntries() {
  const res = await fetch("/api/data");
  allEntries = await res.json();
  applyFiltersAndSort();
}

document.getElementById("searchBox").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();

  filteredEntries = allEntries.filter((entry) => {
    return (
      entry.id.toLowerCase().includes(q) ||
      entry.question.toLowerCase().includes(q) ||
      entry.answer.toLowerCase().includes(q) ||
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
      let av = a[field] || "";
      let bv = b[field] || "";

      if (field === "created_at" || field === "modified") {
        av = new Date(av);
        bv = new Date(bv);
      }

      if (av < bv) return dir === "asc" ? -1 : 1;
      if (av > bv) return dir === "asc" ? 1 : -1;
    }
    return 0;
  });
}

function applyFiltersAndSort() {
  filteredEntries = [...allEntries];
  applySort();
  renderTable();
}

function renderTable() {
  const tbody = document.getElementById("entryTable");
  tbody.innerHTML = "";

  for (const entry of filteredEntries) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
<td>${entry.created_at?.split("T")[0] || ""}</td>
<td>${entry.id}</td>
<td class="truncate" title="${escapeHtml(entry.question)}">${
      entry.question
    }</td>
<td class="truncate">${(entry.tags || []).join(", ")}</td>
<td>${entry.source?.type || ""}</td>
<td>
<button class="btn btn-sm btn-outline-primary" onclick="openEdit('${
      entry.id
    }')">✏️</button>
<button class="btn btn-sm btn-outline-danger" onclick="confirmDelete('${
      entry.id
    }')">🗑</button>
</td>
`;

    tbody.appendChild(tr);
  }
}

function openEdit(id) {
  window.open(`/edit/${id}`, "_blank");
}

async function confirmDelete(id) {
  if (!confirm(`Delete entry ${id}?`)) return;

  const res = await fetch(`/api/delete/${id}`, { method: "DELETE" });

  if (res.ok) {
    allEntries = allEntries.filter((e) => e.id !== id);
    applyFiltersAndSort();
  }
}

function escapeHtml(text) {
  return text.replace(
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
