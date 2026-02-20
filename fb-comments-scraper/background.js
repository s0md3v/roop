// FB Comments Scraper - Background Service Worker
// Minimal background; main logic lives in content.js

chrome.runtime.onInstalled.addListener(() => {
  console.log('[FB-Scraper] Extension installed.');
});
