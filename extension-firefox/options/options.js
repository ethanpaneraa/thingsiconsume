const browser = window.browser || window.chrome;

let settingsForm;
let statusMessage;
let apiUrlInput;
let apiKeyInput;
let saveBtn;
let testConnectionBtn;
let toggleKeyVisibilityBtn;

document.addEventListener("DOMContentLoaded", async () => {
  settingsForm = document.getElementById("settings-form");
  statusMessage = document.getElementById("status-message");
  apiUrlInput = document.getElementById("api-url");
  apiKeyInput = document.getElementById("api-key");
  saveBtn = document.getElementById("save-btn");
  testConnectionBtn = document.getElementById("test-connection-btn");
  toggleKeyVisibilityBtn = document.getElementById("toggle-key-visibility");

  await loadSettings();

  settingsForm.addEventListener("submit", handleSave);
  testConnectionBtn.addEventListener("click", handleTestConnection);
  toggleKeyVisibilityBtn.addEventListener("click", toggleKeyVisibility);
});

async function loadSettings() {
  try {
    const result = await browser.storage.sync.get(["apiKey"]);

    apiUrlInput.value = "https://thingsiconsume-production.up.railway.app";

    if (result && result.apiKey) {
      apiKeyInput.value = result.apiKey;
    }
  } catch (error) {}
}

async function handleSave(e) {
  e.preventDefault();

  const apiKey = apiKeyInput.value.trim();

  if (!apiKey) {
    showStatus("Please enter your API key", "error");
    return;
  }

  try {
    await browser.storage.sync.set({ apiKey });
    showStatus("Settings saved successfully!", "success");
  } catch (error) {
    showStatus("Failed to save settings: " + error.message, "error");
  }
}

async function handleTestConnection() {
  const apiUrl = "https://thingsiconsume-production.up.railway.app";
  const apiKey = apiKeyInput.value.trim();

  if (!apiKey) {
    showStatus("Please enter your API key before testing", "error");
    return;
  }

  testConnectionBtn.disabled = true;
  testConnectionBtn.textContent = "Testing...";
  showStatus("Testing connection...", "info");

  try {
    const response = await sendMessageToBackground({
      action: "testConnection",
      config: { apiUrl, apiKey },
    });

    if (response.success) {
      showStatus("✓ Connection successful! API is reachable.", "success");
    } else {
      showStatus(`✗ Connection failed: ${response.error}`, "error");
    }
  } catch (error) {
    showStatus("✗ Connection test failed", "error");
  } finally {
    testConnectionBtn.disabled = false;
    testConnectionBtn.textContent = "Test Connection";
  }
}

function toggleKeyVisibility() {
  if (apiKeyInput.type === "password") {
    apiKeyInput.type = "text";
    toggleKeyVisibilityBtn.textContent = "Hide";
  } else {
    apiKeyInput.type = "password";
    toggleKeyVisibilityBtn.textContent = "Show";
  }
}

function sendMessageToBackground(message) {
  return new Promise((resolve) => {
    browser.runtime.sendMessage(message, (response) => {
      resolve(response || { success: false, error: "No response" });
    });
  });
}

function showStatus(message, type) {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
  statusMessage.classList.remove("hidden");

  if (type === "success") {
    setTimeout(() => {
      statusMessage.classList.add("hidden");
    }, 3000);
  }
}
