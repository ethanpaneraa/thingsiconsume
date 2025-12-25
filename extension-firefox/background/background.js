// Background script for What I Consumed extension
// Handles API communication

// Get browser API (works for both Chrome and Firefox)
const browser = window.browser || window.chrome;

// Listen for messages from popup or content scripts
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "createEvent") {
    handleCreateEvent(message.data, message.config)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true; // Keep message channel open for async response
  }

  if (message.action === "testConnection") {
    testConnection(message.config)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

// Create event via API
async function handleCreateEvent(eventData, config) {
  console.log("handleCreateEvent called with:", { eventData, config });
  try {
    const apiUrl = config.apiUrl.replace(/\/$/, ""); // Remove trailing slash
    const endpoint = `${apiUrl}/v1/events`;

    console.log("Making request to:", endpoint);
    console.log("Request body:", JSON.stringify(eventData));
    console.log(
      "API Key:",
      config.apiKey ? "***" + config.apiKey.slice(-4) : "MISSING"
    );

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": config.apiKey,
      },
      body: JSON.stringify(eventData),
    });

    console.log("Response status:", response.status);
    console.log("Response headers:", response.headers);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response body:", errorText);
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = { detail: errorText };
      }
      throw new Error(
        errorData.detail ||
          `API error: ${response.status} ${response.statusText}`
      );
    }

    const result = await response.json();
    console.log("Success! Result:", result);

    return {
      success: true,
      data: result,
    };
  } catch (error) {
    console.error("Error creating event:", error);
    return {
      success: false,
      error: error.message || "Failed to create event",
    };
  }
}

// Test API connection
async function testConnection(config) {
  try {
    const apiUrl = config.apiUrl.replace(/\/$/, "");
    const endpoint = `${apiUrl}/health`;

    const response = await fetch(endpoint, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    const result = await response.json();

    if (result.status === "ok") {
      return {
        success: true,
        message: "Connection successful",
      };
    } else {
      throw new Error("Unexpected health check response");
    }
  } catch (error) {
    console.error("Connection test failed:", error);
    return {
      success: false,
      error: error.message || "Connection failed",
    };
  }
}

// Log when extension is installed or updated
browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("What I Consumed extension installed");
    // Open options in a popup window on first install
    browser.windows.create({
      url: browser.runtime.getURL("options/options.html"),
      type: "popup",
      width: 500,
      height: 400,
    });
  } else if (details.reason === "update") {
    console.log("What I Consumed extension updated");
  }
});
