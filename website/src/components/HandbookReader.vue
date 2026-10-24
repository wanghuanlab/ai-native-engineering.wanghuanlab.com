<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
  watchEffect,
} from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { docs, resolveDocLink } from "../docs";

const props = defineProps<{ docId: string }>();
const current = computed(
  () => docs.find((doc) => doc.id === props.docId) || docs[0]!,
);
watchEffect(() => {
  document.title = `${current.value.title} · AI Native Engineering`;
});
const articleElement = ref<HTMLElement>();
const activeHeading = ref("");
const copyMessage = ref("");
const sourcePath = ref("");
const sourceDialog = ref<HTMLDialogElement>();
let observer: IntersectionObserver | undefined;

function slugify(text: string): string {
  return (
    text
      .normalize("NFKC")
      .toLowerCase()
      .trim()
      .replace(/[^\p{L}\p{N}\s_-]/gu, "")
      .replace(/\s+/g, "-") || "section"
  );
}

const content = computed(() => {
  const clean = DOMPurify.sanitize(
    marked.parse(current.value.markdown, { async: false }) as string,
    {
      USE_PROFILES: { html: true },
      FORBID_TAGS: ["style", "form", "input", "textarea", "button", "iframe"],
      FORBID_ATTR: ["style"],
    },
  );
  const fragment = document.createElement("div");
  fragment.innerHTML = clean;
  const used = new Map<string, number>();
  const headings: Array<{ id: string; text: string; level: number }> = [];
  let titleId = "document-title";
  let firstTitleRemoved = false;

  fragment.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach((heading) => {
    const label = heading.textContent || "";
    const base = slugify(label);
    const count = used.get(base) || 0;
    used.set(base, count + 1);
    const id = count ? `${base}-${count}` : base;
    const level = Number(heading.tagName.slice(1));
    heading.id = id;
    if (level === 1 && !firstTitleRemoved) {
      titleId = id;
      firstTitleRemoved = true;
      heading.remove();
      return;
    }
    headings.push({ id, text: label, level });
    const anchor = document.createElement("a");
    anchor.href = `#${id}`;
    anchor.className = "heading-anchor";
    anchor.setAttribute("aria-label", `链接到：${label}`);
    anchor.textContent = "#";
    heading.append(anchor);
  });

  fragment.querySelectorAll("a").forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (!href || href.startsWith("#")) return;
    const resolved = resolveDocLink(href, current.value);
    if (resolved) {
      link.href = resolved;
    } else if (/^(https?:|mailto:)/i.test(href)) {
      if (/^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(href)) {
        link.setAttribute("data-source-path", href);
        link.href = "#source-reference";
      } else {
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
    } else {
      link.setAttribute("data-source-path", href);
      link.href = "#source-reference";
    }
  });

  fragment.querySelectorAll("pre").forEach((pre) => {
    const code = pre.querySelector("code");
    if (!code) return;
    const wrapper = document.createElement("div");
    wrapper.className = "code-block";
    const toolbar = document.createElement("div");
    toolbar.className = "code-toolbar";
    const language = document.createElement("span");
    language.textContent = (
      code.className.match(/language-([\w+-]+)/)?.[1] || "code"
    ).toUpperCase();
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    button.textContent = "复制代码";
    button.setAttribute("aria-label", "复制这段代码");
    toolbar.append(language, button);
    pre.replaceWith(wrapper);
    wrapper.append(toolbar, pre);
  });
  fragment.querySelectorAll("table").forEach((table) => {
    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll";
    wrapper.tabIndex = 0;
    wrapper.setAttribute("role", "region");
    wrapper.setAttribute("aria-label", "文档表格，可横向滚动");
    table.replaceWith(wrapper);
    wrapper.append(table);
  });
  return { html: fragment.innerHTML, headings, titleId };
});

