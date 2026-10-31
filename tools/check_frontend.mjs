/** Parse and link every browser module without running DOM code. No npm dependencies. */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../app/static');
const modules = new Map();
function scan(directory) {
  for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
    const filename = path.join(directory, item.name);
    if (item.isDirectory()) scan(filename);
    else if (item.name.endsWith('.js')) {
      modules.set(
        filename,
        new vm.SourceTextModule(fs.readFileSync(filename, 'utf8'), { identifier: filename })
      );
    }
  }
}
scan(root);
function resolve(specifier, parent) {
  if (!specifier.startsWith('.'))
    throw new Error(`Only relative browser imports allowed: ${specifier}`);
  const filename = path.resolve(path.dirname(parent.identifier), specifier);
  const module = modules.get(filename);
  if (!module) throw new Error(`Missing module: ${filename}`);
  return module;
}
const visited = new Set();
function visit(module, stack = []) {
  if (stack.includes(module.identifier))
    throw new Error(`Circular imports: ${[...stack, module.identifier].join(' -> ')}`);
  if (visited.has(module.identifier)) return;
  for (const specifier of module.dependencySpecifiers)
    visit(resolve(specifier, module), [...stack, module.identifier]);
  visited.add(module.identifier);
}
for (const module of modules.values()) visit(module);
for (const module of modules.values()) {
  if (module.status === 'unlinked') await module.link(resolve);
}
console.log(`${modules.size} browser modules parsed and linked; no circular imports.`);
