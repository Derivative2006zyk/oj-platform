const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..', '..')
const assetsDir = path.resolve(__dirname, '..', 'src-tauri', 'assets')

function rmrf(p) {
  if (fs.existsSync(p)) {
    fs.rmSync(p, { recursive: true, force: true })
  }
}

function copyFile(src, dst) {
  fs.mkdirSync(path.dirname(dst), { recursive: true })
  fs.copyFileSync(src, dst)
}

const EXCLUDE_DIRS = new Set([
  'tests',
  '.pytest_cache',
  '__pycache__',
  '.mypy_cache',
  '.ruff_cache',
])

const EXCLUDE_FILES = new Set([
  'tmp_publish.py',
])

function copyBackend(srcDir, dstDir) {
  fs.mkdirSync(dstDir, { recursive: true })
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (EXCLUDE_DIRS.has(entry.name)) continue
      if (entry.name === 'uploads') {
        // 只创建空目录
        const uploadsDst = path.join(dstDir, 'uploads')
        fs.mkdirSync(uploadsDst, { recursive: true })
        fs.writeFileSync(path.join(uploadsDst, '.gitkeep'), '')
        continue
      }
      copyBackend(path.join(srcDir, entry.name), path.join(dstDir, entry.name))
    } else {
      if (EXCLUDE_FILES.has(entry.name)) continue
      if (entry.name.endsWith('.pyc')) continue
      copyFile(path.join(srcDir, entry.name), path.join(dstDir, entry.name))
    }
  }
}

function main() {
  console.log('[prep-assets] root =', root)
  console.log('[prep-assets] assets dir =', assetsDir)

  rmrf(assetsDir)
  fs.mkdirSync(assetsDir, { recursive: true })

  // docker-compose.yml
  const composeSrc = path.join(root, 'docker-compose.yml')
  if (!fs.existsSync(composeSrc)) {
    console.error('[prep-assets] docker-compose.yml not found at', composeSrc)
    process.exit(1)
  }
  copyFile(composeSrc, path.join(assetsDir, 'docker-compose.yml'))

  // .env.example（可选）
  const envExampleSrc = path.join(root, '.env.example')
  if (fs.existsSync(envExampleSrc)) {
    copyFile(envExampleSrc, path.join(assetsDir, '.env.example'))
  } else {
    // 兜底：写一份最小 .env
    fs.writeFileSync(
      path.join(assetsDir, '.env.example'),
      'ADMIN_KEY=admin-key-change-me\n'
    )
  }

  // backend/
  const backendSrc = path.join(root, 'backend')
  if (!fs.existsSync(backendSrc)) {
    console.error('[prep-assets] backend/ not found at', backendSrc)
    process.exit(1)
  }
  copyBackend(backendSrc, path.join(assetsDir, 'backend'))

  console.log('[prep-assets] done')
}

main()