const tableOfContents = computed(() =>
  content.value.headings.filter((heading) => heading.level <= 3),
);
const readingMinutes = computed(() =>
  Math.max(1, Math.ceil(current.value.markdown.length / 450)),
);
const currentIndex = computed(() =>
  docs.findIndex((doc) => doc.id === current.value.id),
);
const nextDoc = computed(() => docs[currentIndex.value + 1]);
const previousDoc = computed(() => docs[currentIndex.value - 1]);

async function copyCode(button: HTMLButtonElement) {
  const code =
    button.closest(".code-block")?.querySelector("code")?.textContent || "";
  try {
    await navigator.clipboard.writeText(code);
    button.textContent = "已复制";
    copyMessage.value = "代码已复制到剪贴板";
    window.setTimeout(() => {
      if (button.isConnected) button.textContent = "复制代码";
      copyMessage.value = "";
    }, 2000);
  } catch {
    const selection = window.getSelection();
    const codeElement = button.closest(".code-block")?.querySelector("code");
    if (selection && codeElement) {
      const range = document.createRange();
      range.selectNodeContents(codeElement);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    copyMessage.value = "代码已选中，请使用 Ctrl+C 或 Command+C 复制";
  }
}

function onArticleClick(event: MouseEvent) {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest<HTMLButtonElement>(".copy-code");
  if (button) {
    void copyCode(button);
    return;
  }
  const reference =
    event.target.closest<HTMLAnchorElement>("[data-source-path]");
  if (reference) {
    event.preventDefault();
    sourcePath.value = reference.dataset.sourcePath || "";
    sourceDialog.value?.showModal();
  }
}

function downloadMarkdown() {
  const blob = new Blob([current.value.markdown], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = current.value.source.split("/").pop() || "handbook.md";
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function observeHeadings() {
  observer?.disconnect();
  await nextTick();
  if (!articleElement.value || !("IntersectionObserver" in window)) return;
  activeHeading.value = tableOfContents.value[0]?.id || "";
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries.find((item) => item.isIntersecting);
      if (entry) activeHeading.value = entry.target.id;
    },
    { rootMargin: "-110px 0px -65% 0px", threshold: 0 },
  );
  articleElement.value
    .querySelectorAll("h2, h3")
    .forEach((heading) => observer?.observe(heading));
  if (window.location.hash) {
    try {
      document
        .getElementById(decodeURIComponent(window.location.hash.slice(1)))
        ?.scrollIntoView();
    } catch {
      /* A malformed fragment should not interrupt reading. */
    }
  }
}

watch(current, observeHeadings);
onMounted(observeHeadings);
onBeforeUnmount(() => observer?.disconnect());
</script>

<template>
  <div class="handbook-shell">
    <div class="handbook-topline">
      <a class="back-home" href="/">
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path
            d="m11.5 5-5 5 5 5M7 10h10"
            stroke="currentColor"
            stroke-width="1.4"
          />
        </svg>
        返回首页
      </a>
      <span class="edition-label">规范 · 实践 · 协作</span>
    </div>

    <details class="mobile-doc-navigation">
      <summary>
        <span>文档导航</span
        ><span>{{ current.title }} <span aria-hidden="true">⌄</span></span>
      </summary>
      <nav aria-label="移动端手册导航">
        <a
          v-for="doc in docs"
          :key="doc.id"
          :href="`?doc=${doc.id}`"
          :aria-current="doc.id === current.id ? 'page' : undefined"
          >{{ doc.title }}</a
        >
        <a href="/training/index.html">图文培训版 ↗</a>
      </nav>
    </details>

    <div class="handbook-layout">
      <aside class="handbook-sidebar">
        <div class="sidebar-inner">
          <p class="navigation-label">研发手册</p>
          <nav aria-label="手册导航">
            <a
              v-for="doc in docs"
              :key="doc.id"
              :href="`?doc=${doc.id}`"
              :aria-current="doc.id === current.id ? 'page' : undefined"
            >
              <span>{{ doc.title }}</span>
              <span
                v-if="doc.id === current.id"
                class="doc-active-mark"
                aria-hidden="true"
                >↗</span
              >
            </a>
          </nav>
          <a class="training-link" href="/training/index.html">
            <span class="training-icon" aria-hidden="true">↗</span>
            <span
              ><strong>从一次团队培训开始</strong
              ><small>交互图解与完整需求演练</small></span
            >
          </a>
          <p class="sidebar-footnote">
            从同一套约定出发，<br />把协作落实到每一次交付。
          </p>
        </div>
      </aside>

      <section class="document-main" aria-labelledby="document-heading">
        <div
          v-if="props.docId && !docs.some((doc) => doc.id === props.docId)"
          class="document-notice"
        >
          没有找到该文档，已为你打开方案全文。
        </div>
        <header class="document-header" :id="content.titleId">
          <h1 id="document-heading">{{ current.title }}</h1>
          <p>{{ current.description }}</p>
          <div class="document-meta">
            <span>约 {{ readingMinutes }} 分钟阅读</span
            ><span class="meta-separator" aria-hidden="true">/</span
            ><span>与项目规范同步</span
            ><button type="button" @click="downloadMarkdown">
              下载 Markdown <span aria-hidden="true">↓</span>
            </button>
          </div>
        </header>
        <details class="mobile-table-of-contents" v-if="tableOfContents.length">
          <summary>本文目录 <span aria-hidden="true">⌄</span></summary>
          <nav aria-label="本文目录">
            <a
              v-for="heading in tableOfContents"
              :key="heading.id"
              :href="`#${heading.id}`"
              :class="{ nested: heading.level === 3 }"
              >{{ heading.text }}</a
            >
          </nav>
        </details>
        <article
          ref="articleElement"
          class="document-prose"
          v-html="content.html"
          @click="onArticleClick"
        ></article>
        <div class="document-source">
          <span>文档来源</span><code>{{ current.source }}</code>
        </div>
        <nav class="document-pagination" aria-label="相邻文档">
          <a v-if="previousDoc" :href="`?doc=${previousDoc.id}`"
            ><small>← 上一篇</small><strong>{{ previousDoc.title }}</strong></a
          >
          <span v-else></span>
          <a v-if="nextDoc" :href="`?doc=${nextDoc.id}`" class="next-document"
            ><small>下一篇 →</small><strong>{{ nextDoc.title }}</strong></a
          >
          <a v-else href="/" class="next-document"
            ><small>继续探索 →</small><strong>返回项目首页</strong></a
          >
        </nav>
      </section>

      <aside class="table-of-contents" v-if="tableOfContents.length">
        <div class="toc-inner">
          <p class="navigation-label">本文内容</p>
          <nav aria-label="本文章节">
            <a
              v-for="heading in tableOfContents"
              :key="heading.id"
              :href="`#${heading.id}`"
              :class="{
                nested: heading.level === 3,
                active: activeHeading === heading.id,
              }"
              :aria-current="
                activeHeading === heading.id ? 'location' : undefined
              "
              >{{ heading.text }}</a
            >
          </nav>
          <a class="back-to-top" :href="`#${content.titleId}`"
            >回到顶部 <span aria-hidden="true">↑</span></a
          >
        </div>
      </aside>
    </div>

    <span class="sr-only" aria-live="polite" role="status">{{
      copyMessage
    }}</span>
    <dialog
      ref="sourceDialog"
      class="source-dialog"
      @click="$event.target === sourceDialog && sourceDialog?.close()"
    >
      <div class="source-dialog-inner">
        <h2>在本地项目中查看</h2>
        <p>
          这是一条项目文件或本地服务引用。请在创建后的工程中打开对应路径，或启动服务后访问。
        </p>
        <code>{{ sourcePath }}</code>
        <button type="button" @click="sourceDialog?.close()">
          继续阅读 <span aria-hidden="true">↗</span>
        </button>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
