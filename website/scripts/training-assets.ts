import { readFile, readdir, realpath, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Plugin } from "vite";

const trainingRoot = fileURLToPath(
  new URL("../../handbook/training/", import.meta.url),
);
const documentIds: Record<string, string> = {
  "README.md": "overview",
  "00-方案全文.md": "overview",
  "01-工程师指南.md": "engineer",
  "02-技术负责人指南.md": "lead",
  "03-产品经理指南.md": "product",
  "04-运维实施指南.md": "operations",
  "05-基线维护指南.md": "maintainer",
  "06-团队培训使用手册.md": "training",
};

const contentTypes: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
};

/** Only the training wrapper's handbook links change; diagram assets stay byte-identical. */
function rewriteHandbookLinks(html: string): string {
  return html.replace(
    /href=(["'])\.\.\/([^"'?#]+\.md)(#[^"']*)?\1/g,
    (original, quote: string, file: string, fragment: string | undefined) => {
      let decoded: string;
      try {
        decoded = decodeURIComponent(file);
      } catch {
        return original;
      }
      const id = documentIds[decoded];
      return id
        ? `href=${quote}../?doc=${id}${fragment || ""}${quote}`
        : original;
    },
  );
}

function insideRoot(root: string, file: string): boolean {
  const relative = path.relative(root, file);
  return (
    relative !== ".." &&
    !relative.startsWith(`..${path.sep}`) &&
    !path.isAbsolute(relative)
  );
}

async function trainingFiles(
  directory = path.join(trainingRoot, "assets"),
): Promise<string[]> {
  const files: string[] = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const source = path.join(directory, entry.name);
    // Evidence artifacts are ordinary files. Do not follow symlinks outside this tree.
    if (entry.isDirectory()) files.push(...(await trainingFiles(source)));
    else if (entry.isFile()) files.push(source);
  }
  return files;
}

export function trainingAssets(): Plugin {
  return {
    name: "repository-training-assets",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        let pathname: string;
        try {
          pathname = decodeURIComponent((req.url || "").split("?")[0] || "");
        } catch {
          res.statusCode = 400;
          res.end("Invalid URL");
          return;
        }
        if (pathname !== "/training" && !pathname.startsWith("/training/")) {
          next();
          return;
        }
        if (
          pathname.includes("\\") ||
          pathname.includes("\0") ||
          pathname.split("/").some((part) => part === ".." || part === ".")
        ) {
          res.statusCode = 403;
          res.end("Forbidden");
          return;
        }
        if (req.method !== "GET" && req.method !== "HEAD") {
          res.statusCode = 405;
          res.setHeader("Allow", "GET, HEAD");
          res.end("Method not allowed");
          return;
        }
        const relative =
          pathname === "/training" || pathname === "/training/"
            ? "index.html"
            : pathname.slice("/training/".length);
        if (relative !== "index.html" && !relative.startsWith("assets/")) {
          res.statusCode = 404;
          res.end("Not found");
          return;
        }
        try {
          const root = await realpath(trainingRoot);
          const source = await realpath(path.resolve(trainingRoot, relative));
          if (!insideRoot(root, source)) {
            res.statusCode = 403;
            res.end("Forbidden");
            return;
          }
          if (!(await stat(source)).isFile()) {
            res.statusCode = 404;
            res.end("Not found");
            return;
          }
          const original = await readFile(source);
          const body =
            relative === "index.html"
              ? Buffer.from(rewriteHandbookLinks(original.toString("utf8")))
              : original;
          res.statusCode = 200;
          res.setHeader(
            "Content-Type",
            contentTypes[path.extname(source).toLowerCase()] ||
              "application/octet-stream",
          );
          res.setHeader("Content-Length", body.byteLength);
          res.setHeader("X-Content-Type-Options", "nosniff");
          res.setHeader("Cache-Control", "no-cache");
          res.end(req.method === "HEAD" ? undefined : body);
        } catch (error) {
          const code = (error as NodeJS.ErrnoException).code;
          if (code === "ENOENT" || code === "ENOTDIR") {
            res.statusCode = 404;
            res.end("Not found");
          } else next(error);
        }
      });
    },
    async generateBundle() {
      const index = await readFile(
        path.join(trainingRoot, "index.html"),
        "utf8",
      );
      this.emitFile({
        type: "asset",
        fileName: "training/index.html",
        source: rewriteHandbookLinks(index),
      });
      for (const source of await trainingFiles()) {
        this.emitFile({
          type: "asset",
          fileName: `training/${path.relative(trainingRoot, source).split(path.sep).join("/")}`,
          source: await readFile(source),
        });
      }
    },
  };
}
