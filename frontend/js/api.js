function getPortalType() {
  const path = window.location.pathname;

  if (path.includes("/master/")) {
    return "master";
  }

  if (path.includes("/agent/")) {
    return "agent";
  }

  return "public";
}

function getAuthStorageKey() {
  const portalType = getPortalType();

  if (portalType === "master") {
    return "master_auth_data";
  }

  if (portalType === "agent") {
    return "agent_auth_data";
  }

  return "auth_data";
}

function getBaseUrl() {
  const portalType = getPortalType();

  if (portalType === "agent") {
    return API_CONFIG.AGENT_BASE_URL;
  }

  return API_CONFIG.MASTER_BASE_URL;
}

function normalizeEndpoint(endpoint) {
  const portalType = getPortalType();

  if (portalType === "agent" && endpoint.startsWith("/api/")) {
    return endpoint.replace("/api/", "/agent/");
  }

  return endpoint;
}

function getStoredAuth() {
  const authText = localStorage.getItem(getAuthStorageKey());

  if (!authText) {
    return null;
  }

  try {
    return JSON.parse(authText);
  } catch (error) {
    return null;
  }
}

function getStoredUser() {
  const auth = getStoredAuth();
  return auth ? auth.user : null;
}

function getStoredToken() {
  const auth = getStoredAuth();
  return auth ? auth.access_token : null;
}

async function apiRequest(endpoint, options = {}) {
  const normalizedEndpoint = normalizeEndpoint(endpoint);
  const url = `${getBaseUrl()}${normalizedEndpoint}`;

  const headers = {
    ...(options.headers || {})
  };

  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const token = getStoredToken();

  if (token && options.auth !== false) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined
    });

    let responseData = null;

    try {
      responseData = await response.json();
    } catch (error) {
      responseData = {
        success: false,
        message: "Server did not return JSON.",
        data: null
      };
    }

    return {
      ok: response.ok,
      status: response.status,
      success: Boolean(responseData.success),
      message: responseData.message || "",
      data: responseData.data,
      raw: responseData
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      success: false,
      message: "Cannot connect to backend server. Please check whether Flask API is running.",
      data: null,
      raw: null
    };
  }
}