.handbook-shell {
  background: #fff;
  color: #111318;
  min-height: 100svh;
  font-size: 16px;
  line-height: 1.7;
  padding: 0 clamp(24px, 4.2vw, 80px) 80px;
}
.handbook-topline {
  max-width: 1600px;
  margin: auto;
  min-height: 92px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.back-home {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #46505e;
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
}
.back-home svg {
  width: 18px;
  height: 18px;
}
.back-home:hover {
  color: #2864f0;
}
.edition-label {
  font-size: 13px;
  color: #505968;
}
.handbook-layout {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 220px minmax(0, 800px) 220px;
  gap: clamp(28px, 3.6vw, 62px);
  align-items: start;
  padding-top: 44px;
}
.sidebar-inner,
.toc-inner {
  position: sticky;
  top: 115px;
}
.handbook-sidebar,
.table-of-contents {
  align-self: stretch;
  min-width: 0;
}
.navigation-label {
  font-size: 14px;
  font-weight: 650;
  margin: 0 0 20px;
  padding: 0 12px;
  color: #202a38;
}
.handbook-sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.handbook-sidebar nav a {
  font-size: 14px;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #4c5768;
  text-decoration: none;
  padding: 12px;
  transition:
    color 0.18s,
    background 0.18s;
}
.handbook-sidebar nav a:hover {
  color: #111318;
  background: #f1f3f6;
}
.handbook-sidebar nav a[aria-current="page"] {
  color: #245ad7;
  background: #edf2ff;
  font-weight: 600;
}
.doc-active-mark {
  margin-left: auto;
  font-size: 17px;
  font-weight: 400;
}
.training-link {
  margin: 32px 0 0;
  padding: 20px 12px;
  background: #f4f6f9;
  display: flex;
  align-items: start;
  gap: 12px;
  color: #343e4d;
  text-decoration: none;
}
.training-link strong {
  font-size: 14px;
  font-weight: 600;
  display: block;
}
.training-link small {
  font-size: 13px;
  color: #526071;
  display: block;
  margin-top: 5px;
  line-height: 1.7;
}
.training-icon {
  color: #2864f0;
  font-size: 20px;
  line-height: 1.2;
}
.training-link:hover strong {
  color: #2864f0;
}
.sidebar-footnote {
  font-size: 13px;
  line-height: 1.9;
  color: #5d6777;
  margin: 28px 12px 0;
}
.document-main {
  min-width: 0;
  padding-bottom: 16px;
}
.document-header {
  padding-bottom: 28px;
  margin-bottom: 18px;
  scroll-margin-top: 115px;
}
.document-header h1 {
  font-size: clamp(30px, 3.2vw, 46px);
  line-height: 1.25;
  letter-spacing: -0.045em;
  font-weight: 600;
  margin: 0 0 20px;
  color: #111318;
}
.document-header > p {
  font-size: 16px;
  color: #404b5b;
  line-height: 1.9;
  margin: 0 0 25px;
}
.document-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  font-size: 13px;
  color: #556172;
  line-height: 1.7;
}
.meta-separator {
  color: #5f6a78;
}
.document-meta button {
  margin-left: auto;
  border: 0;
  background: #f0f3f7;
  padding: 8px 11px;
  color: #3b4a5e;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}
.document-meta button:hover {
  color: #245ad7;
  background: #edf2ff;
}
.document-meta button span {
  font-size: 16px;
  margin-left: 5px;
}
.document-notice {
  background: #edf2ff;
  color: #364b6e;
  padding: 14px 18px;
  font-size: 14px;
  margin: 0 0 25px;
}
.table-of-contents .navigation-label {
  font-size: 14px;
  padding: 0 11px;
  margin-bottom: 16px;
}
.table-of-contents nav {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: calc(100dvh - 275px);
  overflow: auto;
  padding: 0;
  scrollbar-width: thin;
  scrollbar-color: #c4cbd6 transparent;
}
.table-of-contents nav a {
  font-size: 13px;
  line-height: 1.75;
  color: #536073;
  text-decoration: none;
  padding: 7px 11px;
  display: block;
  transition:
    color 0.15s,
    background 0.15s;
}
.table-of-contents nav a.nested {
  padding-left: 23px;
  font-size: 13px;
  color: #566477;
}
.table-of-contents nav a:hover {
  color: #245ad7;
  background: #f2f5fa;
}
.table-of-contents nav a.active {
  color: #245ad7;
  background: #edf2ff;
}
.back-to-top {
  font-size: 13px;
  color: #43546c;
  text-decoration: none;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 11px;
  margin-top: 20px;
  background: #f4f6f9;
}
.back-to-top:hover {
  color: #2864f0;
  background: #edf2ff;
}
.document-prose {
  color: #303b4b;
  line-height: 1.95;
  overflow-wrap: anywhere;
  font-size: 16px;
}
.document-prose :deep(h1),
.document-prose :deep(h2),
.document-prose :deep(h3),
.document-prose :deep(h4),
.document-prose :deep(h5),
.document-prose :deep(h6) {
  color: #171c25;
  font-weight: 600;
  line-height: 1.5;
  letter-spacing: -0.02em;
  scroll-margin-top: 115px;
  position: relative;
}
.document-prose :deep(h2) {
  font-size: 25px;
  margin: 48px 0 20px;
}
.document-prose :deep(h3) {
  font-size: 20px;
  margin: 34px 0 15px;
}
.document-prose :deep(h4) {
  font-size: 18px;
  margin: 27px 0 12px;
}
.document-prose :deep(h5),
.document-prose :deep(h6) {
  font-size: 16px;
  margin: 24px 0 12px;
}
.document-prose :deep(p) {
  margin: 0 0 20px;
}
.document-prose :deep(strong) {
  font-weight: 600;
  color: #202b3b;
}
.document-prose :deep(a) {
  color: #245ad7;
  text-decoration-color: #99b1ec;
  text-underline-offset: 4px;
  text-decoration-thickness: 1px;
}
.document-prose :deep(a:hover) {
  text-decoration-color: #245ad7;
}
.document-prose :deep(.heading-anchor) {
  font-size: 16px;
  text-decoration: none;
  color: #677ea6;
  margin-left: 10px;
  opacity: 0;
  vertical-align: middle;
}
.document-prose :deep(h2:hover .heading-anchor),
.document-prose :deep(h3:hover .heading-anchor),
.document-prose :deep(.heading-anchor:focus-visible) {
  opacity: 1;
}
.document-prose :deep(ul),
.document-prose :deep(ol) {
  padding-left: 1.45em;
  margin: 15px 0 24px;
}
.document-prose :deep(li) {
  padding-left: 0.3em;
  margin: 7px 0;
}
.document-prose :deep(li > p) {
  margin-bottom: 8px;
}
.document-prose :deep(li::marker) {
  color: #4b5d79;
}
.document-prose :deep(blockquote) {
  background: #f2f5f9;
  padding: 20px 24px;
  margin: 24px 0;
  color: #36465d;
  font-size: 16px;
}
.document-prose :deep(blockquote p:last-child) {
  margin-bottom: 0;
}
.document-prose :deep(hr) {
  border: 0;
  height: 0;
  margin: 40px 0;
}
.document-prose :deep(code) {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 0.9em;
  line-height: 1.65;
  background: #eef1f5;
  color: #304057;
  padding: 3px 5px;
  border-radius: 2px;
  box-decoration-break: clone;
}
.document-prose :deep(.code-block) {
  border: 0;
  background: #f5f7fa;
  margin: 24px 0;
  overflow: hidden;
}
.document-prose :deep(.code-toolbar) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 0;
  min-height: 42px;
  padding: 0 16px;
  color: #52637a;
  font-size: 13px;
  background: #ecf0f5;
}
.document-prose :deep(.copy-code) {
  font-family: inherit;
  font-size: 13px;
  background: transparent;
  color: #3f5678;
  border: 0;
  cursor: pointer;
  padding: 10px 0;
  line-height: 1.4;
}
.document-prose :deep(.copy-code:hover) {
  color: #245ad7;
}
.document-prose :deep(pre) {
  overflow: auto;
  margin: 0;
  padding: 19px 20px;
  line-height: 1.8;
  scrollbar-width: thin;
  font-size: 14px;
}
.document-prose :deep(pre code) {
  padding: 0;
  background: none;
  color: #314864;
  border-radius: 0;
  white-space: pre;
  font-size: inherit;
}
.document-prose :deep(.table-scroll) {
  overflow: auto;
  border: 0;
  margin: 24px 0;
  scrollbar-width: thin;
}
.document-prose :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 16px;
  line-height: 1.8;
}
.document-prose :deep(th) {
  text-align: left;
  font-weight: 600;
  color: #26364d;
  background: #eff2f6;
  white-space: nowrap;
}
.document-prose :deep(th),
.document-prose :deep(td) {
  padding: 13px 16px;
  border-bottom: 1px solid #dde3eb;
  vertical-align: top;
  min-width: 105px;
}
.document-prose :deep(tr:last-child td) {
  border-bottom: 0;
}
.document-prose :deep(img) {
  max-width: 100%;
  height: auto;
}
.document-prose :deep(input[type="checkbox"]) {
  accent-color: #2864f0;
}
.document-source {
  display: flex;
  align-items: baseline;
  gap: 16px;
  flex-wrap: wrap;
  background: #f4f6f9;
  padding: 18px;
  margin-top: 48px;
  color: #4d5d74;
  font-size: 13px;
}
.document-source code {
  font-size: 13px;
  color: #425671;
  font-family: inherit;
}
.document-pagination {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 25px;
}
.document-pagination a {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-decoration: none;
  color: #313f54;
  padding: 18px;
  background: #f4f6f9;
}
.document-pagination small {
  font-size: 13px;
  color: #52637a;
}
.document-pagination strong {
  font-size: 15px;
  font-weight: 500;
}
.document-pagination a:hover {
  background: #edf2ff;
  color: #245ad7;
}
.document-pagination .next-document {
  text-align: right;
}
.mobile-doc-navigation,
.mobile-table-of-contents {
  display: none;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.source-dialog {
  max-width: 460px;
  width: calc(100% - 40px);
  padding: 0;
  border: 0;
  background: #fff;
  color: #111318;
  font-family: inherit;
}
.source-dialog::backdrop {
  background: #11131880;
}
.source-dialog-inner {
  padding: 34px;
}
.source-dialog h2 {
  font-size: 25px;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: -0.03em;
  margin: 0 0 16px;
}
.source-dialog-inner > p {
  font-size: 16px;
  color: #44546b;
  line-height: 1.9;
}
.source-dialog code {
  display: block;
  padding: 14px 16px;
  font-size: 14px;
  color: #334967;
  background: #eef2f7;
  overflow-wrap: anywhere;
}
.source-dialog button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 13px 16px;
  background: #111318;
  color: #fff;
  border: 0;
  margin-top: 25px;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}
