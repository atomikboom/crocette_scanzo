document.addEventListener("DOMContentLoaded", () => {
  const sortSelect = document.getElementById("sort");
  const filterInput = document.getElementById("filterName");
  const membersContainer = document.getElementById("members");
  if (!sortSelect || !membersContainer) return;

  function getMembers() {
    return Array.from(membersContainer.querySelectorAll(".member"));
  }

  function applySort() {
    const members = getMembers();
    const [field, direction] = (sortSelect.value || "").split("-");
    const asc = direction === "asc";

    members.sort((a, b) => {
      let va, vb;
      switch (field) {
        case "crocette_prese":
          va = parseInt(a.dataset.cpre || "0");
          vb = parseInt(b.dataset.cpre || "0");
          break;
        case "crocette_pay":
          va = parseInt(a.dataset.cpay || "0");
          vb = parseInt(b.dataset.cpay || "0");
          break;
        case "crocette_due":
          va = parseInt(a.dataset.cdue || "0");
          vb = parseInt(b.dataset.cdue || "0");
          break;
        case "name":
          va = a.dataset.name || "";
          vb = b.dataset.name || "";
          break;
        case "last":
          va = new Date(a.dataset.last || 0).getTime();
          vb = new Date(b.dataset.last || 0).getTime();
          break;
        default:
          va = 0;
          vb = 0;
      }
      if (va < vb) return asc ? -1 : 1;
      if (va > vb) return asc ? 1 : -1;
      return 0;
    });

    // Sostituisci l'ordine nel DOM
    members.forEach((m) => membersContainer.appendChild(m));
  }

  function applyFilter() {
    const val = filterInput.value.trim().toLowerCase();
    getMembers().forEach((m) => {
      const name = (m.dataset.name || "").toLowerCase();
      m.style.display = name.includes(val) ? "" : "none";
    });
  }

  sortSelect.addEventListener("change", () => {
    localStorage.setItem("sortOrder", sortSelect.value);
    applySort();
  });
  filterInput.addEventListener("input", applyFilter);

  // Ripristina ultima scelta ordinamento se esiste
  const savedSort = localStorage.getItem("sortOrder");
  if (savedSort) {
    sortSelect.value = savedSort;
  }

  // Applica ordinamento e filtro iniziale
  applySort();
  applyFilter();
});
