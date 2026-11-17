import json, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_PLUGIN = ROOT / "plugins_develop" / "llm_ocr_plugin"
OUT_DIR = ROOT / "dist"
OUT_FILE = OUT_DIR / "llm_ocr_plugin.ojplugin"

def main():
    OUT_DIR.mkdir(exist_ok=True)
    if OUT_FILE.exists(): OUT_FILE.unlink()

    with zipfile.ZipFile(OUT_FILE, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in SRC_PLUGIN.rglob("*"):
            if item.is_file():
                zf.write(item, item.relative_to(SRC_PLUGIN))

    print(f"[OK] Packed plugin: {OUT_FILE} ({OUT_FILE.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()