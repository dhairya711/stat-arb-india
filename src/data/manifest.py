"""
src/data/manifest.py — File hashes, row counts, coverage. Phase 1 Guard #5 (reproducibility).
"""
import hashlib, json, logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)
LOG = logging.getLogger(__name__)
PROC = ROOT / CFG["paths"]["data_processed"]


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def build_manifest(directories: list[Path]) -> dict:
    manifest = {"generated_at": datetime.utcnow().isoformat(), "files": {}}
    for d in directories:
        for p in sorted(d.glob("*")):
            if p.is_file() and not p.name.startswith("."):
                manifest["files"][str(p.relative_to(ROOT))] = {
                    "hash": file_hash(p),
                    "size_bytes": p.stat().st_size,
                }
    return manifest


def save_manifest(manifest: dict, path: Path | None = None):
    path = path or (PROC / "manifest.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))
    LOG.info(f"Manifest saved: {path} ({len(manifest['files'])} files)")


def verify_manifest(path: Path | None = None) -> bool:
    """Phase 1 Guard #5: verify current hashes match saved manifest."""
    path = path or (PROC / "manifest.json")
    if not path.exists():
        LOG.error("No manifest found. Run manifest.py first.")
        return False
    saved = json.loads(path.read_text())
    ok, fail = 0, []
    for rel, info in saved["files"].items():
        p = ROOT / rel
        if not p.exists():
            fail.append(f"MISSING: {rel}")
            continue
        h = file_hash(p)
        if h != info["hash"]:
            fail.append(f"HASH MISMATCH: {rel} (saved={info['hash']}, now={h})")
        else:
            ok += 1
    if fail:
        LOG.error(f"Manifest verification FAILED: {len(fail)} issues")
        for f in fail[:10]: LOG.error(f"  {f}")
        return False
    LOG.info(f"Manifest verification PASSED: {ok} files match")
    return True


if __name__ == "__main__":
    import argparse, sys
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        ok = verify_manifest()
        sys.exit(0 if ok else 1)
    else:
        raw_dirs = [ROOT / CFG["paths"]["data_raw"] / "equity",
                    ROOT / CFG["paths"]["data_raw"] / "derivatives",
                    PROC]
        m = build_manifest([d for d in raw_dirs if d.exists()])
        save_manifest(m)
