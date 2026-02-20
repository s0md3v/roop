// FB Comments Scraper – Popup Script v2

const $ = id => document.getElementById(id);

const btnProbe   = $('btn-probe');
const btnScrape  = $('btn-scrape');
const btnExport  = $('btn-export');
const optScroll  = $('opt-autoscroll');
const optDebug   = $('opt-debug');
const statusBox  = $('status-box');
const metaPanel  = $('meta-panel');
const metaBody   = $('meta-body');
const reactionBar  = $('reaction-bar');
const reactionChips= $('reaction-chips');
const previewBox = $('preview-box');
const previewCnt = $('preview-count');
const previewBody= $('preview-body');
const debugBox   = $('debug-box');
const debugOut   = $('debug-output');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function showStatus(msg, type = 'info') {
  statusBox.textContent = msg;
  statusBox.className = 'status ' + (type === 'error' ? 'error' : type === 'success' ? 'success' : '');
  statusBox.classList.remove('hidden');
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function isFB(tab) { return tab?.url?.includes('facebook.com'); }

async function ensureContentScript(tabId) {
  await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] }).catch(() => {});
}

// ─── Probe ────────────────────────────────────────────────────────────────────

btnProbe.addEventListener('click', async () => {
  const tab = await getActiveTab();
  if (!isFB(tab)) { showStatus('Navigate to a Facebook post first!', 'error'); return; }
  btnProbe.disabled = true;
  showStatus('Probing…');
  await ensureContentScript(tab.id);
  chrome.tabs.sendMessage(tab.id, { action: 'probe' }, info => {
    btnProbe.disabled = false;
    if (chrome.runtime.lastError) { showStatus(chrome.runtime.lastError.message, 'error'); return; }
    statusBox.classList.add('hidden');
    debugBox.classList.remove('hidden');
    debugOut.textContent = JSON.stringify(info, null, 2);
  });
});

// ─── Scrape ───────────────────────────────────────────────────────────────────

btnScrape.addEventListener('click', async () => {
  const tab = await getActiveTab();
  if (!isFB(tab)) { showStatus('Navigate to a Facebook post first!', 'error'); return; }

  btnScrape.disabled = true;
  btnExport.disabled = true;
  metaPanel.classList.add('hidden');
  reactionBar.classList.add('hidden');
  previewBox.classList.add('hidden');
  debugBox.classList.add('hidden');
  showStatus('Injecting scraper…');

  await ensureContentScript(tab.id);

  const options = { autoScroll: optScroll.checked, debug: optDebug.checked };

  const statusListener = msg => { if (msg.action === 'status') showStatus(msg.text); };
  chrome.runtime.onMessage.addListener(statusListener);

  chrome.tabs.sendMessage(tab.id, { action: 'scrape', options }, result => {
    chrome.runtime.onMessage.removeListener(statusListener);
    btnScrape.disabled = false;

    if (chrome.runtime.lastError) { showStatus(chrome.runtime.lastError.message, 'error'); return; }
    if (!result || result.error)  { showStatus('Error: ' + (result?.error || 'unknown'), 'error'); return; }

    showStatus(`Scraped ${result.count} comments!`, 'success');
    btnExport.disabled = false;

    if (result.postMeta) renderMeta(result.postMeta);
    if (result.comments)  renderPreview(result.comments);
  });
});

// ─── Export ───────────────────────────────────────────────────────────────────

btnExport.addEventListener('click', async () => {
  const tab = await getActiveTab();
  if (!isFB(tab)) { showStatus('No Facebook tab!', 'error'); return; }
  const filename = `fb_comments_${extractPostId(tab.url) || Date.now()}.csv`;
  chrome.tabs.sendMessage(tab.id, { action: 'download', filename }, result => {
    if (chrome.runtime.lastError) { showStatus(chrome.runtime.lastError.message, 'error'); return; }
    if (result?.error)            { showStatus(result.error, 'error'); return; }
    showStatus(`Exported ${result.count} rows → ${filename}`, 'success');
  });
});

function extractPostId(url) {
  if (!url) return '';
  const m = url.match(/\/posts\/(\d+)/) || url.match(/\?fbid=(\d+)/) || url.match(/\/(\d{10,})/);
  return m ? m[1] : '';
}

// ─── Render Post Meta ─────────────────────────────────────────────────────────

