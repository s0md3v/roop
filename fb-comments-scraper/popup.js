// FB Comments Scraper - Popup Script

const $ = id => document.getElementById(id);

const btnProbe   = $('btn-probe');
const btnScrape  = $('btn-scrape');
const btnExport  = $('btn-export');
const optScroll  = $('opt-autoscroll');
const optDebug   = $('opt-debug');
const statusBox  = $('status-box');
const debugBox   = $('debug-box');
const debugOut   = $('debug-output');
const previewBox = $('preview-box');
const previewCnt = $('preview-count');
const previewBody= $('preview-body');

// ─── Helpers ─────────────────────────────────────────────────────────────────

function showStatus(msg, type = 'info') {
  statusBox.textContent = msg;
  statusBox.className = 'status ' + (type === 'error' ? 'error' : type === 'success' ? 'success' : '');
  statusBox.classList.remove('hidden');
}

function hideStatus() {
  statusBox.classList.add('hidden');
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function isFacebookTab(tab) {
  return tab && tab.url && tab.url.includes('facebook.com');
}

function ensureContentScript(tabId) {
  return chrome.scripting.executeScript({
    target: { tabId },
    files: ['content.js'],
  }).catch(() => {}); // ignore if already injected
}

// ─── Probe ────────────────────────────────────────────────────────────────────

btnProbe.addEventListener('click', async () => {
  const tab = await getActiveTab();
  if (!isFacebookTab(tab)) {
    showStatus('Navigate to a Facebook post first!', 'error');
    return;
  }

  btnProbe.disabled = true;
  showStatus('Probing page...');

  await ensureContentScript(tab.id);

  chrome.tabs.sendMessage(tab.id, { action: 'probe' }, info => {
    btnProbe.disabled = false;
    if (chrome.runtime.lastError) {
      showStatus('Could not reach content script: ' + chrome.runtime.lastError.message, 'error');
      return;
    }
    hideStatus();
    debugBox.classList.remove('hidden');
    debugOut.textContent = JSON.stringify(info, null, 2);
  });
});

// ─── Scrape ───────────────────────────────────────────────────────────────────

btnScrape.addEventListener('click', async () => {
  const tab = await getActiveTab();
  if (!isFacebookTab(tab)) {
    showStatus('Navigate to a Facebook post first!', 'error');
    return;
  }

  btnScrape.disabled = true;
  btnExport.disabled = true;
  debugBox.classList.add('hidden');
  previewBox.classList.add('hidden');
  showStatus('Injecting scraper...');

  await ensureContentScript(tab.id);

  const options = {
    autoScroll: optScroll.checked,
    debug: optDebug.checked,
  };

  // Listen for live status updates from content script
  const statusListener = msg => {
    if (msg.action === 'status') {
      showStatus(msg.text);
    }
  };
  chrome.runtime.onMessage.addListener(statusListener);

  chrome.tabs.sendMessage(tab.id, { action: 'scrape', options }, result => {
    chrome.runtime.onMessage.removeListener(statusListener);
    btnScrape.disabled = false;

    if (chrome.runtime.lastError) {
      showStatus('Error: ' + chrome.runtime.lastError.message, 'error');
      return;
    }

    if (!result || result.error) {
      showStatus('Scrape failed: ' + (result?.error || 'unknown error'), 'error');
      return;
    }

    showStatus(`Scraped ${result.count} comments!`, 'success');
    btnExport.disabled = false;
    renderPreview(result.comments);
  });
});

// ─── Export CSV ───────────────────────────────────────────────────────────────

btnExport.addEventListener('click', async () => {
  const tab = await getActiveTab();
  if (!isFacebookTab(tab)) {
    showStatus('No Facebook tab found!', 'error');
    return;
  }

  const postId = extractPostId(tab.url);
  const filename = `fb_comments_${postId || Date.now()}.csv`;

  chrome.tabs.sendMessage(tab.id, { action: 'download', filename }, result => {
    if (chrome.runtime.lastError) {
      showStatus('Export error: ' + chrome.runtime.lastError.message, 'error');
      return;
    }
    if (result?.error) {
      showStatus('Export error: ' + result.error, 'error');
      return;
    }
    showStatus(`Exported ${result.count} comments to ${filename}`, 'success');
  });
});

function extractPostId(url) {
  if (!url) return '';
  const m = url.match(/\/posts\/(\d+)/) ||
            url.match(/\?fbid=(\d+)/) ||
            url.match(/\/(\d{10,})/);
  return m ? m[1] : '';
}

// ─── Preview Table ────────────────────────────────────────────────────────────

function renderPreview(comments) {
  previewBody.innerHTML = '';
  if (!comments || comments.length === 0) return;

  previewCnt.textContent = `(${comments.length})`;

  const max = Math.min(comments.length, 50);
  const frag = document.createDocumentFragment();
  for (let i = 0; i < max; i++) {
    const c = comments[i];
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td title="${esc(c.author)}">${esc(c.author)}</td>
      <td title="${esc(c.text)}">${esc(c.text.slice(0, 60))}${c.text.length > 60 ? '…' : ''}</td>
      <td title="${esc(c.timestamp)}">${esc(c.timestamp)}</td>
      <td>${esc(c.likes)}</td>
    `;
    frag.appendChild(tr);
  }
  previewBody.appendChild(frag);

  if (comments.length > 50) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="4" style="text-align:center;color:#65676b">… and ${comments.length - 50} more</td>`;
    previewBody.appendChild(tr);
  }

  previewBox.classList.remove('hidden');
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
