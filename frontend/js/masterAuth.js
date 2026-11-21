const MASTER_SOURCE = "MP";

function showMasterLoginMessage(message, type) {
  const messageBox = document.getElementById("master-login-message");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;
  messageBox.className = `message ${type}`;
}

function redirectMasterUserByRole(user) {
  if (user.role === "admin") {
    window.location.href = "admin.html";
    return;
  }

  clearAuthData();
  showMasterLoginMessage(
    "This account is not allowed to log in from Master Pi.",
    "error"
  );
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("master-login-form");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
      showMasterLoginMessage("Please enter both username and password.", "error");
      return;
    }

    showMasterLoginMessage("Logging in as admin...", "success");

    const result = await loginUser(username, password, MASTER_SOURCE);

    if (!result.success) {
      showMasterLoginMessage(result.message || "Login failed.", "error");
      return;
    }

    const authData = result.data;
    const user = authData.user;

    if (!user || !user.role || !user.id) {
      showMasterLoginMessage("Invalid login response from server.", "error");
      return;
    }

    if (user.role !== "admin") {
      clearAuthData();
      showMasterLoginMessage(
        "Only admin accounts can access the Master Pi dashboard.",
        "error"
      );
      return;
    }

    saveAuthData(authData);
    redirectMasterUserByRole(user);
  });
});