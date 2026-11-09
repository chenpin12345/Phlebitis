// Where browser checks write their measurements: <storage area>/runtime/performance.
// The storage folder name comes from workspace-layout.json, so results never land in the code folder.
import fs from 'node:fs';
import path from 'node:path';

const workspace = path.resolve(import.meta.dirname, '../..');

function storageRoot() {
  try {
    const layout = JSON.parse(fs.readFileSync(path.join(workspace, 'workspace-layout.json'), 'utf8'));
    if (layout.storage) return path.join(workspace, layout.storage);
  } catch {
    // Older single-folder project: data lives next to the code.
  }
  return path.resolve(import.meta.dirname, '..');
}

export function performanceFile(name) {
  const dir = path.join(storageRoot(), 'runtime/performance');
  fs.mkdirSync(dir, {recursive: true});
  return path.join(dir, name);
}
