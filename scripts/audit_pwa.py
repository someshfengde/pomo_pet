"""Audit the static PWA for launch-critical requirements."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".lock",
    ".md",
    ".py",
    ".rb",
    ".sh",
    ".toml",
    ".txt",
    ".webmanifest",
    ".yml",
    ".yaml",
}
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.links: dict[str, str] = {}
        self.scripts: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = attrs_dict.get("name") or attrs_dict.get("property")
            if key:
                self.meta[key] = attrs_dict.get("content", "")
        elif tag == "link":
            rel = attrs_dict.get("rel")
            if rel:
                self.links[rel] = attrs_dict.get("href", "")
        elif tag == "script":
            self.scripts.append(attrs_dict)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def fail(message: str) -> None:
    raise AssertionError(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_head() -> HeadParser:
    parser = HeadParser()
    parser.feed(read(DOCS / "index.html"))
    return parser


def audit_manifest() -> None:
    manifest = json.loads(read(DOCS / "manifest.webmanifest"))
    required = {
        "name": "Pomo Pet",
        "short_name": "Pomo Pet",
        "display": "standalone",
        "start_url": "./",
        "scope": "./",
    }
    for key, value in required.items():
        if manifest.get(key) != value:
            fail(f"manifest {key!r} should be {value!r}")

    if not manifest.get("theme_color") or not manifest.get("background_color"):
        fail("manifest must define theme_color and background_color")

    icons = manifest.get("icons", [])
    sizes = {icon.get("sizes"): icon for icon in icons}
    for size in ("192x192", "512x512"):
        icon = sizes.get(size)
        if not icon:
            fail(f"manifest missing {size} icon")
        icon_path = DOCS / icon["src"].removeprefix("./")
        if not icon_path.exists():
            fail(f"manifest icon does not exist: {icon_path}")
        with Image.open(icon_path) as image:
            expected = tuple(map(int, size.split("x")))
            if image.size != expected:
                fail(f"{icon_path} expected {expected}, got {image.size}")

    screenshots = manifest.get("screenshots", [])
    preview = next((item for item in screenshots if item.get("src") == "./assets/preview.png"), None)
    if not preview:
        fail("manifest should include launch preview screenshot")
    if preview.get("sizes") != "1200x630":
        fail("preview screenshot should be declared as 1200x630")


def audit_html_metadata() -> None:
    head = parse_head()
    site_url = f"https://{read(ROOT / 'CNAME').strip().rstrip('/')}/"
    if "animated companion" not in head.title:
        fail("title should include launch-friendly app positioning")
    for key in (
        "description",
        "theme-color",
        "og:title",
        "og:description",
        "og:image",
        "twitter:card",
        "twitter:title",
        "twitter:image",
    ):
        if not head.meta.get(key):
            fail(f"missing meta tag: {key}")
    if head.links.get("manifest") != "./manifest.webmanifest":
        fail("manifest link is missing or incorrect")
    if head.links.get("canonical") != site_url:
        fail("canonical URL must match CNAME")
    if head.meta.get("og:url") != site_url:
        fail("og:url must match CNAME")
    for key in ("og:image", "twitter:image"):
        expected = f"{site_url}assets/preview.png"
        if head.meta.get(key) != expected:
            fail(f"{key} should point to the launch preview image")
    if head.meta.get("twitter:card") != "summary_large_image":
        fail("twitter card should use summary_large_image")
    if head.meta.get("og:image:width") != "1200" or head.meta.get("og:image:height") != "630":
        fail("og:image dimensions should be 1200x630")

    html = read(DOCS / "index.html")
    match = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)
    if not match:
        fail("missing JSON-LD structured data")
    structured = json.loads(match.group(1))
    if structured.get("@type") != "SoftwareApplication":
        fail("structured data must describe a SoftwareApplication")


def audit_service_worker() -> None:
    html = read(DOCS / "index.html")
    service_worker = read(DOCS / "sw.js")
    versioned_assets = re.findall(r'["\'](\./(?:app|styles)\.(?:js|css)\?v=\d+)["\']', html)
    for asset in versioned_assets:
        if asset not in service_worker:
            fail(f"service worker does not precache versioned asset: {asset}")
    for asset in (
        "./index.html",
        "./manifest.webmanifest",
        "./assets/icons/icon-192.png",
        "./assets/icons/icon-512.png",
        "./assets/pets/avacado/spritesheet.webp",
    ):
        if asset not in service_worker:
            fail(f"service worker does not precache {asset}")
    if 'event.request.mode === "navigate"' not in service_worker:
        fail("service worker should handle navigation requests")
    if "skipWaiting" not in service_worker or "clients.claim" not in service_worker:
        fail("service worker should activate updates promptly")


def audit_static_assets() -> None:
    for rel_path in (
        "index.html",
        "app.js",
        "styles.css",
        "sw.js",
        "manifest.webmanifest",
        "assets/preview.png",
        "assets/pets/avacado/spritesheet.webp",
    ):
        path = DOCS / rel_path
        if not path.exists() or path.stat().st_size == 0:
            fail(f"missing or empty PWA asset: {path}")

    with Image.open(DOCS / "assets/preview.png") as image:
        if image.size != (1200, 630):
            fail(f"preview image expected (1200, 630), got {image.size}")


def audit_no_secrets() -> None:
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ]
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.name == ".DS_Store" or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        content = read(path)
        for pattern in secret_patterns:
            if pattern.search(content):
                fail(f"secret-like token found in {path}")


def main() -> int:
    checks = (
        audit_static_assets,
        audit_manifest,
        audit_html_metadata,
        audit_service_worker,
        audit_no_secrets,
    )
    for check in checks:
        check()
    print(f"PWA audit passed: {len(checks)} checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PWA audit failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
