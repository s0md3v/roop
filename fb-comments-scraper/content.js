// FB Comments Scraper - Content Script
// Uses multiple selector strategies to work even when FB changes obfuscated class names

const FB_SCRAPER = {
  comments: [],
  isRunning: false,
  debugMode: false,

  log(...args) {
    if (this.debugMode) console.log('[FB-Scraper]', ...args);
  },

  // ─── SELECTOR STRATEGIES ──────────────────────────────────────────────────
  // Strategy 1: role="article" elements inside the comments section
  // Strategy 2: anchor tags with ?comment_id= in href (each comment has one)
  // Strategy 3: [data-testid] patterns
  // We build a comment list by finding the "anchor node" of each comment

  findCommentAnchors() {
    // Every FB comment has a permalink link that contains ?comment_id= or /comment/
    const links = Array.from(document.querySelectorAll('a[href*="comment_id"], a[href*="/comment/"]'));
    this.log(`Found ${links.length} comment anchor links`);
    return links;
  },

  getCommentContainer(anchorEl) {
    // Walk up DOM to find the article/li/div that wraps a single comment
    let el = anchorEl.parentElement;
    for (let i = 0; i < 12; i++) {
      if (!el) break;
      const role = el.getAttribute('role');
      if (role === 'article') return el;
      // FB sometimes uses <li> as the comment wrapper
      if (el.tagName === 'LI') return el;
      el = el.parentElement;
    }
    // Fallback: go up a reasonable number of levels
    el = anchorEl;
    for (let i = 0; i < 6; i++) {
      if (!el.parentElement) break;
      el = el.parentElement;
    }
    return el;
  },

  extractTimestamp(container) {
    // Timestamps are usually in <abbr> or in a link with a unix timestamp
    const abbr = container.querySelector('abbr[data-utime], abbr[title]');
    if (abbr) {
      const utime = abbr.getAttribute('data-utime');
      if (utime) return new Date(parseInt(utime) * 1000).toISOString();
      return abbr.getAttribute('title') || abbr.textContent.trim();
    }

    // Timestamp links: the permalink link text is usually the relative time
    const timeLinks = container.querySelectorAll('a[href*="comment_id"], a[href*="/comment/"]');
    for (const link of timeLinks) {
      const txt = link.textContent.trim();
      if (txt && txt.length < 30) return txt; // "2 hours ago", "Monday at 3:00 PM" etc.
    }
    return '';
  },

  extractAuthor(container) {
    // Author names are in <a> elements near the top of the comment
    // Heuristic: the first <a> that is NOT a comment permalink and has reasonable text length
    const allLinks = container.querySelectorAll('a');
    for (const link of allLinks) {
      const href = link.getAttribute('href') || '';
      if (href.includes('comment_id') || href.includes('/comment/')) continue;
      const txt = link.textContent.trim();
      if (txt && txt.length > 1 && txt.length < 80) return txt;
    }

    // Fallback: strong or b tag
    const bold = container.querySelector('strong, b');
    if (bold) return bold.textContent.trim();

    return '(unknown)';
  },

  extractText(container, anchorEl) {
    // The comment text is in a div that is a sibling or descendant near the timestamp anchor
    // Strategy: collect all text nodes in the container, exclude author name & timestamp

    // FB often wraps text in a <div> with dir="auto"
    const textDivs = container.querySelectorAll('div[dir="auto"]');
    const candidates = [];
    for (const div of textDivs) {
      const txt = div.textContent.trim();
      if (txt && txt.length > 0 && !div.querySelector('div[dir="auto"]')) {
        // Leaf div with dir=auto → likely comment text
        candidates.push(txt);
      }
    }

    if (candidates.length > 0) {
      // Longest candidate is most likely the comment body
      candidates.sort((a, b) => b.length - a.length);
      return candidates[0];
    }

    // Fallback: take all text from container minus author & timestamp text
    const author = this.extractAuthor(container);
    const ts = this.extractTimestamp(container);
    let raw = container.innerText || container.textContent || '';
    raw = raw.replace(author, '').replace(ts, '').trim();
    return raw;
  },

  extractLikes(container) {
    // Like count is often in a span near a reaction button
    // Pattern: aria-label containing "reaction" or text like "123" near a like button
    const spans = container.querySelectorAll('span');
    for (const span of spans) {
      const label = span.getAttribute('aria-label') || '';
      if (/reaction/i.test(label)) {
        const match = label.match(/\d+/);
        if (match) return match[0];
      }
      // Plain number in short span
      const txt = span.textContent.trim();
      if (/^\d+$/.test(txt) && parseInt(txt) < 1000000) {
        // Could be likes – check parent context
        const parentText = (span.parentElement?.textContent || '').toLowerCase();
        if (/like|reaction|love|care|haha|wow|sad|angry/i.test(parentText)) {
          return txt;
        }
      }
    }
    return '0';
  },

  parseCommentFromAnchor(anchorEl) {
    const container = this.getCommentContainer(anchorEl);
    const author = this.extractAuthor(container);
    const text = this.extractText(container, anchorEl);
    const timestamp = this.extractTimestamp(container);
    const likes = this.extractLikes(container);
    const permalink = anchorEl.getAttribute('href') || '';

    return { author, text, timestamp, likes, permalink };
  },

  deduplicateComments(list) {
    const seen = new Set();
    return list.filter(c => {
      const key = `${c.author}|${c.permalink}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  },

  // ─── SCROLL & LOAD MORE ───────────────────────────────────────────────────

  clickLoadMore() {
    // Look for "View more comments", "View X more comments" etc.
    const patterns = [
      /view \d* ?(more)? comment/i,
      /load more comment/i,
      /zobraziť (ďalšie|viac)/i,
      /further comment/i,
    ];

    const allButtons = Array.from(document.querySelectorAll(
      'div[role="button"], button, span[role="button"]'
    ));

    let clicked = 0;
    for (const btn of allButtons) {
      const txt = (btn.innerText || btn.textContent || '').trim();
      if (patterns.some(p => p.test(txt))) {
        this.log('Clicking load more:', txt);
        btn.click();
        clicked++;
      }
    }

    // Also look for "X replies" buttons (nested replies)
    const replyButtons = Array.from(document.querySelectorAll(
      'div[role="button"], span[role="button"]'
    )).filter(el => /\d+ repl/i.test(el.textContent || ''));
    for (const btn of replyButtons) {
      btn.click();
      clicked++;
    }

    return clicked;
  },

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  async autoScroll(statusCallback) {
    let lastHeight = 0;
    let noChangeCount = 0;

    while (noChangeCount < 3) {
      window.scrollTo(0, document.body.scrollHeight);
      await this.sleep(1500);

      const clicked = this.clickLoadMore();
      if (clicked > 0) {
        await this.sleep(2000);
        noChangeCount = 0;
      }

      const newHeight = document.body.scrollHeight;
      if (newHeight === lastHeight) {
        noChangeCount++;
      } else {
        noChangeCount = 0;
        lastHeight = newHeight;
      }

      const count = this.findCommentAnchors().length;
      if (statusCallback) statusCallback(`Scrolling... found ${count} comments so far`);
    }
  },

  // ─── MAIN SCRAPE ──────────────────────────────────────────────────────────

  async scrape(options = {}, statusCallback) {
    if (this.isRunning) return { error: 'Already running' };
    this.isRunning = true;
    this.debugMode = options.debug || false;
    this.comments = [];

    try {
      if (statusCallback) statusCallback('Starting scrape...');

      if (options.autoScroll !== false) {
        await this.autoScroll(statusCallback);
      }

      if (statusCallback) statusCallback('Parsing comments...');

      const anchors = this.findCommentAnchors();
      this.log(`Parsing ${anchors.length} comment anchors`);

      for (const anchor of anchors) {
        try {
          const comment = this.parseCommentFromAnchor(anchor);
          if (comment.text && comment.text.length > 0) {
            this.comments.push(comment);
          }
        } catch (e) {
          this.log('Error parsing comment:', e);
        }
      }

      this.comments = this.deduplicateComments(this.comments);
      this.log(`Final comment count: ${this.comments.length}`);

      if (statusCallback) statusCallback(`Done! Scraped ${this.comments.length} comments.`);
      return { success: true, count: this.comments.length, comments: this.comments };

    } catch (err) {
      return { error: err.message };
    } finally {
      this.isRunning = false;
    }
  },

  // ─── EXPORT ───────────────────────────────────────────────────────────────

  toCSV(comments) {
    const headers = ['author', 'text', 'timestamp', 'likes', 'permalink'];
    const escape = val => {
      const s = String(val ?? '').replace(/"/g, '""');
      return `"${s}"`;
    };
    const rows = [
      headers.join(','),
      ...comments.map(c =>
        headers.map(h => escape(c[h])).join(',')
      ),
    ];
    return rows.join('\r\n');
  },

  downloadCSV(filename = 'fb_comments.csv') {
    if (this.comments.length === 0) return { error: 'No comments to export' };
    const csv = this.toCSV(this.comments);
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    return { success: true, count: this.comments.length };
  },

  // ─── DEBUG PROBE ──────────────────────────────────────────────────────────

  debugProbe() {
    const anchors = this.findCommentAnchors();
    const info = {
      url: location.href,
      totalAnchors: anchors.length,
      articleElements: document.querySelectorAll('[role="article"]').length,
      dirAutoDivs: document.querySelectorAll('div[dir="auto"]').length,
      sampleComments: [],
    };

    for (const anchor of anchors.slice(0, 3)) {
      try {
        const container = this.getCommentContainer(anchor);
        info.sampleComments.push({
          author: this.extractAuthor(container),
          text: this.extractText(container, anchor).slice(0, 100),
          timestamp: this.extractTimestamp(container),
          likes: this.extractLikes(container),
          permalink: anchor.getAttribute('href'),
        });
      } catch (e) {
        info.sampleComments.push({ error: e.message });
      }
    }
    return info;
  },
};

// ─── MESSAGE LISTENER ───────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'scrape') {
    FB_SCRAPER.scrape(msg.options || {}, status => {
      chrome.runtime.sendMessage({ action: 'status', text: status }).catch(() => {});
    }).then(result => sendResponse(result));
    return true; // async
  }

  if (msg.action === 'download') {
    const result = FB_SCRAPER.downloadCSV(msg.filename);
    sendResponse(result);
    return false;
  }

  if (msg.action === 'probe') {
    const info = FB_SCRAPER.debugProbe();
    sendResponse(info);
    return false;
  }

  if (msg.action === 'getComments') {
    sendResponse({ comments: FB_SCRAPER.comments });
    return false;
  }
});
