<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
} from "vue";
import { fullChecks, quickChecks, roles, stages } from "./content";

const HandbookReader = defineAsyncComponent(
  () => import("./components/HandbookReader.vue"),
);
const docId = new URLSearchParams(window.location.search).get("doc");
const menuOpen = ref(false);
const activeStage = ref(0);
const stage = computed(() => stages[activeStage.value]!);
const gate = ref<"quick" | "full">("quick");
const checks = computed(() =>
  gate.value === "quick" ? quickChecks : fullChecks,
);
const system = ref<"unix" | "windows">("unix");
const projectName = ref("myproject");
const validName = computed(() =>
  /^[a-z][a-z0-9]{1,19}$/.test(projectName.value),
);
const safeProject = computed(() =>
  validName.value ? projectName.value : "myproject",
);
const command = computed(() =>
  system.value === "unix"
    ? `bin/new-project.sh ~/work/${safeProject.value} -d project_code=${safeProject.value}\ncd ~/work/${safeProject.value}\n./scripts/setup.sh\n./scripts/verify.sh quick`
    : `bin\\new-project.cmd "%USERPROFILE%\\work\\${safeProject.value}" -d project_code=${safeProject.value}\ncd /d "%USERPROFILE%\\work\\${safeProject.value}"\nscripts\\setup.cmd\nscripts\\verify.cmd quick`,
);
const copyState = ref("复制命令");
const copyMessage = ref("");
const fileIndex = ref(1);
const files = [
  {
    name: "proposal.md",
    title: "变更提案",
    lines: [
      "为什么需要这次变更",
      "明确目标与本期范围",
      "保留需求来源与确认依据",
    ],
  },
  {
    name: "spec-delta.md",
    title: "规格增量",
    lines: [
      "将业务规则写入规格",
      "让验收标准可以验证",
      "由产品确认，工程师登记",
    ],
  },
  {
    name: "tasks.md",
    title: "实施任务",
    lines: ["明确允许修改的范围", "逐项记录验证命令", "让下一次会话有据可循"],
  },
  {
    name: "acceptance.md",
    title: "验收报告",
    lines: ["逐条对应验收标准", "保存测试与操作证据", "工程师完成人工验收"],
  },
];
const activeFile = computed(() => files[fileIndex.value]!);
let copyTimer: ReturnType<typeof setTimeout> | undefined;
let revealObserver: IntersectionObserver | undefined;

