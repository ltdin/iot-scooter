async function loginUser(username, password, source) {
  return apiRequest("/api/login", {
    method: "POST",
    auth: false,
    body: {
      username,
      password,
      source
    }
  });
}

async function registerCustomer(customerData) {
  return apiRequest("/api/register", {
    method: "POST",
    auth: false,
    body: customerData
  });
}

function saveAuthData(authData) {
  localStorage.setItem(getAuthStorageKey(), JSON.stringify(authData));
}

function saveCurrentUser(user) {
  const currentAuth = getStoredAuth() || {};
  saveAuthData({
    ...currentAuth,
    user
  });
}

function getCurrentUser() {
  return getStoredUser();
}

function getCurrentRole() {
  const user = getCurrentUser();
  return user ? user.role : null;
}

function isLoggedIn() {
  return Boolean(getCurrentUser() && getStoredToken());
}

function clearAuthData() {
  localStorage.removeItem(getAuthStorageKey());
}

async function logoutTo(loginPagePath) {
  await apiRequest("/api/logout", {
    method: "POST"
  });

  clearAuthData();
  window.location.href = loginPagePath;
}

function requireRole(allowedRoles, loginPagePath) {
  const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
  const user = getCurrentUser();

  if (!user || !roles.includes(user.role)) {
    alert("You are not allowed to access this page. Please log in again.");
    clearAuthData();
    window.location.href = loginPagePath;
  }
}