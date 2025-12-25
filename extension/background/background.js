const browser = window.browser || window.chrome;

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "createEvent") {
    handleCreateEvent(message.data, message.config)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (message.action === "testConnection") {
    testConnection(message.config)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

async function handleCreateEvent(eventData, config) {
  try {
    const apiUrl = config.apiUrl.replace(/\/$/, "");
    const endpoint = `${apiUrl}/v1/events`;

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": config.apiKey,
      },
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      const errorText = await response.text();
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

    return {
      success: true,
      data: result,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || "Failed to create event",
    };
  }
}

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
    return {
      success: false,
      error: error.message || "Connection failed",
    };
  }
}

browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    browser.windows.create({
      url: browser.runtime.getURL("options/options.html"),
      type: "popup",
      width: 500,
      height: 400,
    });
  }
});
