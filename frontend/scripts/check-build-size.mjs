import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const distDir = join(process.cwd(), "dist");

function walk(dir) {
  let files = [];
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      files = files.concat(walk(fullPath));
    } else {
      files.push({ path: fullPath.replace(distDir + "\\", "").replace(distDir + "/", ""), size: stats.size });
    }
  }
  return files;
}

function format(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const files = walk(distDir).sort((a, b) => b.size - a.size);
const total = files.reduce((sum, file) => sum + file.size, 0);

console.log("\n📦 Production build size report\n");
console.log(`Total dist/: ${format(total)}\n`);
console.log("Largest files:");
for (const file of files.slice(0, 12)) {
  console.log(`  ${format(file.size).padStart(10)}  ${file.path}`);
}
console.log("");
