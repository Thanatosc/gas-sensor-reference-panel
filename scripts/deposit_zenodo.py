"""Create Zenodo deposits for the code and data records, as unpublished drafts.

Deliberately stops short of publishing. Publishing mints a DOI and is
irreversible, so the final step is left to a human who has looked at the draft.

The token is read from the ZENODO_TOKEN environment variable and is never
written to disk, echoed, or stored in the state file.

    export ZENODO_TOKEN=...
    python scripts/deposit_zenodo.py --dry-run     # check what would happen
    python scripts/deposit_zenodo.py --code        # new version of 21973117
    python scripts/deposit_zenodo.py --data        # brand-new dataset record

Each run writes release/zenodo_deposit_state.json with deposition ids, reserved
DOIs and the upload checksums Zenodo reports back, so an interrupted run can be
inspected rather than blindly repeated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / "release"
STATE = RELEASE / "zenodo_deposit_state.json"
API = "https://zenodo.org/api"

CODE_PARENT_RECORD = "21973117"   # v1.0.0, the withdrawn analysis
CODE_ZIP = "gas-sensor-reference-panel-v2.0.0.zip"
DATA_ZIP = "gas-sensor-reference-panel-results-v1.0.0.zip"
CODE_META = "zenodo_code_metadata.json"
DATA_META = "zenodo_data_metadata.json"


def token() -> str:
    tok = os.environ.get("ZENODO_TOKEN", "").strip()
    if not tok:
        sys.exit("ZENODO_TOKEN is not set. export ZENODO_TOKEN=... first.")
    return tok


def call(method: str, url: str, tok: str, payload: dict | None = None,
         data: bytes | None = None, content_type: str = "application/json") -> dict:
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {tok}")
    if data is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1500]
        sys.exit(f"HTTP {exc.code} on {method} {url}\n{detail}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def upload(deposit: dict, archive: Path, tok: str) -> dict:
    """Upload one file, preferring the bucket API, and verify the checksum."""
    bucket = deposit.get("links", {}).get("bucket")
    local_md5 = md5(archive)
    if bucket:
        url = f"{bucket}/{archive.name}"
        result = call("PUT", url, tok, data=archive.read_bytes(),
                      content_type="application/octet-stream")
    else:
        sys.exit("deposit has no bucket link; aborting rather than guessing")
    remote = str(result.get("checksum", "")).replace("md5:", "")
    if remote and remote != local_md5:
        sys.exit(f"checksum mismatch after upload: local {local_md5} remote {remote}")
    print(f"    uploaded {archive.name} ({archive.stat().st_size / 1e6:.2f} MB), "
          f"md5 verified {local_md5}")
    return result


def deposit_code(tok: str, state: dict, dry: bool) -> None:
    meta = json.loads((RELEASE / CODE_META).read_text(encoding="utf-8"))
    archive = RELEASE / CODE_ZIP
    print(f"CODE record: new version of {CODE_PARENT_RECORD}")
    print(f"  title   : {meta['metadata']['title']}")
    print(f"  version : {meta['metadata']['version']}")
    print(f"  archive : {archive.name} ({archive.stat().st_size / 1e6:.2f} MB)")
    print(f"  sha256  : {sha256(archive)}")
    if dry:
        print("  (dry run, nothing sent)")
        return

    # Zenodo's legacy deposit API: newversion returns a draft of the concept.
    dep = call("POST",
               f"{API}/deposit/depositions/{CODE_PARENT_RECORD}/actions/newversion",
               tok)
    draft_url = dep["links"]["latest_draft"]
    draft = call("GET", draft_url, tok)
    dep_id = draft["id"]
    print(f"  draft id: {dep_id}")

    # A new version inherits the previous files; remove them before uploading.
    for f in call("GET", f"{API}/deposit/depositions/{dep_id}/files", tok):
        call("DELETE", f"{API}/deposit/depositions/{dep_id}/files/{f['id']}", tok)
        print(f"    removed inherited file {f.get('filename')}")

    upload(draft, archive, tok)
    updated = call("PUT", f"{API}/deposit/depositions/{dep_id}", tok, payload=meta)
    state["code"] = {
        "deposition_id": dep_id,
        "reserved_doi": updated.get("metadata", {}).get("prereserve_doi", {}).get("doi")
        or updated.get("doi"),
        "concept_doi": "10.5281/zenodo.21973116",
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "published": False,
        "draft_url": f"https://zenodo.org/uploads/{dep_id}",
    }
    save_state(state)
    print(f"  metadata set. Draft: https://zenodo.org/uploads/{dep_id}")


def deposit_data(tok: str, state: dict, dry: bool) -> None:
    meta = json.loads((RELEASE / DATA_META).read_text(encoding="utf-8"))
    archive = RELEASE / DATA_ZIP
    print("DATA record: new concept")
    print(f"  title   : {meta['metadata']['title']}")
    print(f"  version : {meta['metadata']['version']}")
    print(f"  archive : {archive.name} ({archive.stat().st_size / 1e6:.2f} MB)")
    print(f"  sha256  : {sha256(archive)}")
    if dry:
        print("  (dry run, nothing sent)")
        return

    draft = call("POST", f"{API}/deposit/depositions", tok, payload={})
    dep_id = draft["id"]
    print(f"  draft id: {dep_id}")
    upload(draft, archive, tok)
    updated = call("PUT", f"{API}/deposit/depositions/{dep_id}", tok, payload=meta)
    state["data"] = {
        "deposition_id": dep_id,
        "reserved_doi": updated.get("metadata", {}).get("prereserve_doi", {}).get("doi")
        or updated.get("doi"),
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "published": False,
        "draft_url": f"https://zenodo.org/uploads/{dep_id}",
    }
    save_state(state)
    print(f"  metadata set. Draft: https://zenodo.org/uploads/{dep_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", action="store_true")
    parser.add_argument("--data", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.code or args.data):
        args.code = args.data = True

    for name in ([CODE_ZIP, CODE_META] if args.code else []) + \
                ([DATA_ZIP, DATA_META] if args.data else []):
        if not (RELEASE / name).exists():
            sys.exit(f"missing {RELEASE / name}; run build_zenodo_packages.py first")

    tok = "" if args.dry_run else token()
    state = load_state()
    if args.code:
        deposit_code(tok, state, args.dry_run)
        print()
    if args.data:
        deposit_data(tok, state, args.dry_run)

    if not args.dry_run:
        print(f"\nstate written to {STATE}")
        print("\nBoth records are UNPUBLISHED DRAFTS. Review them in the browser,")
        print("then publish from the Zenodo UI. Publishing mints a DOI and cannot")
        print("be undone, so it is not automated here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
