/**
 * scripts/build-3d.js
 * Builds and bundles static 3D assets for GitHub Pages.
 * Ensures offline standalone capability for Three.js & OrbitControls.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const ROOT_DIR = path.resolve(__dirname, '..');
const ASSETS_DIR = path.join(ROOT_DIR, 'assets');
const DASHBOARD_ASSETS_DIR = path.join(ROOT_DIR, 'dashboard', 'assets');

const THREE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js';
const ORBIT_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    if (fs.existsSync(dest) && fs.statSync(dest).size > 1000) {
      console.log(`[CACHED] ${path.basename(dest)} already present (${fs.statSync(dest).size} bytes)`);
      return resolve();
    }

    console.log(`[FETCH] Downloading ${path.basename(dest)} from ${url}...`);
    const file = fs.createWriteStream(dest);
    
    https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        // Handle redirect
        https.get(res.headers.location, (redirectRes) => {
          redirectRes.pipe(file);
          file.on('finish', () => { file.close(); resolve(); });
        }).on('error', reject);
        return;
      }

      if (res.statusCode !== 200) {
        return reject(new Error(`Failed to download ${url}: status code ${res.statusCode}`));
      }

      res.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log(`[OK] Saved ${path.basename(dest)} (${fs.statSync(dest).size} bytes)`);
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function main() {
  console.log('=== 3D Assets Builder ===');
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
  fs.mkdirSync(DASHBOARD_ASSETS_DIR, { recursive: true });

  const threeDest = path.join(ASSETS_DIR, 'three.module.min.js');
  const orbitDest = path.join(ASSETS_DIR, 'OrbitControls.js');

  try {
    await downloadFile(THREE_URL, threeDest);
    await downloadFile(ORBIT_URL, orbitDest);

    // Mirror to dashboard/assets
    fs.copyFileSync(threeDest, path.join(DASHBOARD_ASSETS_DIR, 'three.module.min.js'));
    fs.copyFileSync(orbitDest, path.join(DASHBOARD_ASSETS_DIR, 'OrbitControls.js'));
    console.log('[OK] Mirrored assets to dashboard/assets/');
  } catch (err) {
    console.warn('[WARN] Asset download failed (offline mode):', err.message);
    console.log('[INFO] Web app will fallback gracefully to CDN via importmap');
  }

  console.log('✓ 3D Build step completed successfully!');
}

main();
