/**
 * Resolve path prefix for GitHub Pages deployment.
 * Priority: ENV var > repo.json > fallback to "/"
 */

const fs = require('fs');
const path = require('path');

function resolvePathPrefix() {
  // 1. Environment variable
  let prefix = process.env.PATH_PREFIX;

  // 2. repo.json from preprocessing
  if (!prefix) {
    try {
      const repoDataPath = path.join(__dirname, '..', '_data', 'repo.json');
      const repoData = JSON.parse(fs.readFileSync(repoDataPath, 'utf-8'));
      prefix = repoData.base_url || '/';
    } catch (err) {
      console.log('[glintstone] No repo.json found, using / as path prefix');
      prefix = '/';
    }
  }

  // Ensure trailing slash
  if (!prefix.endsWith('/')) {
    prefix += '/';
  }

  return prefix;
}

module.exports = { resolvePathPrefix };