async function copyCommand() {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(command.value);
    } else {
      const area = document.createElement("textarea");
      area.value = command.value;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      const copied = document.execCommand("copy");
      area.remove();
      if (!copied) throw new Error("copy unavailable");
    }
    copyState.value = "已复制";
    copyMessage.value = "命令已复制到剪贴板";
  } catch {
    copyState.value = "请选择并复制";
    copyMessage.value = "浏览器未允许复制，请选中下方命令手动复制。";
  }
  clearTimeout(copyTimer);
  copyTimer = setTimeout(() => {
    copyState.value = "复制命令";
    copyMessage.value = "";
  }, 3200);
}
function stageKeys(event: KeyboardEvent) {
  const keys: Record<string, number> = {
    ArrowDown: 1,
    ArrowRight: 1,
    ArrowUp: -1,
    ArrowLeft: -1,
  };
  if (event.key in keys) {
    event.preventDefault();
    activeStage.value =
      (activeStage.value + keys[event.key]! + stages.length) % stages.length;
  } else if (event.key === "Home" || event.key === "End") {
    event.preventDefault();
    activeStage.value = event.key === "Home" ? 0 : stages.length - 1;
  } else return;
  nextTick(() =>
    document.getElementById(`stage-${activeStage.value}`)?.focus(),
  );
}
function closeMenu() {
  menuOpen.value = false;
}
function onEscape(event: KeyboardEvent) {
  if (event.key === "Escape") closeMenu();
}
onMounted(() => {
  document.addEventListener("keydown", onEscape);
  if (docId) return;
  const motionReduced = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  if (!motionReduced && "IntersectionObserver" in window) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-visible");
          revealObserver?.unobserve(entry.target);
        }
      },
      { threshold: 0.1 },
    );
    document
      .querySelectorAll("[data-reveal]")
      .forEach((el) => revealObserver?.observe(el));
  }
});
onBeforeUnmount(() => {
  clearTimeout(copyTimer);
  revealObserver?.disconnect();
  document.removeEventListener("keydown", onEscape);
});
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="site-header">
    <div class="header-inner container">
      <a class="brand" href="/" aria-label="AI Native Engineering 首页">
        <svg class="brand-mark" viewBox="0 0 44 44" aria-hidden="true">
          <rect width="44" height="44" fill="currentColor" />
          <path d="m9 31 10-19h5L14 31Zm12 0 10-19h5L26 31Z" fill="white" />
          <path d="M12 24h17v4H12z" fill="#2864f0" />
        </svg>
        <span>AI Native<span>Engineering</span></span>
      </a>
      <nav class="desktop-nav" aria-label="主导航">
        <a :href="docId ? '/#system' : '#system'">工程体系</a>
        <a :href="docId ? '/#workflow' : '#workflow'">工作流程</a>
        <a :href="docId ? '/#quality' : '#quality'">质量门禁</a>
        <a href="/?doc=training">研发手册</a>
      </nav>
      <a class="header-cta" :href="docId ? '/#start' : '#start'"
        >开始使用 <span aria-hidden="true">↗</span></a
      >
      <button
        class="menu-toggle"
        :aria-expanded="menuOpen"
        aria-controls="mobile-nav"
        :aria-label="menuOpen ? '关闭导航' : '打开导航'"
        @click="menuOpen = !menuOpen"
      >
        <span></span><span></span>
      </button>
    </div>
    <nav
      v-if="menuOpen"
      id="mobile-nav"
      class="mobile-nav container"
      aria-label="手机主导航"
      @click="closeMenu"
    >
      <a href="/#system">工程体系</a><a href="/#workflow">工作流程</a
      ><a href="/#quality">质量门禁</a><a href="/?doc=training">研发手册</a
      ><a href="/#start">开始使用</a>
    </nav>
  </header>

  <main v-if="!docId" id="main-content">
    <section class="hero container" aria-labelledby="hero-title">
      <div class="hero-copy">
        <h1 id="hero-title" class="hero-title">
          <span>让 AI 协作，</span><span>成为工程能力。</span>
        </h1>
        <p class="hero-description">
          以统一流程、工程规范与质量门禁，<br
            class="desktop-break"
          />连接需求、开发、验证和交付。
        </p>
        <div class="hero-actions">
          <a class="button button-primary" href="#start"
            >开始使用 <span aria-hidden="true">↗</span></a
          ><a class="text-link" href="/?doc=training">阅读研发手册</a>
        </div>
        <p class="hero-note">AI 协作工程化管理基线</p>
      </div>
      <div class="hero-art" data-ui aria-label="变更包产物结构交互示意">
        <div class="artifact-back">
          <span>docs / changes</span
          ><svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 18V6h14M9 14 19 4M12 4h7v7" />
          </svg>
        </div>
        <div class="artifact-paper">
          <div class="artifact-file">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6" /></svg
            ><code>{{ activeFile.name }}</code
            ><span>变更包</span>
          </div>
          <Transition name="file" mode="out-in">
            <div :key="fileIndex" class="paper-content">
              <p class="paper-title">{{ activeFile.title }}</p>
              <p class="paper-subtitle">把每次协作，变成可交接的依据。</p>
              <div class="paper-lines">
                <div v-for="line in activeFile.lines" :key="line">
                  <span class="square-check" aria-hidden="true"
                    ><svg viewBox="0 0 16 16">
                      <path d="m4 8 3 3 5-6" /></svg></span
                  ><span>{{ line }}</span>
                </div>
              </div>
            </div>
          </Transition>
          <div class="artifact-tabs" aria-label="查看变更包文件">
            <button
              v-for="(file, index) in files"
              :key="file.name"
              :aria-pressed="fileIndex === index"
              @click="fileIndex = index"
            >
              {{ file.title }}
            </button>
          </div>
        </div>
        <div class="artifact-base">
          <span>规则有源 · 过程有据 · 交付可查</span
          ><svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m4 12 5 5L20 6" />
          </svg>
        </div>
        <p class="artifact-caption">基于真实模板的产物结构示意</p>
      </div>
      <div class="hero-chain" aria-label="工程主线">
        <span>需求</span><span aria-hidden="true">→</span><span>规格</span
        ><span aria-hidden="true">→</span><span>实现</span
        ><span aria-hidden="true">→</span><span>验证</span
        ><span aria-hidden="true">→</span><span>交付</span>
        <p>每个环节，都有明确的输入与完成标准。</p>
      </div>
    </section>

    <section id="system" class="intro section" aria-labelledby="system-title">
      <div class="container">
        <div class="intro-heading">
          <h2 id="system-title" data-reveal>
            把个人经验，<br />变成团队基线。
          </h2>
          <p data-reveal>
            AI
            改变了代码的生产方式。统一的工程基线，让不同项目、不同工具和不同角色，在同一套规则下推进工作。
          </p>
        </div>
        <div class="principles">
          <div data-reveal>
            <p class="principle-title">一份规则源</p>
            <p>
              统一维护 AI 规则，生成多工具配置。换工具时，工程约定依然一致。
            </p>
          </div>
          <div data-reveal>
            <p class="principle-title">8 个标准 Skills</p>
            <p>
              从需求入库到发布打包，为每个环节提供明确的输入、动作与交接物。
            </p>
          </div>
          <div data-reveal>
            <p class="principle-title">两级质量校验</p>
            <p>
              quick 支撑开发反馈，full 覆盖完整验证。质量要求进入日常执行路径。
            </p>
          </div>
        </div>
      </div>
    </section>

    <section
      class="collaboration section dark-section"
      aria-labelledby="collaboration-title"
    >
      <div class="container collaboration-grid">
        <div class="collaboration-copy">
          <h2 id="collaboration-title" data-reveal>
            工具可以不同。<br />工程规则一致。
          </h2>
          <p data-reveal>
            团队共享一份规则与 Skills
            源文件，编译为各工具所需的配置，并按项目密级生成 AI 使用规则。
          </p>
          <a class="text-link light-link" href="/?doc=overview#6-ai-协作规范"
            >了解 AI 协作约定</a
          >
        </div>
        <div class="rules-fragment" data-ui data-reveal>
          <div class="rules-source">
            <span class="source-symbol" aria-hidden="true">⌘</span>
            <div>
              <strong>统一的规则与技能</strong>
              <p>
                <code>.ai/rules</code><span> + </span><code>.ai/skills</code>
              </p>
            </div>
          </div>
          <div class="compile-connector">
            <span aria-hidden="true">↓</span><span>编译生成</span>
          </div>
          <div class="tool-outputs">
            <div><strong>Codex</strong><code>AGENTS.md</code></div>
            <div><strong>Claude Code</strong><code>CLAUDE.md</code></div>
            <div><strong>Cursor</strong><code>.cursor/rules</code></div>
          </div>
          <p class="fragment-note">
            项目补充规则归项目维护，生成配置由源文件更新。
          </p>
        </div>
      </div>
    </section>

    <section
      id="workflow"
      class="workflow section"
      aria-labelledby="workflow-title"
    >
      <div class="container">
        <div class="section-heading">
          <h2 id="workflow-title" data-reveal>
            从一句需求，<br />到一次可靠交付。
          </h2>
          <p data-reveal>
            沿着真实产物推进协作。选择一个环节，查看它需要什么、产出什么，以及由谁负责。
          </p>
        </div>
        <div class="workflow-explorer" data-reveal>
          <div
            class="stage-list"
            role="tablist"
            aria-label="M / L 级标准研发流程"
            aria-orientation="vertical"
            @keydown="stageKeys"
          >
            <button
              v-for="(item, index) in stages"
              :id="`stage-${index}`"
              :key="item.id"
              role="tab"
              :aria-selected="activeStage === index"
              aria-controls="stage-panel"
              :tabindex="activeStage === index ? 0 : -1"
              @click="activeStage = index"
            >
              <span>{{ item.label }}</span
              ><svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 12h14m-5-5 5 5-5 5" />
              </svg>
            </button>
          </div>
          <div
            id="stage-panel"
            class="stage-panel"
            role="tabpanel"
            :aria-labelledby="`stage-${activeStage}`"
            tabindex="0"
            data-ui
          >
            <Transition name="stage" mode="out-in"
              ><div :key="activeStage">
                <div class="stage-meta">
                  <span>{{
                    activeStage === 8 ? "部署与归档" : "标准 Skill"
                  }}</span
                  ><code v-if="activeStage !== 8">{{ stage.skill }}</code
                  ><span v-else>运维部署 · 工程师归档</span>
                </div>
                <h3>{{ stage.title }}</h3>
                <p class="stage-description">{{ stage.description }}</p>
                <div class="stage-io">
                  <div>
                    <p class="field-label">输入</p>
                    <p>{{ stage.input }}</p>
                  </div>
                  <div>
                    <p class="field-label">输出</p>
                    <ul>
                      <li v-for="output in stage.outputs" :key="output">
                        {{ output }}
                      </li>
                    </ul>
                  </div>
                </div>
                <div class="stage-criteria">
                  <p class="field-label">完成条件</p>
                  <p>{{ stage.criteria }}</p>
                </div>
                <p class="stage-owner">{{ stage.owner }}</p>
              </div></Transition
            >
          </div>
        </div>
        <div class="workflow-footnote">
          <p>
            以上为 M / L 级标准路径。S 级小改按分级规则简化；AI
            起草与执行，人工承担确认、审批和验收。
          </p>
          <a class="text-link" href="/?doc=training">阅读完整流程</a>
        </div>
      </div>
    </section>

    <section
      id="quality"
      class="quality section"
      aria-labelledby="quality-title"
    >
      <div class="container quality-grid">
        <div>
          <h2 id="quality-title" data-reveal>质量要求，<br />进入执行路径。</h2>
          <p class="section-description" data-reveal>
            提交与推送钩子、统一校验入口和架构约束，让工程规范在每次改动中得到检查。
          </p>
          <div class="quality-note" data-reveal>
            <strong>机器检查，人工负责</strong>
            <p>自动校验提供证据，工程师完成业务验收，技术负责人复核与合并。</p>
            <a class="text-link" href="/?doc=training">查看门禁职责与边界</a>
          </div>
        </div>
        <div class="gate-fragment" data-ui data-reveal>
          <div class="gate-tabs" aria-label="选择质量校验范围">
            <button :aria-pressed="gate === 'quick'" @click="gate = 'quick'">
              quick <span>开发反馈</span></button
            ><button :aria-pressed="gate === 'full'" @click="gate = 'full'">
              full <span>完整验证</span>
            </button>
          </div>
          <div class="gate-body">
            <pre><code><span aria-hidden="true">$ </span>./scripts/verify.sh {{ gate }}</code></pre>
            <p class="gate-intro">
              {{
                gate === "quick"
                  ? "开发阶段，及时发现问题。"
                  : "合并、验收与发布前，核对完整证据。"
              }}
            </p>
            <Transition name="stage" mode="out-in"
              ><ul :key="gate">
                <li v-for="check in checks" :key="check">
                  <svg viewBox="0 0 20 20" aria-hidden="true">
                    <path d="m4 10 4 4 8-9" /></svg
                  ><span>{{ check }}</span>
                </li>
              </ul></Transition
            >
            <p class="gate-disclaimer">
              校验范围示意。实际执行结果以项目报告为准。
            </p>
          </div>
        </div>
      </div>
    </section>

    <section
      class="foundation section dark-section"
      aria-labelledby="foundation-title"
    >
      <div class="container">
        <div class="foundation-heading">
          <h2 id="foundation-title" data-reveal>
            可运行的起点。<br />可演进的工程。
          </h2>
          <p data-reveal>
            创建时复制骨架，让业务代码归项目所有；持续同步基线版本，让流程、规则与门禁共同演进。
          </p>
        </div>
        <div class="stack-table" data-reveal>
          <div>
            <span>后端工程</span><strong>Java 21 · Spring Boot 4</strong>
            <p>JPA · Flyway · Spring Modulith · ArchUnit</p>
          </div>
          <div>
            <span>前端工程</span><strong>Vue 3 · TypeScript</strong>
            <p>Element Plus · Pinia · 契约生成客户端</p>
          </div>
          <div>
            <span>数据与可视化</span><strong>PostgreSQL · 多方言</strong>
            <p>可选达梦、人大金仓与 Three.js 大屏</p>
          </div>
        </div>
        <div class="ownership-band" data-reveal>
          <div>
            <span>项目自主维护</span>
            <p>业务代码、项目规格与补充规则</p>
          </div>
          <span class="ownership-plus" aria-hidden="true">＋</span>
          <div>
            <span>基线持续托管</span>
            <p>研发流程、AI 规则与质量门禁</p>
          </div>
          <a class="text-link light-link" href="/?doc=maintainer"
            >了解版本同步</a
          >
        </div>
      </div>
    </section>

    <section
      id="handbook"
      class="handbook section"
      aria-labelledby="handbook-title"
    >
      <div class="container">
        <div class="section-heading">
          <h2 id="handbook-title" data-reveal>
            每个角色，<br />都有清晰的下一步。
          </h2>
          <p data-reveal>
            从自己的角色开始阅读，把共同约定落实到每天的工作中。
          </p>
        </div>
        <div class="role-grid">
          <a
            v-for="role in roles"
            :key="role.id"
            :href="`/?doc=${role.id}`"
            class="role-row"
            data-reveal
            ><div>
              <h3>{{ role.title }}</h3>
              <p>{{ role.description }}</p>
            </div>
            <span class="role-arrow" aria-hidden="true">↗</span></a
          >
        </div>
        <a
          class="training-link text-link"
          href="/training/index.html"
          target="_blank"
          rel="noopener"
          >打开离线图文培训版 <span class="sr-only">（新窗口）</span></a
        >
      </div>
    </section>

    <section id="start" class="start section" aria-labelledby="start-title">
      <div class="container start-grid">
        <div class="start-copy">
          <h2 id="start-title" data-reveal>下一个项目，<br />从这里开始。</h2>
          <p data-reveal>
            在基线仓库根目录运行创建命令，按提示选择项目画像，建立属于团队的工程起点。
          </p>
          <a class="text-link" href="/?doc=lead">查看完整准备步骤</a>
          <div class="prerequisites">
            <span>运行前准备</span>
            <p>
              Python 3.10+ 与 uv 或 Copier、Git、JDK 21、Docker、Node.js
              22+、pnpm 11。
            </p>
          </div>
        </div>
        <div class="start-fragment" data-ui data-reveal>
          <div class="system-tabs" aria-label="选择操作系统">
            <button :aria-pressed="system === 'unix'" @click="system = 'unix'">
              macOS / Linux</button
            ><button
              :aria-pressed="system === 'windows'"
              @click="system = 'windows'"
            >
              Windows
            </button>
          </div>
          <div class="project-input">
            <label for="project-name">项目代号</label
            ><input
              id="project-name"
              v-model="projectName"
              :aria-invalid="!validName"
              aria-describedby="project-help"
              maxlength="20"
              spellcheck="false"
              autocomplete="off"
            />
            <p id="project-help" :class="{ 'input-error': !validName }">
              {{
                validName
                  ? "2–20 位，小写字母开头，仅含小写字母和数字。"
                  : "请输入 2–20 位有效代号。下方暂用 myproject。"
              }}
            </p>
          </div>
          <div class="command-block">
            <div class="command-heading">
              <span>{{
                system === "unix" ? "终端" : "Windows 命令提示符（cmd）"
              }}</span
              ><button @click="copyCommand">
                {{ copyState
                }}<svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M9 9h11v12H9zM5 16H3V3h13v2" />
                </svg>
              </button>
            </div>
            <pre><code>{{ command }}</code></pre>
          </div>
          <p class="command-note">命令需在本地终端执行；本页仅生成命令。</p>
          <p class="sr-only" role="status">{{ copyMessage }}</p>
        </div>
      </div>
    </section>
  </main>
  <main v-else id="main-content">
    <Suspense
      ><HandbookReader :doc-id="docId" /><template #fallback
        ><div class="document-loading container" role="status">
          正在打开研发手册…
        </div></template
      ></Suspense
    >
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <a class="footer-wordmark" href="/"
          >AI Native<br />Engineering<span aria-hidden="true">↗</span></a
        >
        <div class="footer-description">
          <p>让 AI 协作，成为工程能力。</p>
          <span>统一规范 · 明确责任 · 保留证据</span>
        </div>
      </div>
      <div class="footer-bottom">
        <span>AI 协作工程化管理基线</span>
        <nav aria-label="页脚导航">
          <a href="/?doc=overview">方案全文</a
          ><a href="/?doc=training">团队培训</a
          ><a href="/?doc=changelog">版本记录</a>
        </nav>
        <span>元宇宙研发中心</span>
      </div>
    </div>
  </footer>
</template>
