document.addEventListener("DOMContentLoaded", () => {
  initActivityRows();
  initGanttChart();
  initMandayChart();
});

function initActivityRows() {
  const addRowButton = document.getElementById("add-activity-row");
  if (!addRowButton) return;

  const rowsContainer = document.getElementById("activity-rows");
  const template = rowsContainer?.querySelector(".activity-row-group");

  if (!rowsContainer || !template) return;

  const attachRemoveHandler = (group) => {
    const removeButton = group.querySelector(".remove-row");
    if (!removeButton) return;
    removeButton.addEventListener("click", () => {
      if (rowsContainer.querySelectorAll(".activity-row-group").length > 1) {
        group.remove();
      }
    });
  };

  attachRemoveHandler(template);

  addRowButton.addEventListener("click", () => {
    const clone = template.cloneNode(true);
    clone.querySelectorAll("select").forEach((select) => {
      select.selectedIndex = 0;
    });
    clone.classList.remove("mt-1");
    clone.classList.add("mt-2");
    rowsContainer.appendChild(clone);
    attachRemoveHandler(clone);
  });
}

function initGanttChart() {
  const container = document.getElementById("gantt-chart");
  if (!container || !window.FrappeGantt || !Array.isArray(ganttData) || ganttData.length === 0) {
    return;
  }

  // eslint-disable-next-line no-new
  new window.FrappeGantt(container, ganttData, {
    view_mode: "Month",
    date_format: "YYYY-MM-DD",
    custom_popup_html: (task) => `
      <div class="card shadow-sm gantt-popup">
        <div class="card-body">
          <h6 class="mb-1">${task.name}</h6>
          <small>${task.start} → ${task.end}</small>
        </div>
      </div>
    `,
  });
}

function initMandayChart() {
  const canvas = document.getElementById("mandayChart");
  if (!canvas || !window.Chart || !mandayData || !mandayData.labels?.length) {
    return;
  }

  const ctx = canvas.getContext("2d");
  // eslint-disable-next-line no-new
  new window.Chart(ctx, {
    type: "bar",
    data: {
      labels: mandayData.labels,
      datasets: [
        {
          label: "Manday",
          data: mandayData.values,
          backgroundColor: "#0d6efd",
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Manday",
          },
        },
      },
    },
  });
}
