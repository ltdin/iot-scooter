let selectedReport = null;

function showEngineerMessage(message, type) {
  const messageBox = document.getElementById("engineer-message");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;
  messageBox.className = `message ${type}`;
  messageBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function getReportId(report) {
  return report.id || report.report_id;
}

function getEngineerIdForQr() {
  const user = getCurrentUser();

  return (
    user?.id ||
    user?.user_id ||
    null
  );
}

function renderEngineerInfo() {
  const user = getCurrentUser();

  if (!user) {
    return;
  }

  document.getElementById("engineer-welcome").textContent =
    `Welcome, ${user.last_name || user.username}`;
}

function renderReports(reports) {
  const reportsList = document.getElementById("reports-list");

  if (!reports || reports.length === 0) {
    reportsList.innerHTML = `
      <div class="empty-state">No reported scooters found.</div>
    `;
    return;
  }

  reportsList.innerHTML = reports.map((report) => {
    const reportId = getReportId(report);

    return `
      <article class="data-card">
        <h3>Report #${reportId}</h3>
        <p><strong>Scooter:</strong> ${report.scooter_id || "-"}</p>
        <p><strong>Issue:</strong> ${report.issue_description || "-"}</p>
        <p><strong>Report Status:</strong> <span class="badge">${report.status || "Open"}</span></p>
        <p><strong>Scooter Status:</strong> <span class="badge">${report.scooter_status || "-"}</span></p>
        <p><strong>Make:</strong> ${report.make || "-"}</p>
        <p><strong>Colour:</strong> ${report.colour || report.color || "-"}</p>
        <p><strong>Location:</strong> ${report.location || "-"}</p>

        <button
          class="primary-button"
          type="button"
          onclick="selectReportById(${reportId})"
        >
          Select Report
        </button>
      </article>
    `;
  }).join("");
}

function hideEngineerQrCode() {
  const qrSection = document.getElementById("engineer-qr-section");
  const qrContainer = document.getElementById("engineer-qr-code");
  const qrTextElement = document.getElementById("engineer-qr-text");

  if (qrSection) {
    qrSection.style.display = "none";
  }

  if (qrContainer) {
    qrContainer.innerHTML = "";
  }

  if (qrTextElement) {
    qrTextElement.textContent = "";
  }
}

function buildEngineerQrText(action) {
  if (!selectedReport || !selectedReport.scooter_id) {
    return null;
  }

  const engineerId = getEngineerIdForQr();

  if (!engineerId) {
    return null;
  }

  return `${action}|${selectedReport.scooter_id}|${engineerId}`;
}

function showEngineerQrCode(action) {
  const qrSection = document.getElementById("engineer-qr-section");
  const qrContainer = document.getElementById("engineer-qr-code");
  const qrTextElement = document.getElementById("engineer-qr-text");
  const qrTitle = document.getElementById("engineer-qr-title");
  const qrInstruction = document.getElementById("engineer-qr-instruction");

  if (!qrSection || !qrContainer || !qrTextElement) {
    console.warn("Engineer QR elements are missing in engineer.html.");
    return;
  }

  const qrText = buildEngineerQrText(action);

  if (!qrText) {
    showEngineerMessage(
      "Cannot show engineer QR. Please select a report first and make sure you are logged in.",
      "error"
    );
    hideEngineerQrCode();
    return;
  }

  qrSection.style.display = "block";
  qrContainer.innerHTML = "";

  if (qrTitle) {
    qrTitle.textContent =
      action === "ENGINEER_UNLOCK"
        ? "Engineer Unlock QR Code"
        : "Engineer Lock QR Code";
  }

  if (qrInstruction) {
    qrInstruction.textContent =
      action === "ENGINEER_UNLOCK"
        ? "Show this QR code to the Raspberry Pi camera to unlock the scooter for repair."
        : "Show this QR code to the Raspberry Pi camera to lock the scooter after repair work.";
  }

  if (typeof QRCode === "undefined") {
    qrContainer.innerHTML = `
      <p class="message error">
        QR library could not be loaded. Please check internet connection or CDN access.
      </p>
    `;
    qrTextElement.textContent = `QR text: ${qrText}`;
    return;
  }

  new QRCode(qrContainer, {
    text: qrText,
    width: 220,
    height: 220,
    correctLevel: QRCode.CorrectLevel.M
  });

  qrTextElement.textContent = `QR text: ${qrText}`;
}

function getGoogleMapsUrl(report) {
  return (
    report.google_maps_url ||
    report.google_maps_directions_url ||
    report.map_url ||
    (
      report.latitude && report.longitude
        ? `https://www.google.com/maps/search/?api=1&query=${report.latitude},${report.longitude}`
        : ""
    )
  );
}

function renderSelectedReport() {
  const selectedBox = document.getElementById("selected-report-box");
  const locationBox = document.getElementById("location-box");

  if (!selectedReport) {
    selectedBox.className = "empty-state";
    selectedBox.innerHTML = "No report selected yet.";

    locationBox.className = "empty-state";
    locationBox.innerHTML = "Select a report to view scooter location details.";

    document.getElementById("repair-scooter-id").value = "";
    document.getElementById("repair-report-id").value = "";

    hideEngineerQrCode();
    return;
  }

  const reportId = getReportId(selectedReport);
  const googleMapsUrl = getGoogleMapsUrl(selectedReport);

  selectedBox.className = "data-card";
  selectedBox.innerHTML = `
    <h3>Report #${reportId}</h3>

    <p><strong>Scooter ID:</strong> ${selectedReport.scooter_id || "-"}</p>
    <p><strong>Issue:</strong> ${selectedReport.issue_description || "-"}</p>
    <p><strong>Report Status:</strong> <span class="badge">${selectedReport.status || "Open"}</span></p>
    <p><strong>Scooter Status:</strong> <span class="badge">${selectedReport.scooter_status || "-"}</span></p>

    <hr />

    <p><strong>Make:</strong> ${selectedReport.make || "-"}</p>
    <p><strong>Colour:</strong> ${selectedReport.colour || selectedReport.color || "-"}</p>
    <p><strong>Location:</strong> ${selectedReport.location || "-"}</p>

    <hr />

    <p class="small-note">
      Next step: scan the unlock QR to start repair. After finishing the repair work,
      scan the lock QR and submit the repair result.
    </p>
  `;

  locationBox.className = "data-card";
  locationBox.innerHTML = `
    <h3>${selectedReport.location || "Unknown location"}</h3>

    <p><strong>Scooter:</strong> ${selectedReport.scooter_id || "-"}</p>
    <p><strong>Make:</strong> ${selectedReport.make || "-"}</p>
    <p><strong>Colour:</strong> ${selectedReport.colour || selectedReport.color || "-"}</p>
    <p><strong>Latitude:</strong> ${selectedReport.latitude || "-"}</p>
    <p><strong>Longitude:</strong> ${selectedReport.longitude || "-"}</p>

    <div class="card-actions">
      ${
        googleMapsUrl
          ? `<a class="mini-button" href="${googleMapsUrl}" target="_blank" rel="noopener noreferrer">Open in Google Maps</a>`
          : `<p class="small-note">No map location is available for this report.</p>`
      }
    </div>
  `;

  document.getElementById("repair-scooter-id").value =
    selectedReport.scooter_id || "";

  document.getElementById("repair-report-id").value = reportId || "";

  hideEngineerQrCode();
}

async function loadReports() {
  showEngineerMessage("Loading reported scooters...", "success");

  const result = await apiRequest("/api/reports", {
    method: "GET"
  });

  if (!result.success) {
    window.currentReports = [];
    renderReports([]);
    showEngineerMessage(
      result.message || "Could not load repair reports.",
      "error"
    );
    return;
  }

  window.currentReports = result.data || [];
  renderReports(window.currentReports);

  showEngineerMessage(
    `Reported scooters loaded. Showing ${window.currentReports.length} active report(s).`,
    "success"
  );
}

function selectReportById(reportId) {
  const currentReports = window.currentReports || [];

  selectedReport = currentReports.find((report) => {
    return Number(getReportId(report)) === Number(reportId);
  });

  if (!selectedReport) {
    showEngineerMessage(`Report #${reportId} was not found.`, "error");
    return;
  }

  renderSelectedReport();
  showEngineerMessage(`Report #${reportId} selected.`, "success");
}

async function updateReportStatus(event) {
  event.preventDefault();

  if (!selectedReport) {
    showEngineerMessage("Please select a report first.", "error");
    return;
  }

  const reportId = getReportId(selectedReport);
  const status = document.getElementById("report-status").value;

  const result = await apiRequest(`/api/reports/${reportId}/status`, {
    method: "PUT",
    body: {
      status
    }
  });

  showEngineerMessage(
    result.message || (result.success ? "Report status updated." : "Report update failed."),
    result.success ? "success" : "error"
  );

  if (result.success) {
    selectedReport = null;
    renderSelectedReport();
    await loadReports();
  }
}

function showEngineerUnlockQr() {
  if (!selectedReport) {
    showEngineerMessage("Please select a report first.", "error");
    return;
  }

  showEngineerQrCode("ENGINEER_UNLOCK");
  showEngineerMessage(
    "Engineer Unlock QR is ready. Scan it with the Raspberry Pi camera.",
    "success"
  );
}

function showEngineerLockQr() {
  if (!selectedReport) {
    showEngineerMessage("Please select a report first.", "error");
    return;
  }

  showEngineerQrCode("ENGINEER_LOCK");
  showEngineerMessage(
    "Engineer Lock QR is ready. Scan it with the Raspberry Pi camera.",
    "success"
  );
}

async function submitRepairResult(event) {
  event.preventDefault();

  if (!selectedReport) {
    showEngineerMessage("Please select a report first.", "error");
    return;
  }

  const reportId = document.getElementById("repair-report-id").value.trim();
  const repairNotes = document.getElementById("repair-notes").value.trim();

  if (!selectedReport.scooter_id) {
    showEngineerMessage("Selected report does not have a scooter ID.", "error");
    return;
  }

  if (!reportId || !repairNotes) {
    showEngineerMessage("Please enter report ID and repair notes.", "error");
    return;
  }

  const result = await apiRequest("/api/engineer/repair-results", {
    method: "POST",
    body: {
      scooter_id: selectedReport.scooter_id,
      report_id: Number(reportId),
      result: repairNotes
    }
  });

  showEngineerMessage(
    result.message || (result.success ? "Repair result submitted." : "Repair result failed."),
    result.success ? "success" : "error"
  );

  if (result.success) {
    selectedReport = null;
    renderSelectedReport();
    document.getElementById("repair-result-form").reset();
    await loadReports();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  requireRole("engineer", "login.html");

  renderEngineerInfo();
  renderSelectedReport();
  loadReports();

  document.getElementById("refresh-reports-button").addEventListener(
    "click",
    loadReports
  );

  document.getElementById("engineer-unlock-button").addEventListener(
    "click",
    showEngineerUnlockQr
  );

  document.getElementById("engineer-lock-button").addEventListener(
    "click",
    showEngineerLockQr
  );

  document.getElementById("repair-result-form").addEventListener(
    "submit",
    submitRepairResult
  );

  document.getElementById("logout-button").addEventListener("click", () => {
    logoutTo("login.html");
  });
});