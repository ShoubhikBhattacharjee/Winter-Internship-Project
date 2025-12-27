// =======================================
// LOAD & SEARCH ENTRIES
// =======================================
async function loadEntries() {
  const queryInput = document.getElementById("search");
  const query = queryInput ? queryInput.value.trim() : "";

  const res = await fetch(`/api/data?q=${encodeURIComponent(query)}`);
  const data = await res.json();

  const table = document.getElementById("table");
  table.innerHTML = "";

  data.forEach(entry => {
    let fileInfo = "—";

    // Handle existing uploaded files
    if (entry.source && entry.source.path) {
      const ext = Object.keys(entry.source.path)[0];
      const filename = entry.id; // Use entry_id for backend file route

      fileInfo = `
        <a href="/files/by-id/${encodeURIComponent(filename)}" target="_blank">
          ${filename}${ext}
        </a>
      `;
    }

    table.innerHTML += `
      <tr>
        <td>${entry.id}</td>
        <td>${entry.question}</td>
        <td>${(entry.tags || []).join(", ")}</td>
        <td>${fileInfo}</td>
        <td>
          <button onclick='editEntry(${JSON.stringify(entry)})'>Edit</button>
          <button onclick='deleteEntry("${entry.id}")'>Delete</button>
        </td>
      </tr>
    `;
  });
}

// =======================================
// EDIT ENTRY
// =======================================
function editEntry(entry) {
  document.getElementById("entryId").value = entry.id;
  document.getElementById("question").value = entry.question;
  document.getElementById("answer").value = entry.answer;
  document.getElementById("tags").value = (entry.tags || []).join(",");
  document.getElementById("notes").value = entry.notes || "";

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// =======================================
// DELETE ENTRY
// =======================================
async function deleteEntry(id) {
  if (!confirm("Are you sure you want to delete this entry?")) return;

  await fetch(`/api/delete/${id}`, { method: "DELETE" });
  loadEntries();
}

// =======================================
// SAVE (ADD / UPDATE) ENTRY
// =======================================
document
  .getElementById("entryForm")
  .addEventListener("submit", async e => {
    e.preventDefault();

    const formData = new FormData();
    const fileInput = document.getElementById("file");

    formData.append("id", document.getElementById("entryId").value);
    formData.append("question", document.getElementById("question").value);
    formData.append("answer", document.getElementById("answer").value);
    formData.append("tags", document.getElementById("tags").value);
    formData.append("notes", document.getElementById("notes").value);

    if (fileInput.files.length > 0) {
      formData.append("file", fileInput.files[0]);
    }

    await fetch("/api/save", {
      method: "POST",
      body: formData
    });

    // Reset form
    document.getElementById("entryForm").reset();
    document.getElementById("entryId").value = "";

    loadEntries();
  });

// =======================================
// INITIAL LOAD
// =======================================
loadEntries();
