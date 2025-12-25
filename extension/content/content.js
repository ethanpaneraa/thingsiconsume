const browser = window.browser || window.chrome;

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "getPageInfo") {
    const pageInfo = getPageInfo();
    sendResponse({ success: true, data: pageInfo });
    return true;
  }
});

function getPageInfo() {
  const info = {
    url: window.location.href,
    title: document.title,
    isVideo: false,
    videoTitle: null,
    videoUrl: null,
  };

  const videoDetection = detectVideoPage();
  if (videoDetection.isVideo) {
    info.isVideo = true;
    info.title = videoDetection.title || info.title;
    info.videoUrl = videoDetection.url || info.url;
  }

  return info;
}

function detectVideoPage() {
  const result = {
    isVideo: false,
    title: null,
    url: null,
  };

  const hostname = window.location.hostname;
  const url = window.location.href;

  if (hostname.includes("youtube.com") || hostname.includes("youtu.be")) {
    result.isVideo = true;

    const h1Title = document.querySelector(
      "h1.ytd-video-primary-info-renderer"
    );
    const ytTitle = document.querySelector("h1.title yt-formatted-string");
    const metaTitle = document.querySelector('meta[name="title"]');

    if (h1Title) {
      result.title = h1Title.textContent.trim();
    } else if (ytTitle) {
      result.title = ytTitle.textContent.trim();
    } else if (metaTitle) {
      result.title = metaTitle.content;
    }

    result.url = url;
  } else if (hostname.includes("vimeo.com")) {
    result.isVideo = true;

    const vimeoTitle = document.querySelector("h1.title");
    const metaTitle = document.querySelector('meta[property="og:title"]');

    if (vimeoTitle) {
      result.title = vimeoTitle.textContent.trim();
    } else if (metaTitle) {
      result.title = metaTitle.content;
    }

    result.url = url;
  } else if (hostname.includes("twitch.tv")) {
    result.isVideo = true;

    const twitchTitle = document.querySelector(
      'h2[data-a-target="stream-title"]'
    );
    const metaTitle = document.querySelector('meta[property="og:title"]');

    if (twitchTitle) {
      result.title = twitchTitle.textContent.trim();
    } else if (metaTitle) {
      result.title = metaTitle.content;
    }

    result.url = url;
  } else if (hostname.includes("netflix.com")) {
    result.isVideo = true;

    const netflixTitle = document.querySelector(".video-title");
    const metaTitle = document.querySelector('meta[property="og:title"]');

    if (netflixTitle) {
      result.title = netflixTitle.textContent.trim();
    } else if (metaTitle) {
      result.title = metaTitle.content;
    }

    result.url = url;
  } else {
    const hasVideoTag = document.querySelector("video");
    const hasVideoPlayer = document.querySelector(
      '[class*="video-player"], [id*="video-player"], [class*="player"], [id*="player"]'
    );

    if (hasVideoTag || hasVideoPlayer) {
      result.isVideo = true;

      const ogTitle = document.querySelector('meta[property="og:title"]');
      const twitterTitle = document.querySelector('meta[name="twitter:title"]');

      if (ogTitle) {
        result.title = ogTitle.content;
      } else if (twitterTitle) {
        result.title = twitterTitle.content;
      }

      result.url = url;
    }
  }

  return result;
}
