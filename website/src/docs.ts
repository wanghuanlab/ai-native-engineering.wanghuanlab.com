export interface HandbookDocument {
  id: string;
  title: string;
  description: string;
  source: string;
  markdown: string;
}

const handbookSources = import.meta.glob("../../handbook/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

import readme from "../../README.md?raw";
import changelog from "../../CHANGELOG.md?raw";

const definitions = [
  [
    "overview",
    "方案全文",
    "理解角色、流程、产物与质量门禁的完整约定。",
    "00-方案全文.md",
  ],
  [
    "engineer",
    "工程师指南",
    "从接到需求到提交验收，让每一步都有明确依据。",
    "01-工程师指南.md",
  ],
  [
    "lead",
    "技术负责人指南",
    "创建项目、认定分级、审批设计与复核发布。",
    "02-技术负责人指南.md",
  ],
  [
    "product",
    "产品经理指南",
    "提供需求、参与澄清，确认业务规则与验收标准。",
    "03-产品经理指南.md",
  ],
  [
    "operations",
    "运维实施指南",
    "从交付包到现场部署、版本升级与部署回执。",
    "04-运维实施指南.md",
  ],
  [
    "maintainer",
    "基线维护指南",
    "维护公共规则、验证基线与发布可同步的版本。",
    "05-基线维护指南.md",
  ],
  [
    "training",
    "团队培训手册",
    "完整需求示例、AI 提示词和 90 分钟团队演练。",
    "06-团队培训使用手册.md",
  ],
] as const;

export const docs: HandbookDocument[] = [
  ...definitions.map(([id, title, description, file]) => ({
    id,
    title,
    description,
    source: `handbook/${file}`,
    markdown: handbookSources[`../../handbook/${file}`] || "",
  })),
  {
    id: "readme",
    title: "快速开始",
    description: "创建第一个项目，了解工程骨架与日常维护方式。",
    source: "README.md",
    markdown: readme,
  },
  {
    id: "changelog",
    title: "版本记录",
    description: "查看基线版本的能力演进和具体变更。",
    source: "CHANGELOG.md",
    markdown: changelog,
  },
];

/** Resolve repository-relative Markdown links without depending on a public Git URL. */
export function resolveDocLink(
  href: string,
  current: HandbookDocument,
): string | undefined {
  const hashIndex = href.indexOf("#");
  const rawPath = hashIndex >= 0 ? href.slice(0, hashIndex) : href;
  const hash = hashIndex >= 0 ? href.slice(hashIndex) : "";
  if (!rawPath || /^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(rawPath))
    return undefined;

  let path: string;
  try {
    path = decodeURIComponent(rawPath.split("?")[0] || "");
  } catch {
    path = rawPath.split("?")[0] || "";
  }
  const directory = current.source.split("/").slice(0, -1);
  const parts = path.startsWith("/") ? [] : [...directory];
  for (const part of path.split("/")) {
    if (part === "..") parts.pop();
    else if (part && part !== ".") parts.push(part);
  }
  const normalized = parts.join("/");
  const target = docs.find((doc) => doc.source === normalized);
  if (target) return `?doc=${target.id}${hash}`;
  if (normalized === "handbook/README.md") return "?doc=overview";
  if (normalized.startsWith("handbook/training/")) {
    return `/training/${normalized.slice("handbook/training/".length)}${hash}`;
  }
  return undefined;
}
