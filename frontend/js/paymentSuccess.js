document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.getElementById("payment-status");
  const params = new URLSearchParams(window.location.search);
  const sessionId = params.get("session_id");

  if (!sessionId) {
    statusElement.textContent = "Missing Stripe session ID.";
    return;
  }

  try {
    statusElement.textContent = "Confirming payment with backend...";

    const response = await apiRequest("/api/payments/checkout-session/confirm", {
      method: "POST",
      body: {
        session_id: sessionId
      }
    });

    const updatedUser = response.data?.user;
    const transaction = response.data?.transaction;

    if (updatedUser) {
      const authData = getStoredAuth() || {};

      authData.user = {
        ...authData.user,
        ...updatedUser
      };

      saveAuthData(authData);
    }

    statusElement.textContent =
      `Payment successful. Top-up $${transaction?.amount || ""} applied. Returning to dashboard...`;

    setTimeout(() => {
      window.location.href = "customer.html";
    }, 1500);
  } catch (error) {
    statusElement.textContent =
      error.message || "Could not confirm Stripe payment.";
  }
});