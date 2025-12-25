const browser = window.browser || window.chrome;

let eventForm;
let statusMessage;
let submitBtn;
let titleInput;
let urlInput;
let eventTypeSelect;

document.addEventListener("DOMContentLoaded", async () => {
  eventForm = document.getElementById("event-form");
  statusMessage = document.getElementById("status-message");
  submitBtn = document.getElementById("submit-btn");
  titleInput = document.getElementById("title");
  urlInput = document.getElementById("url");
  eventTypeSelect = document.getElementById("event-type");

  const settingsLink = document.getElementById("settings-link");

  const config = await getConfig();
  if (!config.apiKey) {
    showStatus("Please configure API key in settings first", "error");
    submitBtn.disabled = true;
  }

  await autoFillFromPage();

  eventForm.addEventListener("submit", handleSubmit);

  if (settingsLink) {
    settingsLink.addEventListener("click", async (e) => {
      e.preventDefault();

      try {
        const currentWindow = await browser.windows.getCurrent();

        const left = Math.round(
          currentWindow.left + (currentWindow.width - 500) / 2
        );
        const top = Math.round(
          currentWindow.top + (currentWindow.height - 400) / 2
        );

        await browser.windows.create({
          url: browser.runtime.getURL("options/options.html"),
          type: "popup",
          width: 500,
          height: 400,
          left: left,
          top: top,
        });

        window.close();
      } catch (error) {
        showStatus("Could not open settings: " + error.message, "error");
      }
    });
  }
});

async function getConfig() {
  try {
    const result = await browser.storage.sync.get(["apiKey"]);
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

async function autoFillFromPage() {
  try {
    const tabs = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });

    const tab = tabs[0];

    if (!tab) {
      return;
    }

    if (
      tab.url &&
      !tab.url.startsWith("about:") &&
      !tab.url.startsWith("chrome:") &&
      !tab.url.startsWith("moz-extension:")
    ) {
      urlInput.value = tab.url;
    }

    if (tab.title) {
      titleInput.value = tab.title;
    }

    try {
      const response = await browser.tabs.sendMessage(tab.id, {
        action: "getPageInfo",
      });

      if (response && response.success) {
        const info = response.data;

        if (info.url) {
          urlInput.value = info.url;
        }

        if (info.title) {
          titleInput.value = info.title;
        }

        if (info.isVideo) {
          eventTypeSelect.value = "video";
        } else {
          eventTypeSelect.value = "link";
        }
      }
    } catch (contentScriptError) {}
  } catch (error) {}
}

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

  setLoading(true);
  hideStatus();

  try {
    const config = await getConfig();

    if (!config.apiKey) {
      throw new Error("API key not configured. Please check settings.");
    }

    const eventData = {
      occurred_at: new Date().toISOString(),
      type: type,
      title: title,
      url: url || undefined,
      payload: {},
    };

    const response = await sendMessageToBackground({
      action: "createEvent",
      data: eventData,
      config: config,
    });

    if (response.success) {
      showStatus("Event saved successfully!", "success");

      setTimeout(() => {
        eventForm.reset();
        autoFillFromPage();
      }, 1500);
    } else {
      throw new Error(response.error || "Failed to save event");
    }
  } catch (error) {
    showStatus(error.message || "Failed to save event", "error");
  } finally {
    setLoading(false);
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
}

function hideStatus() {
  statusMessage.classList.add("hidden");
}

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
