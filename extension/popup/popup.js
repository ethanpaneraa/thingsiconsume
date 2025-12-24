// Popup script for What I Consumed extension

// Get browser API (works for both Chrome and Firefox)
const browser = window.browser || window.chrome;

// DOM elements
let eventForm;
let statusMessage;
let submitBtn;
let titleInput;
let urlInput;
let eventTypeSelect;

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", async () => {
  // Get DOM elements
  eventForm = document.getElementById("event-form");
  statusMessage = document.getElementById("status-message");
  submitBtn = document.getElementById("submit-btn");
  titleInput = document.getElementById("title");
  urlInput = document.getElementById("url");
  eventTypeSelect = document.getElementById("event-type");

  const settingsLink = document.getElementById("settings-link");

  // Check if API is configured
  const config = await getConfig();
  if (!config.apiKey) {
    showStatus("Please configure API key in settings first", "error");
    submitBtn.disabled = true;
  }

  // Auto-fill from current page on load
  await autoFillFromPage();

  // Event listeners
  eventForm.addEventListener("submit", handleSubmit);

  if (settingsLink) {
    settingsLink.addEventListener("click", async (e) => {
      e.preventDefault();
      console.log("Settings link clicked");

      try {
        // Open settings in a small popup window
        const currentWindow = await browser.windows.getCurrent();
        console.log("Current window:", currentWindow);

        const left = Math.round(
          currentWindow.left + (currentWindow.width - 500) / 2
        );
        const top = Math.round(
          currentWindow.top + (currentWindow.height - 400) / 2
        );

        console.log("Creating settings window at:", { left, top });

        await browser.windows.create({
          url: browser.runtime.getURL("options/options.html"),
          type: "popup",
          width: 500,
          height: 400,
          left: left,
          top: top,
        });

        console.log("Settings window created, closing popup");
        // Close the current popup
        window.close();
      } catch (error) {
        console.error("Error opening settings:", error);
        showStatus("Could not open settings: " + error.message, "error");
      }
    });
  } else {
    console.error("Settings link not found!");
  }
});

// Get configuration from storage
async function getConfig() {
  try {
    const result = await browser.storage.sync.get(["apiKey"]);
    console.log("Storage result:", result);
    return {
      apiUrl: "https://thingsiconsume-production.up.railway.app",
      apiKey: (result && result.apiKey) || "",
    };
  } catch (error) {
    console.error("Error getting config:", error);
    return {
      apiUrl: "https://thingsiconsume-production.up.railway.app",
      apiKey: "",
    };
  }
}

// Auto-fill form from current page
async function autoFillFromPage() {
  console.log("autoFillFromPage called");
  try {
    // Query for active tab
    const tabs = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });
    console.log("Tabs query result:", tabs);

    const tab = tabs[0];

    if (!tab) {
      console.log("No active tab found");
      return;
    }

    console.log("Active tab:", { url: tab.url, title: tab.title, id: tab.id });

    // Always set basic tab info first as fallback
    if (
      tab.url &&
      !tab.url.startsWith("about:") &&
      !tab.url.startsWith("chrome:") &&
      !tab.url.startsWith("moz-extension:")
    ) {
      console.log("Setting URL to:", tab.url);
      urlInput.value = tab.url;
    } else {
      console.log("Skipping URL (internal page):", tab.url);
    }

    if (tab.title) {
      console.log("Setting title to:", tab.title);
      titleInput.value = tab.title;
    }

    // Try to get enhanced info from content script
    try {
      console.log("Attempting to send message to content script...");
      const response = await browser.tabs.sendMessage(tab.id, {
        action: "getPageInfo",
      });
      console.log("Content script response:", response);

      if (response && response.success) {
        const info = response.data;
        console.log("Got page info from content script:", info);

        // Set URL (prefer content script data)
        if (info.url) {
          urlInput.value = info.url;
        }

        // Set title (prefer content script data)
        if (info.title) {
          titleInput.value = info.title;
        }

        // Detect video content and set type
        if (info.isVideo) {
          eventTypeSelect.value = "video";
        } else {
          eventTypeSelect.value = "link";
        }
      }
    } catch (contentScriptError) {
      console.log(
        "Content script not available, using basic tab info:",
        contentScriptError
      );
      // Fallback already set above
    }
  } catch (error) {
    console.error("Error auto-filling:", error);
  }
}

// Handle form submission
async function handleSubmit(e) {
  e.preventDefault();

  const formData = new FormData(eventForm);
  const type = formData.get("type");
  const title = formData.get("title");
  const url = formData.get("url");

  if (!title) {
    showStatus("Title is required", "error");
    return;
  }

  // Show loading state
  setLoading(true);
  hideStatus();

  try {
    const config = await getConfig();

    if (!config.apiKey) {
      throw new Error("API key not configured. Please check settings.");
    }

    // Prepare event data
    const eventData = {
      occurred_at: new Date().toISOString(),
      type: type,
      title: title,
      url: url || undefined,
      payload: {},
    };

    console.log("Submitting event:", eventData);

    // Send to background script to make API call
    const response = await sendMessageToBackground({
      action: "createEvent",
      data: eventData,
      config: config,
    });

    if (response.success) {
      showStatus("Event saved successfully!", "success");

      // Clear form after short delay
      setTimeout(() => {
        eventForm.reset();
        autoFillFromPage();
      }, 1500);
    } else {
      throw new Error(response.error || "Failed to save event");
    }
  } catch (error) {
    console.error("Error creating event:", error);
    showStatus(error.message || "Failed to save event", "error");
  } finally {
    setLoading(false);
  }
}

// Send message to background script
function sendMessageToBackground(message) {
  return new Promise((resolve) => {
    browser.runtime.sendMessage(message, (response) => {
      resolve(response || { success: false, error: "No response" });
    });
  });
}

// Show status message
function showStatus(message, type) {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
  statusMessage.classList.remove("hidden");
}

// Hide status message
function hideStatus() {
  statusMessage.classList.add("hidden");
}

// Set loading state
function setLoading(loading) {
  const btnText = submitBtn.querySelector(".btn-text");
  const btnLoader = submitBtn.querySelector(".btn-loader");

  if (loading) {
    submitBtn.disabled = true;
    btnText.classList.add("hidden");
    btnLoader.classList.remove("hidden");
    btnLoader.classList.add("active");
  } else {
    submitBtn.disabled = false;
    btnText.classList.remove("hidden");
    btnLoader.classList.add("hidden");
    btnLoader.classList.remove("active");
  }
}