.source-dialog button:hover {
  background: #2864f0;
}
.source-dialog button span {
  font-size: 17px;
}
@media (min-width: 1700px) {
  .handbook-layout {
    grid-template-columns: 245px minmax(0, 900px) 225px;
    justify-content: space-between;
  }
}
@media (max-width: 1250px) {
  .handbook-layout {
    grid-template-columns: 200px minmax(0, 1fr);
    gap: 40px;
    padding-top: 36px;
  }
  .table-of-contents {
    display: none;
  }
  .handbook-topline {
    min-height: 78px;
  }
  .mobile-table-of-contents {
    display: block;
    background: #f1f4f8;
    padding: 16px 18px;
    margin-bottom: 32px;
    font-size: 14px;
    color: #3f5069;
  }
  .mobile-table-of-contents summary {
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    list-style: none;
  }
  .mobile-table-of-contents summary::-webkit-details-marker {
    display: none;
  }
  .mobile-table-of-contents nav {
    margin-top: 14px;
    padding-top: 5px;
    max-height: 320px;
    overflow: auto;
  }
  .mobile-table-of-contents nav a {
    display: block;
    color: #435775;
    text-decoration: none;
    font-size: 13px;
    padding: 7px 0;
    line-height: 1.75;
  }
  .mobile-table-of-contents nav a.nested {
    padding-left: 16px;
    font-size: 13px;
  }
  .mobile-table-of-contents a:hover {
    color: #245ad7;
  }
}
@media (max-width: 800px) {
  .handbook-shell {
    padding: 0 28px 60px;
  }
  .handbook-layout {
    grid-template-columns: 1fr;
    gap: 0;
    padding-top: 32px;
  }
  .handbook-sidebar {
    display: none;
  }
  .mobile-doc-navigation {
    display: block;
    background: #f3f5f8;
    font-size: 14px;
  }
  .mobile-doc-navigation > summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    padding: 16px;
    cursor: pointer;
    list-style: none;
    color: #364b68;
  }
  .mobile-doc-navigation > summary::-webkit-details-marker {
    display: none;
  }
  .mobile-doc-navigation > summary > span:first-child {
    color: #4e607a;
    font-size: 13px;
  }
  .mobile-doc-navigation > summary > span > span {
    margin-left: 10px;
  }
  .mobile-doc-navigation nav {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3px 10px;
    padding: 0 10px 12px;
  }
  .mobile-doc-navigation nav a {
    display: block;
    text-decoration: none;
    color: #415672;
    padding: 10px;
    font-size: 13px;
  }
  .mobile-doc-navigation nav a[aria-current="page"] {
    background: #e5edff;
    color: #245ad7;
  }
  .mobile-doc-navigation nav a:hover {
    color: #245ad7;
  }
  .handbook-topline {
    min-height: 76px;
  }
  .document-header {
    padding-bottom: 25px;
    margin-bottom: 20px;
  }
  .document-header h1 {
    font-size: 36px;
  }
  .document-header > p {
    font-size: 16px;
  }
  .document-prose :deep(h2) {
    font-size: 24px;
  }
  .document-prose :deep(h3) {
    font-size: 20px;
  }
  .document-source {
    margin-top: 36px;
  }
}
@media (max-width: 460px) {
  .handbook-shell {
    padding-left: 20px;
    padding-right: 20px;
  }
  .handbook-topline {
    gap: 15px;
  }
  .back-home {
    font-size: 13px;
    gap: 5px;
  }
  .edition-label {
    font-size: 13px;
  }
  .document-header h1 {
    font-size: 32px;
  }
  .document-meta {
    gap: 8px;
    font-size: 13px;
  }
  .document-meta button {
    font-size: 13px;
    margin-left: 0;
    margin-top: 4px;
  }
  .document-prose {
    font-size: 16px;
    line-height: 1.95;
  }
  .document-prose :deep(h2) {
    font-size: 22px;
    margin-top: 38px;
  }
  .document-prose :deep(.heading-anchor) {
    opacity: 1;
    font-size: 16px;
    margin-left: 7px;
  }
  .document-prose :deep(pre) {
    padding: 15px;
    font-size: 13px;
  }
  .document-prose :deep(.code-toolbar) {
    padding-left: 14px;
    padding-right: 14px;
  }
  .document-prose :deep(blockquote) {
    padding: 17px;
  }
  .document-pagination {
    gap: 15px;
  }
  .document-pagination a {
    padding: 16px;
  }
  .document-pagination strong {
    font-size: 14px;
  }
  .source-dialog-inner {
    padding: 26px;
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
.document-prose :deep(ul) {
  list-style: disc;
}
.document-prose :deep(ol) {
  list-style: decimal;
}
</style>
