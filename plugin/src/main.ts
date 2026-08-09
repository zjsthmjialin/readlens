import { App, Plugin, parseYaml, MarkdownPostProcessorContext } from "obsidian";

/** 一本书的精简字段（来自笔记 frontmatter）。 */
interface Book {
  title: string;
  basename: string;
  status: string;
  rating: number | null;
  platformRating: number | null;
  category: string;
  author: string;
  owned: string;
  priority: string;
  location: string;
  price: string;
  source: string;
  progress: number | null;
  finished: string;              // 原始字符串（用于显示/排序）
  finishedYear: number | null;
  finishedMonth: number | null;
  added: string;
}

// Apple 系统色
const PALETTE = ["#0A84FF", "#34C759", "#FF9F0A", "#BF5AF2", "#FF375F",
                 "#64D2FF", "#FFD60A", "#5E5CE6"];

function hexToRgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  const n = parseInt(h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

function numOrNull(v: any): number | null {
  if (v === undefined || v === null || v === "") return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

function collectBooks(app: App): Book[] {
  const out: Book[] = [];
  for (const f of app.vault.getMarkdownFiles()) {
    // 跳过模板目录（避免把书籍/藏书模板当成真书）
    if (f.path.startsWith("00-模板/") || f.path.includes("/00-模板/")) continue;
    const fm = app.metadataCache.getFileCache(f)?.frontmatter;
    if (!fm) continue;
    const tags = fm.tags;
    const isBook =
      fm.type === "book" ||
      (Array.isArray(tags) && tags.includes("book")) ||
      (typeof tags === "string" && tags.includes("book"));
    if (!isBook) continue;
    // 跳过未填充的模板占位（title 含 {{ }}）
    const rawTitle = String(fm.title ?? f.basename);
    if (rawTitle.includes("{{") || rawTitle.includes("}}")) continue;

    let fy: number | null = null, fmo: number | null = null;
    const finRaw = fm.finished ? String(fm.finished) : "";
    if (finRaw) {
      const m = finRaw.match(/^(\d{4})-(\d{2})/);
      if (m) { fy = +m[1]; fmo = +m[2]; }
      else { const y = finRaw.match(/(\d{4})/); if (y) fy = +y[1]; }
    }
    out.push({
      title: String(fm.title ?? f.basename),
      basename: f.basename,
      status: String(fm.status ?? ""),
      rating: numOrNull(fm.rating),
      platformRating: numOrNull(fm.platform_rating),
      category: (fm.category && String(fm.category).trim()) || "",
      author: String(fm.author ?? ""),
      owned: String(fm.owned ?? "none"),
      priority: String(fm.priority ?? ""),
      location: String(fm.location ?? ""),
      price: fm.price != null ? String(fm.price) : "",
      source: String(fm.source ?? ""),
      progress: numOrNull(fm.progress),
      finished: finRaw,
      finishedYear: fy,
      finishedMonth: fmo,
      added: String(fm.added ?? ""),
    });
  }
  return out;
}

/* ---------- 通用小工具 ---------- */

function countUp(el: HTMLElement, target: number): void {
  const dur = 750, start = performance.now();
  const tick = (t: number) => {
    const p = Math.min(1, (t - start) / dur);
    el.setText(String(Math.round(target * (1 - Math.pow(1 - p, 3)))));
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function panel(parent: HTMLElement, title?: string): HTMLElement {
  const p = parent.createDiv({ cls: "rl-panel" });
  if (title) p.createDiv({ cls: "rl-panel-title", text: title });
  return p.createDiv({ cls: "rl-panel-body" });
}

function bookLink(parent: HTMLElement, b: Book): HTMLElement {
  const a = parent.createEl("a", { cls: "internal-link rl-link", text: `《${b.title}》` });
  a.setAttribute("data-href", b.basename);
  a.setAttribute("href", b.basename);
  return a;
}

/* ---------- KPI / 条形 / 圆环 / 热力 ---------- */

function kpiCard(parent: HTMLElement, icon: string, label: string,
                 value: number, accent: string): void {
  const card = parent.createDiv({ cls: "rl-kpi" });
  card.style.setProperty("--rl-accent", accent);
  card.style.setProperty("--rl-tint", hexToRgba(accent, 0.16));
  card.createDiv({ cls: "rl-kpi-tile", text: icon });
  const val = card.createDiv({ cls: "rl-kpi-value", text: "0" });
  card.createDiv({ cls: "rl-kpi-label", text: label });
  countUp(val, value);
}

function barRow(parent: HTMLElement, label: string, value: number, max: number,
                gradient: string, valueText?: string): void {
  const row = parent.createDiv({ cls: "rl-bar-row" });
  row.createDiv({ cls: "rl-bar-label", text: label });
  const track = row.createDiv({ cls: "rl-bar-track" });
  const fill = track.createDiv({ cls: "rl-bar-fill" });
  fill.style.background = gradient;
  const target = max > 0 ? Math.max(3, Math.round((value / max) * 100)) : 0;
  requestAnimationFrame(() => { fill.style.width = target + "%"; });
  row.createDiv({ cls: "rl-bar-value", text: valueText ?? String(value) });
}

function donut(parent: HTMLElement, entries: [string, number][]): void {
  const total = entries.reduce((s, [, n]) => s + n, 0) || 1;
  const box = parent.createDiv({ cls: "rl-donut-box" });
  const wrap = box.createDiv({ cls: "rl-donut-wrap" });
  const size = 172, r = 62, cx = size / 2, cy = size / 2, circ = 2 * Math.PI * r;
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
  svg.setAttribute("class", "rl-donut");
  const bg = document.createElementNS(svgNS, "circle");
  bg.setAttribute("cx", String(cx)); bg.setAttribute("cy", String(cy));
  bg.setAttribute("r", String(r)); bg.setAttribute("fill", "none");
  bg.setAttribute("stroke", "var(--background-modifier-border)");
  bg.setAttribute("stroke-width", "20");
  svg.appendChild(bg);
  let offset = 0;
  entries.forEach(([, n], i) => {
    const frac = n / total;
    const c = document.createElementNS(svgNS, "circle");
    c.setAttribute("cx", String(cx)); c.setAttribute("cy", String(cy));
    c.setAttribute("r", String(r)); c.setAttribute("fill", "none");
    c.setAttribute("stroke", PALETTE[i % PALETTE.length]);
    c.setAttribute("stroke-width", "20");
    c.setAttribute("stroke-linecap", "round");
    c.setAttribute("stroke-dashoffset", String(-offset * circ));
    c.setAttribute("transform", `rotate(-90 ${cx} ${cy})`);
    c.setAttribute("class", "rl-donut-seg");
    c.setAttribute("stroke-dasharray", `0 ${circ}`);
    svg.appendChild(c);
    requestAnimationFrame(() => c.setAttribute("stroke-dasharray", `${frac * circ} ${circ}`));
    offset += frac;
  });
  wrap.appendChild(svg);
  const center = wrap.createDiv({ cls: "rl-donut-center" });
  const cv = center.createDiv({ cls: "rl-donut-total", text: "0" });
  center.createDiv({ cls: "rl-donut-cap", text: "本书" });
  countUp(cv, total);
  const legend = box.createDiv({ cls: "rl-legend" });
  entries.forEach(([k, n], i) => {
    const item = legend.createDiv({ cls: "rl-legend-item" });
    const dot = item.createSpan({ cls: "rl-legend-dot" });
    dot.style.background = PALETTE[i % PALETTE.length];
    item.createSpan({ cls: "rl-legend-k", text: k || "未分类" });
    item.createSpan({ cls: "rl-legend-v", text: `${n} · ${Math.round((100 * n) / total)}%` });
  });
}

function heatmap(parent: HTMLElement, books: Book[]): void {
  const grid: Record<number, number[]> = {};
  for (const b of books) {
    if (b.finishedYear == null) continue;
    if (!grid[b.finishedYear]) grid[b.finishedYear] = new Array(12).fill(0);
    if (b.finishedMonth != null && b.finishedMonth >= 1 && b.finishedMonth <= 12)
      grid[b.finishedYear][b.finishedMonth - 1]++;
  }
  const years = Object.keys(grid).map(Number).sort();
  if (years.length === 0) {
    parent.createDiv({ cls: "rl-empty", text: "还没有带 finished 日期的已读书。" });
    return;
  }
  let max = 1;
  for (const y of years) max = Math.max(max, ...grid[y]);
  const head = parent.createDiv({ cls: "rl-heat-row rl-heat-head" });
  head.createDiv({ cls: "rl-heat-year" });
  for (let m = 1; m <= 12; m++) head.createDiv({ cls: "rl-heat-cell rl-heat-mlabel", text: String(m) });
  for (const y of years) {
    const row = parent.createDiv({ cls: "rl-heat-row" });
    row.createDiv({ cls: "rl-heat-year", text: String(y) });
    grid[y].forEach((n, mi) => {
      const cell = row.createDiv({ cls: "rl-heat-cell", text: n > 0 ? String(n) : "" });
      const a = n > 0 ? (0.22 + 0.78 * (n / max)) : 0;
      cell.style.background = n > 0 ? `rgba(52,199,89,${a.toFixed(2)})` : "var(--background-modifier-border)";
      cell.setAttribute("aria-label", `${y}年${mi + 1}月：${n} 本`);
      if (n > 0) cell.addClass("rl-heat-on");
    });
  }
  const lg = parent.createDiv({ cls: "rl-heat-legend" });
  lg.createSpan({ text: "少" });
  [0.15, 0.4, 0.65, 0.9].forEach(a => {
    const c = lg.createSpan({ cls: "rl-heat-cell rl-heat-lgcell" });
    c.style.background = `rgba(52,199,89,${a})`;
  });
  lg.createSpan({ text: "多" });
}

/* ---------- 书单表格 ---------- */

const COLS: Record<string, { head: string; cell: (b: Book, host: HTMLElement) => void }> = {
  book: { head: "书", cell: (b, td) => bookLink(td, b) },
  author: { head: "作者", cell: (b, td) => td.setText(b.author || "—") },
  status: { head: "状态", cell: (b, td) => td.setText(b.status || "—") },
  progress: { head: "进度", cell: (b, td) => td.setText(b.progress != null ? b.progress + "%" : "—") },
  rating: { head: "评分", cell: (b, td) => td.setText(b.rating != null ? "★".repeat(Math.round(b.rating)) : "—") },
  platform: { head: "平台评分", cell: (b, td) => td.setText(b.platformRating != null ? String(b.platformRating) : "—") },
  finished: { head: "读完于", cell: (b, td) => td.setText(b.finished || "—") },
  category: { head: "分类", cell: (b, td) => td.setText(b.category || "—") },
  owned: { head: "拥有", cell: (b, td) => td.setText(b.owned || "—") },
  priority: { head: "优先级", cell: (b, td) => td.setText(b.priority || "—") },
  location: { head: "位置", cell: (b, td) => td.setText(b.location || "—") },
  price: { head: "价格", cell: (b, td) => td.setText(b.price || "—") },
  source: { head: "来源", cell: (b, td) => td.setText(b.source || "—") },
};

function sortBooks(books: Book[], sort: string, order: string): Book[] {
  const dir = order === "asc" ? 1 : -1;
  const key = (b: Book): any => {
    switch (sort) {
      case "progress": return b.progress ?? -1;
      case "rating": return b.rating ?? -1;
      case "finished": return b.finished || "";
      case "added": return b.added || "";
      case "title": return b.title;
      default: return b.added || "";
    }
  };
  return [...books].sort((a, b) => {
    const ka = key(a), kb = key(b);
    if (ka < kb) return -1 * dir;
    if (ka > kb) return 1 * dir;
    return 0;
  });
}

function renderTable(parent: HTMLElement, books: Book[], columns: string[]): void {
  if (books.length === 0) { parent.createDiv({ cls: "rl-empty", text: "暂无书籍。" }); return; }
  const table = parent.createEl("table", { cls: "rl-table" });
  const thead = table.createEl("thead").createEl("tr");
  for (const c of columns) thead.createEl("th", { text: COLS[c]?.head ?? c });
  const tbody = table.createEl("tbody");
  for (const b of books) {
    const tr = tbody.createEl("tr");
    for (const c of columns) {
      const td = tr.createEl("td");
      (COLS[c]?.cell ?? ((bb: Book, t: HTMLElement) => t.setText("")))(b, td);
    }
  }
}

function filterBooks(books: Book[], spec: any, ctx: MarkdownPostProcessorContext): Book[] {
  let out = books;
  if (spec.status) out = out.filter(b => b.status === String(spec.status));
  if (spec.owned) out = out.filter(b => (b.owned || "none") === String(spec.owned));
  if (spec.priority) out = out.filter(b => b.priority === String(spec.priority));
  if (spec.finished === true) out = out.filter(b => !!b.finished);
  if (spec.rated === true) out = out.filter(b => b.rating != null);
  if (spec.match === "author") {
    const name = ctx.sourcePath.split("/").pop()?.replace(/\.md$/, "") ?? "";
    out = out.filter(b => b.author && b.author.includes(name));
  }
  if (spec.match === "category") {
    const name = ctx.sourcePath.split("/").pop()?.replace(/\.md$/, "") ?? "";
    out = out.filter(b => b.category === name);
  }
  return out;
}

function renderList(app: App, el: HTMLElement, ctx: MarkdownPostProcessorContext, spec: any): void {
  const books = filterBooks(collectBooks(app), spec, ctx);
  const sorted = sortBooks(books, String(spec.sort || "added"), String(spec.order || "desc"));
  const limited = spec.limit ? sorted.slice(0, Number(spec.limit)) : sorted;
  const columns: string[] = Array.isArray(spec.columns) && spec.columns.length
    ? spec.columns.map(String) : ["book", "author", "status"];
  const host = spec.title ? panel(el.createDiv({ cls: "rl-dash" }), String(spec.title))
                          : el.createDiv({ cls: "rl-dash" });
  renderTable(host, limited, columns);
}

/* ---------- 组合视图 ---------- */

function renderStats(app: App, el: HTMLElement): void {
  const books = collectBooks(app);
  const root = el.createDiv({ cls: "rl-dash" });
  if (books.length === 0) { root.createDiv({ cls: "rl-empty", text: "没有找到 #book 笔记。" }); return; }
  const count = (p: (b: Book) => boolean) => books.filter(p).length;

  const hero = root.createDiv({ cls: "rl-hero" });
  hero.createDiv({ cls: "rl-hero-title", text: "我的阅读" });
  hero.createDiv({ cls: "rl-hero-sub",
    text: `共 ${books.length} 本 · 已读 ${count(b => b.status === "已读")}`
      + ` · 在读 ${count(b => b.status === "在读")} · 想读 ${count(b => b.status === "想读")}` });

  const kpis = root.createDiv({ cls: "rl-kpis" });
  kpiCard(kpis, "📚", "书籍总数", books.length, "#0A84FF");
  kpiCard(kpis, "✅", "已读", count(b => b.status === "已读"), "#34C759");
  kpiCard(kpis, "📖", "在读", count(b => b.status === "在读"), "#FF9F0A");
  kpiCard(kpis, "🌱", "想读", count(b => b.status === "想读"), "#BF5AF2");
  kpiCard(kpis, "🛒", "待购", count(b => (b.owned || "none") === "none"), "#FF375F");

  const rated = books.filter(b => b.rating != null);
  const p1 = panel(root, "⭐ 评分分布");
  if (rated.length === 0) p1.createDiv({ cls: "rl-empty", text: "还没有打分的书。" });
  else {
    const bk: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    for (const b of rated) { const s = Math.round(b.rating as number); if (s >= 1 && s <= 5) bk[s]++; }
    const mx = Math.max(...Object.values(bk));
    [5, 4, 3, 2, 1].forEach(s => barRow(p1, "★".repeat(s), bk[s], mx, "linear-gradient(90deg,#FFB340,#FF9F0A)"));
  }

  const byCat: Record<string, number> = {};
  for (const b of books) { const k = b.category || "未分类"; byCat[k] = (byCat[k] || 0) + 1; }
  donut(panel(root, "🗂️ 分类占比"), Object.entries(byCat).sort((a, b) => b[1] - a[1]));

  heatmap(panel(root, "🔥 阅读热力（按读完月份）"), books);
}

function renderHome(app: App, el: HTMLElement, ctx: MarkdownPostProcessorContext): void {
  const books = collectBooks(app);
  const root = el.createDiv({ cls: "rl-dash" });
  if (books.length === 0) { root.createDiv({ cls: "rl-empty", text: "没有找到 #book 笔记。" }); return; }
  const count = (p: (b: Book) => boolean) => books.filter(p).length;

  const hero = root.createDiv({ cls: "rl-hero" });
  hero.createDiv({ cls: "rl-hero-title", text: "我的读书库" });
  hero.createDiv({ cls: "rl-hero-sub",
    text: `共 ${books.length} 本 · 已读 ${count(b => b.status === "已读")}`
      + ` · 在读 ${count(b => b.status === "在读")} · 想读 ${count(b => b.status === "想读")}` });

  const kpis = root.createDiv({ cls: "rl-kpis" });
  kpiCard(kpis, "📚", "书籍总数", books.length, "#0A84FF");
  kpiCard(kpis, "✅", "已读", count(b => b.status === "已读"), "#34C759");
  kpiCard(kpis, "📖", "在读", count(b => b.status === "在读"), "#FF9F0A");
  kpiCard(kpis, "🌱", "想读", count(b => b.status === "想读"), "#BF5AF2");

  const reading = sortBooks(books.filter(b => b.status === "在读"), "progress", "desc");
  renderTable(panel(root, "📖 正在读"), reading, ["book", "author", "progress"]);
  const done = sortBooks(books.filter(b => b.status === "已读" && b.finished), "finished", "desc").slice(0, 5);
  renderTable(panel(root, "✅ 最近读完"), done, ["book", "author", "rating", "finished"]);
  const want = sortBooks(books.filter(b => b.status === "想读"), "added", "desc").slice(0, 8);
  renderTable(panel(root, "🌱 想读"), want, ["book", "author", "category"]);
}

export default class ReadLensPlugin extends Plugin {
  async onload(): Promise<void> {
    this.registerMarkdownCodeBlockProcessor("readlens", (source, el, ctx) => {
      let spec: any = {};
      try { spec = parseYaml(source) || {}; } catch (e) { spec = {}; }
      const view = String(spec.view || "stats");
      try {
        if (view === "home") renderHome(this.app, el, ctx);
        else if (view === "list") renderList(this.app, el, ctx, spec);
        else if (view === "author") renderList(this.app, el, ctx, { ...spec, match: "author", columns: spec.columns || ["book", "status", "rating"] });
        else if (view === "topic") renderList(this.app, el, ctx, { ...spec, match: "category", columns: spec.columns || ["book", "author", "status", "rating"] });
        else renderStats(this.app, el);
      } catch (e: any) {
        el.createDiv({ cls: "rl-empty", text: "渲染失败：" + (e?.message || e) });
      }
    });
  }
}
