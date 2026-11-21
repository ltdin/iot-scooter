const AGENT_SOURCE = "AP";

function showAgentLoginMessage(message, type) {
  const messageBox = document.getElementById("login-message");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;
  messageBox.className = `message ${type}`;
}

function redirectAgentUserByRole(user) {
  if (user.role === "customer") {
    window.location.href = "customer.html";
    return;
  }

  if (user.role === "engineer") {
    window.location.href = "engineer.html";
    return;
  }

  clearAuthData();
  showAgentLoginMessage(
    "This account is not allowed to log in from Agent Pi.",
    "error"
  );
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("agent-login-form");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
      showAgentLoginMessage("Please enter both username and password.", "error");
      return;
    }

    showAgentLoginMessage("Logging in...", "success");

    try {
      const result = await loginUser(username, password, AGENT_SOURCE);

      console.log("Agent login result:", result);

      if (!result || !result.success) {
        showAgentLoginMessage(result?.message || "Login failed.", "error");
        return;
      }

      const authData = result.data || result.raw?.data;

      if (!authData || !authData.access_token || !authData.user) {
        console.log("Invalid login response:", result);
        showAgentLoginMessage("Invalid login response from server.", "error");
        return;
      }

      const user = authData.user;

      if (!user || !user.role || !user.id) {
        console.log("Invalid user object:", user);
        showAgentLoginMessage("Invalid user data from server.", "error");
        return;
      }

      saveAuthData(authData);
      redirectAgentUserByRole(user);
    } catch (error) {
      console.error("Agent login error:", error);
      showAgentLoginMessage(error.message || "Login failed due to a frontend error.", "error");
    }
  });
});

function showRegisterMessage(message, type) {
  const messageBox = document.getElementById("register-message");

  if (!messageBox) {
    return;
  }

  messageBox.textContent = message;
  messageBox.className = `message ${type}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.getElementById("register-form");

  if (!registerForm) {
    return;
  }

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const customerData = {
      username: document.getElementById("username").value.trim(),
      password: document.getElementById("password").value,
      first_name: document.getElementById("first_name").value.trim(),
      last_name: document.getElementById("last_name").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      email: document.getElementById("email").value.trim()
    };

    if (
      !customerData.username ||
      !customerData.password ||
      !customerData.first_name ||
      !customerData.last_name ||
      !customerData.phone ||
      !customerData.email
    ) {
      showRegisterMessage("Please fill in all required fields.", "error");
      return;
    }

    showRegisterMessage("Creating customer account...", "success");

    try {
      const result = await registerCustomer(customerData);

      console.log("Agent register result:", result);

      if (!result || !result.success) {
        showRegisterMessage(result?.message || "Registration failed.", "error");
        return;
      }

      showRegisterMessage(
        "Registration successful. Redirecting to login page...",
        "success"
      );

      setTimeout(() => {
        window.location.href = "login.html";
      }, 1200);
    } catch (error) {
      console.error("Agent register error:", error);
      showRegisterMessage(error.message || "Registration failed due to a frontend error.", "error");
    }
  });
});