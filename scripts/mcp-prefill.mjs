#!/usr/bin/env node
// Pins fixed arguments onto a stdio MCP server's tools and hides them from the model.
// usage: mcp-prefill.mjs '<pins JSON>' <command> [args...]
// pins: { "<tool name or *>": { "<dotted.argument.path>": <value> } }; a tool's own pins win over "*".
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";

const [pinsJson, command, ...args] = process.argv.slice(2);
const pins = JSON.parse(pinsJson);
const child = spawn(command, args, { stdio: ["pipe", "pipe", "inherit"] });
const listRequests = new Set();
const pinsByTool = new Map();

// Removes the pinned property from the schema, and any object it empties; reports whether the schema had it.
function hide(schema, [key, ...rest]) {
  const property = schema?.properties?.[key];
  if (!property) return false;
  if (rest.length && !hide(property, rest)) return false;
  if (!rest.length || Object.keys(property.properties).length === 0) {
    delete schema.properties[key];
    schema.required = schema.required?.filter((name) => name !== key);
  }
  return true;
}

function set(target, [key, ...rest], value) {
  if (!rest.length) target[key] = value;
  else set((target[key] ??= {}), rest, value);
}

function pinTool(tool) {
  const applied = Object.entries({ ...pins["*"], ...pins[tool.name] })
    .map(([path, value]) => [path.split("."), value])
    .filter(([path]) => hide(tool.inputSchema, path));
  pinsByTool.set(tool.name, applied);
}

function relay(input, output, rewrite) {
  createInterface({ input }).on("line", (line) => {
    const message = JSON.parse(line);
    rewrite(message);
    output.write(`${JSON.stringify(message)}\n`);
  });
}

relay(process.stdin, child.stdin, (request) => {
  if (request.method === "tools/list") listRequests.add(request.id);
  if (request.method !== "tools/call") return;
  for (const [path, value] of pinsByTool.get(request.params.name) ?? []) {
    set((request.params.arguments ??= {}), path, value);
  }
});

relay(child.stdout, process.stdout, (response) => {
  if (listRequests.delete(response.id)) response.result?.tools?.forEach(pinTool);
});

process.stdin.on("end", () => child.stdin.end());
child.on("exit", (code) => process.exit(code ?? 1));
