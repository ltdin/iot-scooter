let selectedBooking = null;

function showCustomerMessage(message, type) {
  const messageBox = document.getElementById("customer-message");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;
  messageBox.className = `message ${type}`;
  messageBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function formatMoney(value) {
  const numberValue = Number(value || 0);
  return `$${numberValue.toFixed(2)}`;
}

function updateStoredUser(updatedUser) {
  if (!updatedUser) {
    return;
  }

  const authData = getStoredAuth() || {};

  authData.user = {
    ...authData.user,
    ...updatedUser
  };

  saveAuthData(authData);
}

function renderCustomerInfo() {
  const user = getCurrentUser();

  if (!user) {
    return;
  }

  document.getElementById("customer-welcome").textContent =
    `Welcome, ${user.last_name || user.username}`;

  document.getElementById("balance-display").textContent =
    formatMoney(user.balance);
}

async function refreshCurrentUser(showMessage = true) {
  if (showMessage) {
    showCustomerMessage("Refreshing balance...", "success");
  }

  const result = await apiRequest("/api/me", {
    method: "GET"
  });

  if (!result.success) {
    if (showMessage) {
      showCustomerMessage(
        result.message || "Could not refresh balance.",
        "error"
      );
    }
    return;
  }

  updateStoredUser(result.data);
  renderCustomerInfo();

  if (showMessage) {
    showCustomerMessage("Balance refreshed.", "success");
  }
}

function getBookingFromResponse(response) {
  if (!response || !response.data) {
    return null;
  }

  return (
    response.data.booking ||
    response.data.current_booking ||
    response.data.transaction?.booking ||
    response.data
  );
}

function getUnlockCodeFromBooking(booking) {
  if (!booking) {
    return null;
  }

  return (
    booking.unlock_code ||
    booking.qr_payload?.unlock_code ||
    booking.data?.unlock_code ||
    null
  );
}

function getCustomerIdForQr(booking) {
  const currentUser = getCurrentUser();

  return (
    booking?.user_id ||
    booking?.customer_id ||
    currentUser?.id ||
    currentUser?.user_id ||
    null
  );
}

function buildQrText(action, booking) {
  const unlockCode = getUnlockCodeFromBooking(booking);
  const userId = getCustomerIdForQr(booking);

  if (!unlockCode || !userId) {
    return null;
  }

  return `${action}|${unlockCode}|${userId}`;
}

function showBookingQrCode(action, booking) {
  const qrSection = document.getElementById("booking-qr-section");
  const qrContainer = document.getElementById("booking-qr-code");
  const unlockCodeText = document.getElementById("booking-unlock-code");
  const qrTitle = document.getElementById("booking-qr-title");
  const qrInstruction = document.getElementById("booking-qr-instruction");

  if (!qrSection || !qrContainer || !unlockCodeText) {
    console.warn("QR display elements are missing in customer.html.");
    return;
  }

  const qrText = buildQrText(action, booking);

  if (!qrText) {
    console.warn("Cannot build QR text. Missing unlock_code or user_id.", booking);
    hideBookingQrCode();
    showCustomerMessage("Cannot show QR code because booking QR data is missing.", "error");
    return;
  }

  qrSection.style.display = "block";
  qrContainer.innerHTML = "";

  if (qrTitle) {
    qrTitle.textContent =
      action === "UNLOCK" ? "Unlock QR Code" : "Lock / Return QR Code";
  }

  if (qrInstruction) {
    qrInstruction.textContent =
      action === "UNLOCK"
        ? "Show this QR code to the Raspberry Pi camera to unlock your scooter."
        : "Show this QR code to the Raspberry Pi camera to lock/return your scooter.";
  }

  if (typeof QRCode === "undefined") {
    qrContainer.innerHTML = `
      <p class="message error">
        QR library could not be loaded. Please check internet connection or CDN access.
      </p>
    `;
    unlockCodeText.textContent = `QR text: ${qrText}`;
    return;
  }

  new QRCode(qrContainer, {
    text: qrText,
    width: 220,
    height: 220,
    correctLevel: QRCode.CorrectLevel.M
  });

  unlockCodeText.textContent = `QR text: ${qrText}`;
}

function hideBookingQrCode() {
  const qrSection = document.getElementById("booking-qr-section");
  const qrContainer = document.getElementById("booking-qr-code");
  const unlockCodeText = document.getElementById("booking-unlock-code");

  if (qrSection) {
    qrSection.style.display = "none";
  }

  if (qrContainer) {
    qrContainer.innerHTML = "";
  }

  if (unlockCodeText) {
    unlockCodeText.textContent = "";
  }
}

function renderCurrentBooking() {
  const bookingBox = document.getElementById("current-booking-box");

  if (!selectedBooking) {
    bookingBox.className = "empty-state";
    bookingBox.innerHTML = "No active booking selected yet.";
    hideBookingQrCode();
    return;
  }

  const bookingId =
    selectedBooking.id ||
    selectedBooking.booking_id ||
    selectedBooking.bookingId ||
    "Pending";

  const scooterId =
    selectedBooking.scooter_id ||
    selectedBooking.scooterId ||
    selectedBooking.scooter ||
    "-";

  bookingBox.className = "data-card";
  bookingBox.innerHTML = `
    <h3>Booking #${bookingId}</h3>
    <p><strong>Scooter:</strong> ${scooterId}</p>
    <p><strong>Status:</strong> ${selectedBooking.status || "Booked"}</p>
  `;

  showBookingQrCode("UNLOCK", selectedBooking);
}

function getScooterId(scooter) {
  return scooter.id || scooter.scooter_id;
}

function renderScooters(scooters) {
  const scooterList = document.getElementById("scooter-list");

  if (!scooters || scooters.length === 0) {
    scooterList.innerHTML = `
      <div class="empty-state">No available scooters found.</div>
    `;
    return;
  }

  scooterList.innerHTML = scooters.map((scooter) => {
    const scooterId = getScooterId(scooter);
    const isAvailable = scooter.status === "Available";

    return `
      <article class="data-card">
        <h3>${scooterId}</h3>
        <p><strong>Make:</strong> ${scooter.make || "-"}</p>
        <p><strong>Colour:</strong> ${scooter.colour || scooter.color || "-"}</p>
        <p><strong>Location:</strong> ${scooter.location || "-"}</p>
        <p><strong>Cost:</strong> ${formatMoney(scooter.cost_per_minute)} / minute</p>
        <p><span class="badge">${scooter.status || "Unknown"}</span></p>

        <button
          class="primary-button"
          type="button"
          onclick="bookScooter('${scooterId}')"
          ${isAvailable ? "" : "disabled"}
        >
          Book Scooter
        </button>
      </article>
    `;
  }).join("");
}

async function loadAvailableScooters() {
  showCustomerMessage("Loading available scooters...", "success");

  const result = await apiRequest("/api/scooters/available", {
    method: "GET",
    auth: false
  });

  if (!result.success) {
    renderScooters([]);
    showCustomerMessage(
      result.message || "Could not load available scooters.",
      "error"
    );
    return;
  }

  renderScooters(result.data || []);
  showCustomerMessage("Available scooters loaded.", "success");
}

async function bookScooter(scooterId) {
  showCustomerMessage(`Booking scooter ${scooterId}...`, "success");

  const result = await apiRequest("/api/bookings", {
    method: "POST",
    body: {
      scooter_id: scooterId
    }
  });

  if (!result.success) {
    showCustomerMessage(result.message || "Booking failed.", "error");
    return;
  }

  const booking = getBookingFromResponse(result);

  if (!booking || !(booking.id || booking.booking_id)) {
    console.log("Book scooter response:", result);
    showCustomerMessage(
      "Booking succeeded, but booking ID was not returned by backend.",
      "error"
    );
    return;
  }

  selectedBooking = booking;
  document.getElementById("action-scooter-id").value = scooterId;
  document.getElementById("credential-scooter-id").value = scooterId;

  renderCurrentBooking();
  await loadAvailableScooters();

  showCustomerMessage(
    "Scooter booked successfully. You can unlock it with QR or credentials.",
    "success"
  );
}

async function cancelBooking() {
  if (!selectedBooking) {
    showCustomerMessage("No active booking selected to cancel.", "error");
    return;
  }

  const bookingId = selectedBooking.id || selectedBooking.booking_id;

  if (!bookingId) {
    showCustomerMessage("Cannot cancel booking because booking ID is missing.", "error");
    return;
  }

  const result = await apiRequest(`/api/bookings/${bookingId}/cancel`, {
    method: "POST"
  });

  if (!result.success) {
    showCustomerMessage(result.message || "Cancel booking failed.", "error");
    return;
  }

  selectedBooking = null;
  renderCurrentBooking();
  hideBookingQrCode();
  await loadAvailableScooters();

  showCustomerMessage(result.message || "Booking cancelled.", "success");
}

function showUnlockQr() {
  if (!selectedBooking) {
    showCustomerMessage("Please book a scooter first.", "error");
    return;
  }

  showBookingQrCode("UNLOCK", selectedBooking);
  showCustomerMessage("Unlock QR is ready. Scan it with the Raspberry Pi camera.", "success");
}

function showLockQr() {
  if (!selectedBooking) {
    showCustomerMessage("Please book and unlock a scooter first.", "error");
    return;
  }

  showBookingQrCode("LOCK", selectedBooking);
  showCustomerMessage(
    "Lock / Return QR is ready. Scan it with the Raspberry Pi camera, then click the refresh icon beside balance.",
    "success"
  );
}

function getCredentialFormData() {
  return {
    scooterId: document.getElementById("credential-scooter-id").value.trim(),
    username: document.getElementById("credential-username").value.trim(),
    password: document.getElementById("credential-password").value
  };
}

function validateCredentialForm(data) {
  if (!data.scooterId || !data.username || !data.password) {
    showCustomerMessage(
      "Please enter scooter ID, username, and password.",
      "error"
    );
    return false;
  }

  return true;
}

async function credentialUnlockScooter() {
  const formData = getCredentialFormData();

  if (!validateCredentialForm(formData)) {
    return;
  }

  const result = await apiRequest(
    `/api/scooters/${formData.scooterId}/credential-unlock`,
    {
      method: "POST",
      body: {
        username: formData.username,
        password: formData.password
      },
      auth: false
    }
  );

  showCustomerMessage(
    result.message || (result.success ? "Scooter unlocked with credentials." : "Credential unlock failed."),
    result.success ? "success" : "error"
  );

  if (result.success) {
    await loadAvailableScooters();
  }
}

async function credentialLockScooter() {
  const formData = getCredentialFormData();

  if (!validateCredentialForm(formData)) {
    return;
  }

  const result = await apiRequest(
    `/api/scooters/${formData.scooterId}/credential-lock`,
    {
      method: "POST",
      body: {
        username: formData.username,
        password: formData.password
      },
      auth: false
    }
  );

  showCustomerMessage(
    result.message || (result.success ? "Scooter locked with credentials." : "Credential lock failed."),
    result.success ? "success" : "error"
  );

  if (result.success) {
    selectedBooking = null;
    renderCurrentBooking();
    await loadAvailableScooters();
    await refreshCurrentUser(false);
  }
}

async function submitReport(event) {
  event.preventDefault();

  const scooterId = document.getElementById("report-scooter-id").value.trim();
  const issueDescription = document.getElementById("issue-description").value.trim();

  if (!scooterId || !issueDescription) {
    showCustomerMessage("Please enter scooter ID and issue description.", "error");
    return;
  }

  const result = await apiRequest("/api/reports", {
    method: "POST",
    body: {
      scooter_id: scooterId,
      issue_description: issueDescription
    }
  });

  showCustomerMessage(
    result.message || (result.success ? "Issue report submitted." : "Report failed."),
    result.success ? "success" : "error"
  );

  if (result.success) {
    document.getElementById("report-form").reset();
    await loadAvailableScooters();
  }
}

async function handleTopUp(event) {
  event.preventDefault();

  const amountInput = document.getElementById("top-up-amount");
  const messageElement = document.getElementById("top-up-message");

  const amount = Number(amountInput.value);

  if (!amount || amount <= 0) {
    messageElement.textContent = "Please enter a valid top-up amount.";
    messageElement.className = "message error";
    return;
  }

  try {
    messageElement.textContent = "Creating Stripe Checkout session...";
    messageElement.className = "message info";

    const response = await apiRequest("/api/payments/checkout-session", {
      method: "POST",
      body: {
        amount: amount
      }
    });

    const checkoutUrl =
      response.data?.checkout_url ||
      response.checkout_url;

    if (!checkoutUrl) {
      throw new Error(
        response.message || "Stripe Checkout URL was not returned by the backend."
      );
    }

    window.location.href = checkoutUrl;
  } catch (error) {
    messageElement.textContent = error.message || "Could not start Stripe Checkout.";
    messageElement.className = "message error";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  requireRole("customer", "login.html");

  renderCustomerInfo();
  renderCurrentBooking();
  loadAvailableScooters();

  const currentUser = getCurrentUser();
  if (currentUser?.username) {
    document.getElementById("credential-username").value = currentUser.username;
  }

  document.getElementById("refresh-balance-button").addEventListener(
    "click",
    () => refreshCurrentUser(true)
  );

  document.getElementById("refresh-scooters-button").addEventListener(
    "click",
    loadAvailableScooters
  );

  document.getElementById("cancel-booking-button").addEventListener(
    "click",
    cancelBooking
  );

  document.getElementById("unlock-button").addEventListener(
    "click",
    showUnlockQr
  );

  document.getElementById("lock-button").addEventListener(
    "click",
    showLockQr
  );

  document.getElementById("credential-unlock-button").addEventListener(
    "click",
    credentialUnlockScooter
  );

  document.getElementById("credential-lock-button").addEventListener(
    "click",
    credentialLockScooter
  );

  document.getElementById("report-form").addEventListener(
    "submit",
    submitReport
  );

  document.getElementById("top-up-form").addEventListener(
    "submit",
    handleTopUp
  );

  document.getElementById("logout-button").addEventListener("click", () => {
    logoutTo("login.html");
  });
});