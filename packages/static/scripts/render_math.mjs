import { mathjax } from "@mathjax/src/js/mathjax.js";
import { liteAdaptor } from "@mathjax/src/js/adaptors/liteAdaptor.js";
import { RegisterHTMLHandler } from "@mathjax/src/js/handlers/html.js";
import { TeX } from "@mathjax/src/js/input/tex.js";
import { CHTML } from "@mathjax/src/js/output/chtml.js";
import "@mathjax/src/js/input/tex/base/BaseConfiguration.js";
import "@mathjax/src/js/input/tex/ams/AmsConfiguration.js";
import "@mathjax/src/js/input/tex/newcommand/NewcommandConfiguration.js";

const TEX_PACKAGES = ["base", "ams", "newcommand"];

function createRenderer() {
  const adaptor = liteAdaptor();
  RegisterHTMLHandler(adaptor);

  const tex = new TeX({ packages: TEX_PACKAGES });
  const chtml = new CHTML({ fontURL: "fonts" });
  const document = mathjax.document("", { InputJax: tex, OutputJax: chtml });

  return { adaptor, chtml, document };
}

function decodeAttribute(value) {
  return value
    .replaceAll("&quot;", '"')
    .replaceAll("&apos;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&amp;", "&");
}

function extractMathJaxError(html) {
  const match = html.match(/data-mjx-error="([^"]*)"/);
  if (match === null) {
    return null;
  }
  return decodeAttribute(match[1]);
}

function normalizeItem(item, index) {
  if (typeof item !== "object" || item === null) {
    throw new Error(`item ${index} must be an object`);
  }
  if (typeof item.id !== "string" || item.id.length === 0) {
    throw new Error(`item ${index} must include a non-empty string id`);
  }
  if (typeof item.tex !== "string") {
    throw new Error(`item ${item.id} must include a string tex value`);
  }
  if (typeof item.display !== "boolean") {
    throw new Error(`item ${item.id} must include a boolean display value`);
  }
  return item;
}

function renderPayload(payload) {
  if (typeof payload !== "object" || payload === null || !Array.isArray(payload.items)) {
    throw new Error('input must be a JSON object with an "items" array');
  }

  const renderer = createRenderer();
  const rendered = [];
  const errors = [];

  for (const [index, rawItem] of payload.items.entries()) {
    let item;
    try {
      item = normalizeItem(rawItem, index);
      const node = renderer.document.convert(item.tex, { display: item.display });
      const html = renderer.adaptor.outerHTML(node);
      const mathJaxError = extractMathJaxError(html);
      if (mathJaxError !== null) {
        errors.push({ id: item.id, message: mathJaxError });
        continue;
      }
      rendered.push({ id: item.id, html });
    } catch (error) {
      errors.push({
        id: item?.id ?? String(index),
        message: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return {
    rendered,
    errors,
    css: renderer.adaptor.textContent(renderer.chtml.styleSheet(renderer.document)),
  };
}

function emptyCss() {
  const renderer = createRenderer();
  return renderer.adaptor.textContent(renderer.chtml.styleSheet(renderer.document));
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function runJsonMode() {
  let output;
  try {
    const input = await readStdin();
    output = renderPayload(JSON.parse(input));
  } catch (error) {
    output = {
      rendered: [],
      errors: [
        {
          id: "input",
          message: error instanceof Error ? error.message : String(error),
        },
      ],
      css: emptyCss(),
    };
  }

  process.stdout.write(`${JSON.stringify(output)}\n`);
  if (output.errors.length > 0) {
    process.exitCode = 1;
  }
}

function assertSelfTest(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function runSelfTest() {
  const valid = renderPayload({
    items: [
      { id: "display", tex: "\\int_0^1 x^2 dx", display: true },
      { id: "macro-definition", tex: "\\newcommand{\\vect}[1]{\\mathbf{#1}}", display: false },
      { id: "macro-use", tex: "\\vect{x}", display: false },
    ],
  });
  assertSelfTest(valid.errors.length === 0, "expected valid math to render without errors");
  assertSelfTest(valid.rendered.length === 3, "expected all valid items to render");
  assertSelfTest(valid.rendered[0].html.includes('display="true"'), "expected display math output");
  assertSelfTest(valid.rendered[2].html.includes("MathJax"), "expected MathJax HTML output");
  assertSelfTest(valid.css.length > 0, "expected MathJax CSS output");

  const invalid = renderPayload({
    items: [{ id: "bad", tex: "\\unknownmacro", display: false }],
  });
  assertSelfTest(invalid.errors.length === 1, "expected unknown control sequence to fail");
  assertSelfTest(
    invalid.errors[0].message.includes("Undefined control sequence"),
    "expected MathJax undefined-control diagnostic",
  );
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === "--self-test") {
    runSelfTest();
    return;
  }
  if (args.length > 0) {
    process.stderr.write(`unknown argument: ${args.join(" ")}\n`);
    process.exitCode = 2;
    return;
  }
  await runJsonMode();
}

await main();