const REACTION_EMOJI = {
  like: '👍', love: '❤️', care: '🤗', haha: '😂', wow: '😮', sad: '😢', angry: '😡',
};

const META_LABELS = {
  scrape_date:             'Scraped at',
  post_url:                'Post URL',
  post_date:               'Post date',
  post_type:               'Type',
  video_duration:          'Video length',
  post_text_preview:       'Post text',
  reactions_total:         'Total reactions',
  total_comments_scraped:  'Comments scraped',
};

function renderMeta(meta) {
  metaBody.innerHTML = '';
  const skip = new Set(['reactions_like','reactions_love','reactions_care','reactions_haha','reactions_wow','reactions_sad','reactions_angry']);

  for (const [k, v] of Object.entries(meta)) {
    if (skip.has(k)) continue;
    if (!v && v !== 0) continue;
    const label = META_LABELS[k] || k.replace(/_/g, ' ');
    const tr = document.createElement('tr');
    const val = k === 'post_url'
      ? `<a href="${esc(v)}" target="_blank" style="color:#1877f2;word-break:break-all">${esc(v.slice(0, 60))}…</a>`
      : esc(String(v));
    tr.innerHTML = `<td class="meta-key">${esc(label)}</td><td class="meta-val">${val}</td>`;
    metaBody.appendChild(tr);
  }
  metaPanel.classList.remove('hidden');

  // Reaction chips
  reactionChips.innerHTML = '';
  const reactionKeys = ['like','love','care','haha','wow','sad','angry'];
  let hasReactions = false;

  if (meta.reactions_total) {
    const chip = document.createElement('div');
    chip.className = 'reaction-chip reaction-total';
    chip.textContent = `Total: ${meta.reactions_total}`;
    reactionChips.appendChild(chip);
    hasReactions = true;
  }

  for (const type of reactionKeys) {
    const count = meta[`reactions_${type}`];
    if (!count) continue;
    const chip = document.createElement('div');
    chip.className = 'reaction-chip';
    chip.innerHTML = `<span class="emoji">${REACTION_EMOJI[type] || '?'}</span><span class="count">${count}</span>`;
    chip.title = type;
    reactionChips.appendChild(chip);
    hasReactions = true;
  }

  if (hasReactions) reactionBar.classList.remove('hidden');
}

// ─── Render Preview Table ─────────────────────────────────────────────────────

function renderPreview(comments) {
  previewBody.innerHTML = '';
  if (!comments?.length) return;

  previewCnt.textContent = `(${comments.length})`;
  const MAX = 80;
  const frag = document.createDocumentFragment();

  for (let i = 0; i < Math.min(comments.length, MAX); i++) {
    const c = comments[i];
    const tr = document.createElement('tr');

    // Thread badge: shows T1, T2 … and depth as ">" prefix
    const depthMark = c.depth > 0 ? `<span class="depth-badge">${'>'.repeat(c.depth)}</span>` : '';
    const threadBadge = `<span class="thread-badge">T${c.thread_id}</span>`;

    // Timestamp: show only the relevant part
    const ts = formatTS(c.timestamp);

    // Truncate text
    const textShort = c.text.length > 55 ? c.text.slice(0, 55) + '…' : c.text;

    // Parent hint tooltip
    const parentHint = c.parent_author
      ? `title="↩ ${esc(c.parent_author)}: ${esc(c.parent_text_preview)}"`
      : '';

    tr.innerHTML = `
      <td class="col-seq">${c.seq}</td>
      <td class="col-thread">${threadBadge} ${depthMark}</td>
      <td class="col-author" title="${esc(c.author)}">${esc(c.author)}</td>
      <td class="col-text" ${parentHint}>${esc(textShort)}</td>
      <td class="col-time">${esc(ts)}</td>
      <td class="col-react">${c.reactions || ''}</td>
    `;
    frag.appendChild(tr);
  }

  previewBody.appendChild(frag);

  if (comments.length > MAX) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="6" style="text-align:center;padding:5px;color:#65676b;font-size:11px">… and ${comments.length - MAX} more</td>`;
    previewBody.appendChild(tr);
  }

  previewBox.classList.remove('hidden');
}

function formatTS(ts) {
  if (!ts) return '';
  // If ISO date, shorten it
  if (/^\d{4}-\d{2}-\d{2}T/.test(ts)) {
    return ts.slice(0, 16).replace('T', ' ');
  }
  return ts.length > 18 ? ts.slice(0, 18) : ts;
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
