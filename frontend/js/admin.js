const MOCK_ADMIN_SCOOTERS = [
  {
    id: "S001",
    make: "Honda",
    colour: "Red",
    location: "RMIT Vietnam SGS",
    latitude: 10.729367,
    longitude: 106.693128,
    cost_per_minute: 0.5,
    status: "Available"
  },
  {
    id: "S002",
    make: "Yamaha",
    colour: "Blue",
    location: "Nguyen Van Linh",
    latitude: 10.7301,
    longitude: 106.6942,
    cost_per_minute: 0.55,
    status: "To Be Repaired"
  }
];

const MOCK_CUSTOMERS = [
  {
    id: 3,
    username: "alice",
    first_name: "Alice",
    last_name: "Nguyen",
    phone: "0411111111",
    email: "alice@example.com",
    balance: 50
  },
  {
    id: 4,
    username: "bob",
    first_name: "Bob",
    last_name: "Tran",
    phone: "0433333333",
    email: "bob@example.com",
    balance: 30
  }
];

const MOCK_USAGE_HISTORY = [
  {
    id: 1,
    scooter_id: "S001",
    customer_id: 3,
    start_time: "2026-05-18 10:00",
    end_time: "2026-05-18 10:10",
    duration_minutes: 10,
    total_cost: 5
  }
];

const USAGE_PAGE_SIZE = 10;

let currentScooters = [];
let currentUsageHistory = [];
let currentUsagePage = 1;

