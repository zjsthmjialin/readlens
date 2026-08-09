import esbuild from "esbuild";
import process from "process";

const prod = process.argv.includes("production");

const banner = `/* ReadLens 阅镜 · Obsidian plugin — built bundle, do not edit directly */`;

await esbuild.build({
  banner: { js: banner },
  entryPoints: ["src/main.ts"],
  bundle: true,
  external: [
    "obsidian", "electron",
    "@codemirror/autocomplete", "@codemirror/collab", "@codemirror/commands",
    "@codemirror/language", "@codemirror/lint", "@codemirror/search",
    "@codemirror/state", "@codemirror/view",
    "@lezer/common", "@lezer/highlight", "@lezer/lr",
  ],
  format: "cjs",
  target: "es2018",
  logLevel: "info",
  sourcemap: prod ? false : "inline",
  treeShaking: true,
  outfile: "main.js",
  minify: prod,
});

console.log(prod ? "built (production)" : "built (dev)");
