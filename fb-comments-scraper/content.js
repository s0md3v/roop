// FB Comments Scraper - Content Script v2
// Full hierarchical scraping: post meta, nested threads, AI-ready CSV

const FB_SCRAPER = {
  comments: [],
  postMeta: null,
  isRunning: false,
  debugMode: false,

  log(...args) {
    if (this.debugMode) console.log('[FB-Scraper]', ...args);
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // POST METADATA
  // ═══════════════════════════════════════════════════════════════════════════

  findPostArticle() {
    // The post itself is an article that does NOT have a comment_id anchor
    // but is near the top of the page, before the comments section
    const articles = Array.from(document.querySelectorAll('[role="article"]'));
    // Return the first article that doesn't look like a comment
    for (const a of articles) {
      const hasCommentId = !!a.querySelector('a[href*="comment_id"], a[href*="/comment/"]');
      if (!hasCommentId) return a;
    }
    return articles[0] || document.body;
  },

  extractPostDate() {
    // Strategy 1: abbr[data-utime] – the very first one is usually the post
    const abbrs = document.querySelectorAll('abbr[data-utime]');
    if (abbrs.length > 0) {
      const utime = abbrs[0].getAttribute('data-utime');
      if (utime) return new Date(parseInt(utime) * 1000).toISOString();
      if (abbrs[0].title) return abbrs[0].title;
    }

    // Strategy 2: first timestamp-style link before comments
    const postLinks = document.querySelectorAll(
      'a[href*="/posts/"], a[href*="story_fbid"], a[href*="permalink"]'
    );
    for (const link of postLinks) {
      const txt = link.textContent.trim();
      if (txt && txt.length < 40) return txt;
    }
    return '';
  },

  extractPostType() {
    const url = location.href.toLowerCase();
    if (url.includes('/reel') || url.includes('/reels')) return 'reel';
    if (url.includes('/watch')) return 'video';
    if (url.includes('/photo') || url.includes('photo_id')) return 'photo';
    if (document.querySelector('video')) return 'video';
    if (document.querySelector('[data-testid="photo_viewer"], [role="img"][aria-label]')) return 'photo';
    // Link preview: an external link block inside the post
    const postArticle = this.findPostArticle();
    if (postArticle) {
      const extLink = postArticle.querySelector('a[target="_blank"][role="link"]');
      if (extLink) return 'link';
    }
    return 'text';
  },

  extractVideoDuration() {
    // From video element
    const video = document.querySelector('video');
    if (video && video.duration && !isNaN(video.duration) && video.duration > 0) {
      return this._formatDuration(video.duration);
    }
    // From player UI text (matches M:SS or H:MM:SS)
    const spans = document.querySelectorAll('span');
    for (const span of spans) {
      const txt = span.textContent.trim();
      if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(txt)) return txt;
    }
    return '';
  },

  _formatDuration(secs) {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    if (h > 0) return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    return `${m}:${String(s).padStart(2,'0')}`;
  },

  extractPostText() {
    const postArticle = this.findPostArticle();
    if (!postArticle) return '';

    // Remove nested comment articles first
    const clone = postArticle.cloneNode(true);
    clone.querySelectorAll('[role="article"]').forEach(n => n.remove());

    // Prefer dir=auto divs (FB text content)
    const divs = Array.from(clone.querySelectorAll('div[dir="auto"]'));
    const candidates = divs
      .map(d => d.textContent.trim())
      .filter(t => t.length > 10)
      .sort((a, b) => b.length - a.length);

    return candidates[0] ? candidates[0].slice(0, 300) : '';
  },

  extractPostReactions() {
    const TYPES = ['like','love','care','haha','wow','sad','angry'];
    const breakdown = {};
    let total = 0;

    // Strategy 1: aria-label on reaction summary buttons
    // FB renders something like aria-label="123 people reacted with Like"
    // or aria-label="Like: 123"
    const ariaEls = document.querySelectorAll('[aria-label]');
    for (const el of ariaEls) {
      const label = (el.getAttribute('aria-label') || '').toLowerCase();
      for (const type of TYPES) {
        const re = new RegExp(`(\\d[\\d,.]*)\\s*(people\\s+)?reacted\\s+with\\s+${type}|${type}[:\\s]+(\\d[\\d,.]*)`, 'i');
        const m = label.match(re);
        if (m) {
          const raw = (m[1] || m[3] || '').replace(/[,.]/g, '');
          const count = parseInt(raw);
          if (!isNaN(count) && count > 0) breakdown[type] = count;
        }
      }
    }

    // Strategy 2: tooltip text that shows breakdown
    // FB sometimes pre-renders this as hidden elements
    const tooltips = document.querySelectorAll('[data-tooltip-content], [data-hover="tooltip"]');
    for (const tip of tooltips) {
      const txt = (tip.getAttribute('data-tooltip-content') || tip.textContent || '').toLowerCase();
      for (const type of TYPES) {
        if (txt.includes(type)) {
          const m = txt.match(/(\d[\d,.]*)/);
          if (m && !breakdown[type]) {
            breakdown[type] = parseInt(m[1].replace(/[,.]/g, ''));
          }
        }
      }
    }

    // Strategy 3: find the reaction count (total) from the post reaction bar
    // It's a span near the "Like Comment Share" buttons with a number
    const allSpans = Array.from(document.querySelectorAll('span'));
    for (const span of allSpans) {
      const label = (span.getAttribute('aria-label') || '').toLowerCase();
      if (/\d+.*(reaction|reacted)/i.test(label)) {
        const m = label.match(/(\d[\d,.]*)/);
        if (m) { total = parseInt(m[1].replace(/[,.]/g, '')); break; }
      }
      // Short numeric spans in reaction areas
      const txt = span.textContent.trim();
      if (/^[\d,.]+[KkMm]?$/.test(txt)) {
        const parent = span.closest('[role="toolbar"], [role="group"]');
        if (parent && !total) {
          const val = this._parseReactionCount(txt);
          if (val > 0 && val < 1e9) total = val;
        }
      }
    }

    // Fill total from breakdown if not found
    if (total === 0 && Object.keys(breakdown).length > 0) {
      total = Object.values(breakdown).reduce((a, b) => a + b, 0);
    }

    return { total, breakdown };
  },

  _parseReactionCount(txt) {
    const t = txt.trim().replace(/,/g, '');
    if (/^\d+$/.test(t)) return parseInt(t);
    if (/^\d+(\.\d+)?[Kk]$/.test(t)) return Math.round(parseFloat(t) * 1000);
    if (/^\d+(\.\d+)?[Mm]$/.test(t)) return Math.round(parseFloat(t) * 1000000);
    return 0;
  },

  extractPostMeta() {
    const reactions = this.extractPostReactions();
    const postType = this.extractPostType();
    const meta = {
      scrape_date: new Date().toISOString(),
      post_url: location.href,
      post_date: this.extractPostDate(),
      post_type: postType,
      video_duration: postType === 'video' || postType === 'reel' ? this.extractVideoDuration() : '',
      post_text_preview: this.extractPostText(),
      reactions_total: reactions.total,
      reactions_like:  reactions.breakdown.like  || 0,
      reactions_love:  reactions.breakdown.love  || 0,
      reactions_care:  reactions.breakdown.care  || 0,
      reactions_haha:  reactions.breakdown.haha  || 0,
      reactions_wow:   reactions.breakdown.wow   || 0,
      reactions_sad:   reactions.breakdown.sad   || 0,
      reactions_angry: reactions.breakdown.angry || 0,
    };
    this.log('Post meta:', meta);
    return meta;
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // HIERARCHICAL COMMENT TREE
  // ═══════════════════════════════════════════════════════════════════════════

  getCommentArticles() {
    // Only articles that directly contain a comment permalink link
    return Array.from(document.querySelectorAll('[role="article"]')).filter(a =>
      a.querySelector('a[href*="comment_id"], a[href*="/comment/"]')
    );
  },

  buildCommentTree() {
    const articles = this.getCommentArticles();
    const articleSet = new Set(articles);

    // Calculate DOM depth (how many ancestor comment articles)
    const items = articles.map(article => {
      let depth = 0;
      let el = article.parentElement;
      while (el) {
        if (articleSet.has(el)) depth++;
        el = el.parentElement;
      }
      return { element: article, depth };
    });

    // Build tree: assign thread_id and track parents
    let threadId = 0;
    let seq = 0;
    const depthStack = []; // depthStack[d] = last comment node at depth d
    const result = [];

    for (const item of items) {
      if (item.depth === 0) {
        threadId++;
        // Clear all deeper entries
        depthStack.length = 1;
        depthStack[0] = null;
      }

      const parent = (item.depth > 0) ? (depthStack[item.depth - 1] || null) : null;
      seq++;

      const node = {
        element: item.element,
        depth: item.depth,
        threadId,
        seq,
        parent, // reference to parent node (null for top-level)
      };

      depthStack[item.depth] = node;
      result.push(node);
    }

    return result;
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // PER-COMMENT EXTRACTION
  // ═══════════════════════════════════════════════════════════════════════════

  _cleanArticle(article) {
    // Clone and remove nested comment articles so we only parse THIS comment
    const clone = article.cloneNode(true);
    clone.querySelectorAll('[role="article"]').forEach(n => n.remove());
    return clone;
  },

  extractAuthor(clean) {
    // First non-comment-permalink anchor with reasonable text
    const links = Array.from(clean.querySelectorAll('a'));
    for (const link of links) {
      const href = link.getAttribute('href') || '';
      if (href.includes('comment_id') || href.includes('/comment/')) continue;
      const txt = link.textContent.trim();
      if (txt && txt.length >= 2 && txt.length <= 80) return txt;
    }
    const bold = clean.querySelector('strong, b, h3, h4');
    if (bold) return bold.textContent.trim();
    return '(unknown)';
  },

  extractText(clean) {
    // Leaf div[dir="auto"] elements (not containing other dir=auto divs)
    const divs = Array.from(clean.querySelectorAll('div[dir="auto"]'));
    const leaves = divs.filter(d => !d.querySelector('div[dir="auto"]'));
    if (leaves.length > 0) {
      // Longest leaf is most likely the comment body
      return leaves.sort((a, b) => b.textContent.length - a.textContent.length)[0]
        .textContent.trim();
    }
    // Fallback: span[dir="auto"]
    const spans = clean.querySelectorAll('span[dir="auto"]');
    for (const s of spans) {
      const txt = s.textContent.trim();
      if (txt.length > 0) return txt;
    }
    return (clean.textContent || '').trim().slice(0, 500);
  },

  extractTimestamp(article) {
    // abbr[data-utime]
    const abbr = article.querySelector('abbr[data-utime]');
    if (abbr) {
      const utime = abbr.getAttribute('data-utime');
      if (utime) return new Date(parseInt(utime) * 1000).toISOString();
      return abbr.title || abbr.textContent.trim();
    }
    // Text of the comment permalink link is usually "2 hours ago" etc.
    const links = article.querySelectorAll('a[href*="comment_id"], a[href*="/comment/"]');
    for (const link of links) {
      const txt = link.textContent.trim();
      if (txt && txt.length < 40) return txt;
    }
    return '';
  },

  extractCommentReactions(clean) {
    // aria-label containing reaction info
    for (const el of clean.querySelectorAll('[aria-label]')) {
      const label = el.getAttribute('aria-label') || '';
      const m = label.match(/(\d[\d,.]*)\s*(reaction|people)/i);
      if (m) return this._parseReactionCount(m[1]);
    }
    // Short numeric span near a reaction/like element
    const spans = Array.from(clean.querySelectorAll('span'));
    for (const span of spans) {
      const txt = span.textContent.trim();
      if (/^\d+$/.test(txt)) {
        const ctx = (span.parentElement?.textContent || '').toLowerCase();
        if (/like|react|love|care|haha|wow|sad|angry/i.test(ctx)) {
          return parseInt(txt);
        }
      }
    }
    return 0;
  },

  extractPermalink(article) {
    const link = article.querySelector('a[href*="comment_id"], a[href*="/comment/"]');
    if (!link) return '';
    const href = link.getAttribute('href');
    if (href.startsWith('http')) return href;
    return 'https://www.facebook.com' + href;
  },

  parseNode(node) {
    const clean = this._cleanArticle(node.element);
    const author       = this.extractAuthor(clean);
    const text         = this.extractText(clean);
    const timestamp    = this.extractTimestamp(node.element);
    const reactions    = this.extractCommentReactions(clean);
    const permalink    = this.extractPermalink(node.element);
    const parentAuthor = node.parent ? node.parent.parsed?.author || '' : '';
    const parentText   = node.parent ? (node.parent.parsed?.text || '').slice(0, 80) : '';
    const indent       = '>'.repeat(node.depth);

    return {
      seq:          node.seq,
      thread_id:    node.threadId,
      depth:        node.depth,
      indent,
      author,
      text,
      timestamp,
      reactions,
      permalink,
      parent_author: parentAuthor,
      parent_text_preview: parentText,
    };
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // SCROLL & LOAD MORE
  // ═══════════════════════════════════════════════════════════════════════════

  clickLoadMore() {
    const patterns = [
      /view \d* ?(more)? comment/i,
      /load more comment/i,
      /\d+ repl(y|ies)/i,
      /view \d+ more repl/i,
      /zobraziť (ďalšie|viac)/i,
      /most relevant/i,
      /all comment/i,
    ];
    let clicked = 0;
    for (const btn of document.querySelectorAll(
      'div[role="button"], button, span[role="button"]'
    )) {
      const txt = (btn.innerText || btn.textContent || '').trim();
      if (patterns.some(p => p.test(txt))) {
        this.log('Clicking:', txt);
        btn.click();
        clicked++;
      }
    }
    return clicked;
  },

  sleep(ms) { return new Promise(r => setTimeout(r, ms)); },

  async autoScroll(statusCallback) {
    let lastHeight = 0;
    let stale = 0;
    while (stale < 3) {
      window.scrollTo(0, document.body.scrollHeight);
      await this.sleep(1500);
      const clicked = this.clickLoadMore();
      if (clicked > 0) { await this.sleep(2000); stale = 0; }
      const h = document.body.scrollHeight;
      if (h === lastHeight) stale++; else { stale = 0; lastHeight = h; }
      const count = this.getCommentArticles().length;
      if (statusCallback) statusCallback(`Scrolling… found ${count} comment elements`);
    }
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // MAIN SCRAPE
  // ═══════════════════════════════════════════════════════════════════════════

  async scrape(options = {}, statusCallback) {
    if (this.isRunning) return { error: 'Already running' };
    this.isRunning = true;
    this.debugMode = options.debug || false;
    this.comments = [];
    this.postMeta = null;

    try {
      if (statusCallback) statusCallback('Extracting post metadata…');
      this.postMeta = this.extractPostMeta();

      if (options.autoScroll !== false) {
        if (statusCallback) statusCallback('Auto-scrolling to load all comments…');
        await this.autoScroll(statusCallback);
      }

      if (statusCallback) statusCallback('Building comment tree…');
      const tree = this.buildCommentTree();
      this.log(`Tree has ${tree.length} nodes`);

      // Two-pass: parse all nodes, then backfill parent_author/parent_text_preview
      // by referencing already-parsed parent nodes
      for (const node of tree) {
        node.parsed = this.parseNode(node);
      }
      // Second pass to fill parent_* from actual parsed data
      for (const node of tree) {
        if (node.parent && node.parent.parsed) {
          node.parsed.parent_author       = node.parent.parsed.author;
          node.parsed.parent_text_preview = node.parent.parsed.text.slice(0, 80);
        }
      }

      this.comments = tree.map(n => n.parsed);
      this.postMeta.total_comments_scraped = this.comments.length;

      if (statusCallback) statusCallback(`Done! ${this.comments.length} comments scraped.`);
      return { success: true, count: this.comments.length, comments: this.comments, postMeta: this.postMeta };

    } catch (err) {
      this.log('Scrape error:', err);
      return { error: err.message };
    } finally {
      this.isRunning = false;
    }
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // CSV EXPORT (AI-friendly)
  // Format:
  //   Row 1..N:   row_type=META  with meta_key, meta_value
  //   Row N+1:    blank separator
  //   Row N+2:    column headers for comments
  //   Row N+3..:  row_type=COMMENT with full data
  //
  // AI can parse: metadata first, then a chronological threaded comment list.
  // Each COMMENT row has seq (order), thread_id (groups replies), depth+indent
  // (shows nesting), and parent_author+parent_text_preview (context of reply).
  // ═══════════════════════════════════════════════════════════════════════════

  toCSV() {
    const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const rows = [];

    const COLS = [
      'row_type','seq','thread_id','depth','indent',
      'author','text','timestamp','reactions','permalink',
      'parent_author','parent_text_preview',
      'meta_key','meta_value',
    ];

    // ── Metadata rows ──────────────────────────────────────────────────────
    const meta = this.postMeta || {};
    const emptyComment = new Array(10).fill('""');
    for (const [k, v] of Object.entries(meta)) {
      rows.push([
        '"META"', '""','""','""','""',
        '""','""','""','""','""',
        '""','""',
        esc(k), esc(v),
      ].join(','));
    }

    // ── Blank separator ────────────────────────────────────────────────────
    rows.push(COLS.map(() => '""').join(','));

    // ── Header row ─────────────────────────────────────────────────────────
    rows.push(COLS.map(esc).join(','));

    // ── Comment rows ───────────────────────────────────────────────────────
    for (const c of this.comments) {
      rows.push([
        '"COMMENT"',
        esc(c.seq),
        esc(c.thread_id),
        esc(c.depth),
        esc(c.indent),
        esc(c.author),
        esc(c.text),
        esc(c.timestamp),
        esc(c.reactions),
        esc(c.permalink),
        esc(c.parent_author),
        esc(c.parent_text_preview),
        '""', '""',
      ].join(','));
    }

    return rows.join('\r\n');
  },

  downloadCSV(filename = 'fb_comments.csv') {
    if (!this.comments.length) return { error: 'No comments to export' };
    const csv = this.toCSV();
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

  // ═══════════════════════════════════════════════════════════════════════════
  // DEBUG PROBE
  // ═══════════════════════════════════════════════════════════════════════════

  debugProbe() {
    const articles = this.getCommentArticles();
    const tree = this.buildCommentTree().slice(0, 5);

    const info = {
      url: location.href,
      commentArticles: articles.length,
      sampleTree: tree.map(node => {
        const clean = this._cleanArticle(node.element);
        return {
          depth:     node.depth,
          threadId:  node.threadId,
          author:    this.extractAuthor(clean),
          text:      this.extractText(clean).slice(0, 80),
          timestamp: this.extractTimestamp(node.element),
          reactions: this.extractCommentReactions(clean),
        };
      }),
      postMeta: this.extractPostMeta(),
    };
    return info;
  },
};

// ─── MESSAGE LISTENER ────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'scrape') {
    FB_SCRAPER.scrape(msg.options || {}, status => {
      chrome.runtime.sendMessage({ action: 'status', text: status }).catch(() => {});
    }).then(result => sendResponse(result));
    return true;
  }

  if (msg.action === 'download') {
    sendResponse(FB_SCRAPER.downloadCSV(msg.filename));
    return false;
  }

  if (msg.action === 'probe') {
    sendResponse(FB_SCRAPER.debugProbe());
    return false;
  }

  if (msg.action === 'getComments') {
    sendResponse({ comments: FB_SCRAPER.comments, postMeta: FB_SCRAPER.postMeta });
    return false;
  }
});