function showAdminMessage(message, type) {
  const messageBox = document.getElementById("admin-message");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;
  messageBox.className = `message ${type}`;
  messageBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function formatMoney(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-AU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function getScooterId(scooter) {
  return scooter.id || scooter.scooter_id;
}

function renderAdminInfo() {
  const user = getCurrentUser();

  document.getElementById("admin-welcome").textContent =
    `Welcome, ${user.last_name || user.username}`;
}

function renderScooters(scooters) {
  const container = document.getElementById("admin-scooter-list");

  if (!scooters || scooters.length === 0) {
    container.innerHTML = `<div class="empty-state">No scooters found.</div>`;
    return;
  }

  container.innerHTML = scooters.map((scooter) => {
    const scooterId = getScooterId(scooter);

    return `
      <article class="data-card">
        <h3>${scooterId}</h3>
        <p><strong>Make:</strong> ${scooter.make || "-"}</p>
        <p><strong>Colour:</strong> ${scooter.colour || scooter.color || "-"}</p>
        <p><strong>Location:</strong> ${scooter.location || "-"}</p>
        <p><strong>Cost:</strong> ${formatMoney(scooter.cost_per_minute)} / minute</p>
        <p><strong>Status:</strong> <span class="badge">${scooter.status || "Unknown"}</span></p>

        <div class="card-actions">
          <button class="mini-button" type="button" onclick="fillScooterForm('${scooterId}')">
            Edit
          </button>
          <button class="mini-button" type="button" onclick="fillReportForm('${scooterId}')">
            Report Issue
          </button>
          <button class="mini-button danger" type="button" onclick="deleteScooter('${scooterId}')">
            Delete
          </button>
        </div>
      </article>
    `;
  }).join("");
}

function renderCustomers(customers) {
  const container = document.getElementById("customer-list");

  if (!customers || customers.length === 0) {
    container.innerHTML = `<div class="empty-state">No customers found.</div>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Phone</th>
          <th>Email</th>
          <th>Balance</th>
        </tr>
      </thead>
      <tbody>
        ${customers.map((customer) => `
          <tr>
            <td>${customer.id || "-"}</td>
            <td>${customer.first_name || ""} ${customer.last_name || ""}</td>
            <td>${customer.phone || "-"}</td>
            <td>${customer.email || "-"}</td>
            <td>${formatMoney(customer.balance)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function getPaginatedUsageRecords() {
  const totalRecords = currentUsageHistory.length;
  const totalPages = Math.max(Math.ceil(totalRecords / USAGE_PAGE_SIZE), 1);

  if (currentUsagePage > totalPages) {
    currentUsagePage = totalPages;
  }

  if (currentUsagePage < 1) {
    currentUsagePage = 1;
  }

  const startIndex = (currentUsagePage - 1) * USAGE_PAGE_SIZE;
  const endIndex = startIndex + USAGE_PAGE_SIZE;

  return {
    records: currentUsageHistory.slice(startIndex, endIndex),
    totalRecords,
    totalPages,
    startIndex,
    endIndex: Math.min(endIndex, totalRecords)
  };
}

function renderUsagePagination(totalRecords, totalPages, startIndex, endIndex) {
  if (totalRecords <= USAGE_PAGE_SIZE) {
    return "";
  }

  return `
    <div
      class="action-row"
      style="
        justify-content: space-between;
        align-items: center;
        margin-top: 1rem;
        gap: 1rem;
        flex-wrap: wrap;
      "
    >
      <p class="small-note" style="margin: 0;">
        Showing ${startIndex + 1}-${endIndex} of ${totalRecords} records
      </p>

      <div class="action-row" style="gap: 0.5rem;">
        <button
          class="secondary-button"
          type="button"
          onclick="changeUsagePage(-1)"
          ${currentUsagePage <= 1 ? "disabled" : ""}
        >
          Previous
        </button>

        <span class="small-note" style="align-self: center;">
          Page ${currentUsagePage} of ${totalPages}
        </span>

        <button
          class="secondary-button"
          type="button"
          onclick="changeUsagePage(1)"
          ${currentUsagePage >= totalPages ? "disabled" : ""}
        >
          Next
        </button>
      </div>
    </div>
  `;
}

function renderUsageHistory(records) {
  const container = document.getElementById("usage-history-list");

  currentUsageHistory = records || [];

  if (!currentUsageHistory || currentUsageHistory.length === 0) {
    container.innerHTML = `<div class="empty-state">No usage history found.</div>`;
    return;
  }

  const pagination = getPaginatedUsageRecords();

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Scooter</th>
          <th>Customer</th>
          <th>Start</th>
          <th>End</th>
          <th>Duration</th>
          <th>Cost</th>
        </tr>
      </thead>
      <tbody>
        ${pagination.records.map((record) => `
          <tr>
            <td>${record.id || record.usage_id || "-"}</td>
            <td>${record.scooter_id || "-"}</td>
            <td>${record.customer_id || record.user_id || "-"}</td>
            <td>${formatDateTime(record.start_time)}</td>
            <td>${formatDateTime(record.end_time)}</td>
            <td>${record.duration_minutes || "-"} min</td>
            <td>${formatMoney(record.total_cost || record.cost)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>

    ${renderUsagePagination(
      pagination.totalRecords,
      pagination.totalPages,
      pagination.startIndex,
      pagination.endIndex
    )}
  `;
}

function changeUsagePage(direction) {
  const totalPages = Math.max(
    Math.ceil(currentUsageHistory.length / USAGE_PAGE_SIZE),
    1
  );

  currentUsagePage += direction;

  if (currentUsagePage < 1) {
    currentUsagePage = 1;
  }

  if (currentUsagePage > totalPages) {
    currentUsagePage = totalPages;
  }

  renderUsageHistory(currentUsageHistory);
}

async function loadAdminScooters() {
  showAdminMessage("Loading scooters...", "success");

  const result = await apiRequest("/api/admin/scooters", {
    method: "GET"
  });

  if (!result.success) {
    currentScooters = MOCK_ADMIN_SCOOTERS;
    renderScooters(currentScooters);
    showAdminMessage(
      "Backend is not available. Showing mock scooter data for UI testing.",
      "error"
    );
    return;
  }

  currentScooters = result.data || [];
  renderScooters(currentScooters);
  showAdminMessage("Scooters loaded.", "success");
}

async function loadCustomers() {
  const result = await apiRequest("/api/admin/customers", {
    method: "GET"
  });

  if (!result.success) {
    renderCustomers(MOCK_CUSTOMERS);
    showAdminMessage(
      "Backend is not available. Showing mock customer data for UI testing.",
      "error"
    );
    return;
  }

  renderCustomers(result.data || []);
  showAdminMessage("Customers loaded.", "success");
}

async function loadUsageHistory() {
  const result = await apiRequest("/api/admin/usage-history", {
    method: "GET"
  });

  currentUsagePage = 1;

  if (!result.success) {
    renderUsageHistory(MOCK_USAGE_HISTORY);
    showAdminMessage(
      "Backend is not available. Showing mock usage history for UI testing.",
      "error"
    );
    return;
  }

  renderUsageHistory(result.data || []);
  showAdminMessage("Usage history loaded.", "success");
}

function renderUsageReport(reportData) {
  const summaryContainer = document.getElementById("usage-report-summary");
  const chartContainer = document.getElementById("usage-report-chart");

  if (!summaryContainer || !chartContainer) {
    return;
  }

  if (!reportData || !reportData.series || reportData.series.length === 0) {
    summaryContainer.innerHTML = "";
    chartContainer.innerHTML = `<div class="empty-state">No usage report data found.</div>`;
    return;
  }

  const summary = reportData.summary || {};
  const series = reportData.series || [];

  const maxTrips = Math.max(
    ...series.map((row) => Number(row.trip_count || 0)),
    1
  );

  const maxCost = Math.max(
    ...series.map((row) => Number(row.total_cost || 0)),
    1
  );

  summaryContainer.innerHTML = `
    <article class="data-card">
      <h3>${summary.trip_count || 0}</h3>
      <p>Total Trips</p>
    </article>
    <article class="data-card">
      <h3>${summary.customer_count || 0}</h3>
      <p>Customer Count</p>
    </article>
    <article class="data-card">
      <h3>${summary.scooter_count || 0}</h3>
      <p>Scooter Count</p>
    </article>
    <article class="data-card">
      <h3>${summary.total_duration_minutes || 0} min</h3>
      <p>Total Duration</p>
    </article>
    <article class="data-card">
      <h3>${formatMoney(summary.total_cost || 0)}</h3>
      <p>Total Cost</p>
    </article>
  `;

  const chartBars = series.map((row) => {
    const period = row.period || row.start_date || "-";
    const trips = Number(row.trip_count || 0);
    const cost = Number(row.total_cost || 0);

    const tripHeight = Math.max((trips / maxTrips) * 150, trips > 0 ? 18 : 0);
    const costHeight = Math.max((cost / maxCost) * 150, cost > 0 ? 18 : 0);

    return `
      <div
        style="
          display: flex;
          flex-direction: column;
          align-items: center;
          min-width: 90px;
          flex: 1;
        "
      >
        <div
          style="
            height: 190px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 10px;
            width: 100%;
          "
        >
          <div
            style="
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: flex-end;
              height: 100%;
            "
          >
            <span
              style="
                font-size: 0.75rem;
                font-weight: 700;
                margin-bottom: 6px;
                color: #1d4ed8;
              "
            >
              ${trips}
            </span>
            <div
              title="${trips} trips"
              style="
                width: 24px;
                height: ${tripHeight}px;
                background: #2563eb;
                border-radius: 8px 8px 2px 2px;
              "
            ></div>
          </div>

          <div
            style="
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: flex-end;
              height: 100%;
            "
          >
            <span
              style="
                font-size: 0.75rem;
                font-weight: 700;
                margin-bottom: 6px;
                color: #047857;
              "
            >
              ${formatMoney(cost)}
            </span>
            <div
              title="${formatMoney(cost)}"
              style="
                width: 24px;
                height: ${costHeight}px;
                background: #059669;
                border-radius: 8px 8px 2px 2px;
              "
            ></div>
          </div>
        </div>

        <p
          style="
            margin: 0.75rem 0 0 0;
            font-size: 0.8rem;
            font-weight: 700;
            text-align: center;
            color: #0f172a;
          "
        >
          ${period}
        </p>
      </div>
    `;
  }).join("");

  chartContainer.innerHTML = `
    <div
      class="data-card"
      style="
        margin-bottom: 1rem;
        overflow-x: auto;
      "
    >
      <div
        style="
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        "
      >
        <div>
          <h3 style="margin: 0;">Usage Visualization</h3>
          <p class="small-note" style="margin-top: 0.35rem;">
            Blue bars show trip count. Green bars show total cost for each period.
          </p>
        </div>

        <div
          style="
            display: flex;
            gap: 1rem;
            align-items: center;
            font-size: 0.85rem;
            font-weight: 700;
          "
        >
          <span>
            <span
              style="
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #2563eb;
                border-radius: 3px;
                margin-right: 4px;
              "
            ></span>
            Trips
          </span>

          <span>
            <span
              style="
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #059669;
                border-radius: 3px;
                margin-right: 4px;
              "
            ></span>
            Cost
          </span>
        </div>
      </div>

      <div
        style="
          display: flex;
          align-items: flex-end;
          gap: 1.5rem;
          min-width: ${Math.max(series.length * 110, 520)}px;
          border-left: 1px solid #e5e7eb;
          border-bottom: 1px solid #e5e7eb;
          padding: 1rem 1rem 0.75rem 1rem;
          background:
            repeating-linear-gradient(
              to top,
              #ffffff,
              #ffffff 39px,
              #f1f5f9 40px
            );
        "
      >
        ${chartBars}
      </div>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Period</th>
          <th>Trips</th>
          <th>Customers</th>
          <th>Scooters</th>
          <th>Duration</th>
          <th>Total Cost</th>
          <th>Avg Cost / Trip</th>
          <th>Avg Duration / Trip</th>
        </tr>
      </thead>
      <tbody>
        ${series.map((row) => {
          const trips = Number(row.trip_count || 0);
          const duration = Number(row.total_duration_minutes || 0);
          const cost = Number(row.total_cost || 0);

          const averageCost = trips > 0 ? cost / trips : 0;
          const averageDuration = trips > 0 ? duration / trips : 0;

          return `
            <tr>
              <td>${row.period || row.start_date || "-"}</td>
              <td>${trips}</td>
              <td>${row.customer_count || 0}</td>
              <td>${row.scooter_count || 0}</td>
              <td>${duration} min</td>
              <td>${formatMoney(cost)}</td>
              <td>${formatMoney(averageCost)}</td>
              <td>${averageDuration.toFixed(1)} min</td>
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
}

async function loadUsageReport() {
  const groupBy = document.getElementById("usage-report-group")?.value || "day";

  const result = await apiRequest(`/api/admin/usage-report?group_by=${groupBy}`, {
    method: "GET"
  });

  if (!result.success) {
    renderUsageReport(null);
    showAdminMessage(result.message || "Could not load usage report.", "error");
    return;
  }

  renderUsageReport(result.data);
  showAdminMessage(`Usage report loaded by ${groupBy}.`, "success");
}

function getScooterFormData() {
  return {
    id: document.getElementById("scooter-id").value.trim(),
    make: document.getElementById("scooter-make").value.trim(),
    colour: document.getElementById("scooter-colour").value.trim(),
    location: document.getElementById("scooter-location").value.trim(),
    latitude: Number(document.getElementById("scooter-latitude").value),
    longitude: Number(document.getElementById("scooter-longitude").value),
    cost_per_minute: Number(document.getElementById("scooter-cost").value),
    status: document.getElementById("scooter-status").value
  };
}

function clearScooterForm() {
  document.getElementById("scooter-form").reset();
}

function fillScooterForm(scooterId) {
  const scooter = currentScooters.find((item) => {
    return getScooterId(item) === scooterId;
  });

  if (!scooter) {
    showAdminMessage("Scooter not found in current list.", "error");
    return;
  }

  document.getElementById("scooter-id").value = getScooterId(scooter);
  document.getElementById("scooter-make").value = scooter.make || "";
  document.getElementById("scooter-colour").value = scooter.colour || scooter.color || "";
  document.getElementById("scooter-location").value = scooter.location || "";
  document.getElementById("scooter-latitude").value = scooter.latitude || "";
  document.getElementById("scooter-longitude").value = scooter.longitude || "";
  document.getElementById("scooter-cost").value = scooter.cost_per_minute || "";
  document.getElementById("scooter-status").value = scooter.status || "Available";

  showAdminMessage(`Scooter ${scooterId} loaded into form.`, "success");
}

function fillReportForm(scooterId) {
  document.getElementById("report-scooter-id").value = scooterId;
  showAdminMessage(`Scooter ${scooterId} selected for issue report.`, "success");
}

function renderReportResult(resultData) {
  const container = document.getElementById("report-result-content");

  if (!container) {
    return;
  }

  if (!resultData) {
    container.innerHTML = `<div class="empty-state">No issue report submitted yet.</div>`;
    return;
  }

  const report = resultData.report || resultData;
  const email = resultData.email || {};
  const mapUrl = report.google_maps_url || "";
  const directionsUrl = report.google_maps_directions_url || "";
  const marker = report.marker || {};

  container.className = "data-card";
  container.innerHTML = `
    <h3>Report #${report.id || report.report_id || "-"}</h3>
    <p><strong>Scooter:</strong> ${report.scooter_id || "-"}</p>
    <p><strong>Issue:</strong> ${report.issue_description || "-"}</p>
    <p><strong>Report Status:</strong> ${report.status || "Open"}</p>
    <p><strong>Scooter Status:</strong> ${resultData.scooter_status || "To Be Repaired"}</p>

    <hr />

    <p><strong>Email Notification:</strong>
      ${
        email.sent
          ? `Sent to ${email.recipients?.join(", ") || "engineers"}${email.mock_mode ? " (mock mode)" : ""}`
          : `Not sent${email.message ? `: ${email.message}` : ""}`
      }
    </p>

    <p><strong>Location:</strong> ${report.location || marker.location || "-"}</p>
    <p><strong>Latitude:</strong> ${report.latitude || marker.latitude || "-"}</p>
    <p><strong>Longitude:</strong> ${report.longitude || marker.longitude || "-"}</p>

    <div class="card-actions">
      ${
        mapUrl
          ? `<a class="mini-button" href="${mapUrl}" target="_blank" rel="noopener noreferrer">Open Map</a>`
          : ""
      }
      ${
        directionsUrl
          ? `<a class="mini-button" href="${directionsUrl}" target="_blank" rel="noopener noreferrer">Directions</a>`
          : ""
      }
    </div>
  `;
}

async function saveScooter(event) {
  event.preventDefault();

  const scooter = getScooterFormData();

  if (
    !scooter.id ||
    !scooter.make ||
    !scooter.colour ||
    !scooter.location ||
    Number.isNaN(scooter.latitude) ||
    Number.isNaN(scooter.longitude) ||
    Number.isNaN(scooter.cost_per_minute)
  ) {
    showAdminMessage("Please fill in all scooter fields correctly.", "error");
    return;
  }

  const existingScooter = currentScooters.find((item) => {
    return getScooterId(item) === scooter.id;
  });

  const result = await apiRequest(
    existingScooter ? `/api/scooters/${scooter.id}` : "/api/scooters",
    {
      method: existingScooter ? "PUT" : "POST",
      body: scooter
    }
  );

  if (!result.success) {
    if (result.status === 0) {
      const index = currentScooters.findIndex((item) => {
        return getScooterId(item) === scooter.id;
      });

      if (index >= 0) {
        currentScooters[index] = scooter;
      } else {
        currentScooters.push(scooter);
      }

      renderScooters(currentScooters);
      showAdminMessage(
        "Backend is not available. Mock scooter list updated for UI testing.",
        "error"
      );
      return;
    }

    showAdminMessage(result.message || "Failed to save scooter.", "error");
    return;
  }

  showAdminMessage(result.message || "Scooter saved.", "success");
  clearScooterForm();
  loadAdminScooters();
}

async function deleteScooter(scooterId) {
  const confirmed = confirm(`Delete scooter ${scooterId}?`);

  if (!confirmed) {
    return;
  }

  const result = await apiRequest(`/api/scooters/${scooterId}`, {
    method: "DELETE"
  });

  if (!result.success) {
    if (result.status === 0) {
      currentScooters = currentScooters.filter((item) => {
        return getScooterId(item) !== scooterId;
      });

      renderScooters(currentScooters);
      showAdminMessage(
        "Backend is not available. Mock scooter deleted for UI testing.",
        "error"
      );
      return;
    }

    showAdminMessage(result.message || "Failed to delete scooter.", "error");
    return;
  }

  showAdminMessage(result.message || "Scooter deleted.", "success");
  loadAdminScooters();
}

async function submitAdminReport(event) {
  event.preventDefault();

  const scooterId = document.getElementById("report-scooter-id").value.trim();
  const issueDescription = document.getElementById("issue-description").value.trim();

  if (!scooterId || !issueDescription) {
    showAdminMessage("Please enter scooter ID and issue description.", "error");
    return;
  }

  const result = await apiRequest("/api/reports", {
    method: "POST",
    body: {
      scooter_id: scooterId,
      issue_description: issueDescription
    }
  });

  showAdminMessage(
    result.message || (result.success ? "Issue report submitted." : "Report failed."),
    result.success ? "success" : "error"
  );

  if (!result.success) {
    renderReportResult(null);
    return;
  }

  renderReportResult(result.data);

  document.getElementById("admin-report-form").reset();

  await loadAdminScooters();
}

document.addEventListener("DOMContentLoaded", () => {
  requireRole("admin", "login.html");

  renderAdminInfo();
  loadAdminScooters();
  loadCustomers();
  loadUsageHistory();
  loadUsageReport();

  document.getElementById("refresh-scooters-button").addEventListener(
    "click",
    loadAdminScooters
  );

  document.getElementById("refresh-customers-button").addEventListener(
    "click",
    loadCustomers
  );

  document.getElementById("refresh-usage-button").addEventListener(
    "click",
    loadUsageHistory
  );

  document.getElementById("refresh-usage-report-button").addEventListener(
    "click",
    loadUsageReport
  );

  document.getElementById("usage-report-group").addEventListener(
    "change",
    loadUsageReport
  );

  document.getElementById("scooter-form").addEventListener(
    "submit",
    saveScooter
  );

  document.getElementById("clear-scooter-form-button").addEventListener(
    "click",
    clearScooterForm
  );

  document.getElementById("admin-report-form").addEventListener(
    "submit",
    submitAdminReport
  );

  document.getElementById("logout-button").addEventListener("click", () => {
    logoutTo("login.html");
  });
});