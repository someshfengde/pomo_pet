"""Checks for the static Pomo Pet PWA."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_pwa_entrypoint_references_runtime_files():
    html = (DOCS / "index.html").read_text()

    assert 'rel="manifest"' in html
    assert "./styles.css?v=14" in html
    assert "./app.js?v=14" in html
    assert "startPauseButton" in html
    assert "notificationToggle" in html
    assert "wakeLockToggle" in html
    assert "petGallery" in html
    assert "weekChart" in html
    assert "insightBestDay" in html
    assert "insightEnergy" in html
    assert "insightMomentum" in html
    assert "exportStatsButton" in html
    assert "dailyGoalInput" in html
    assert "petMood" in html
    assert "intentionInput" in html
    assert "achievementList" in html
    assert "importStatsButton" in html
    assert "shareSummaryButton" in html
    assert "dataStatus" in html
    assert "onboardingOverlay" in html
    assert "breakPrompt" in html
    assert "nextBreakPromptButton" in html
    assert "sessionReviewOverlay" in html
    assert "sessionReviewInput" in html
    assert "saveReviewButton" in html
    assert "installStatus" in html
    assert "cacheStatus" in html
    assert "storageStatus" in html
    assert "https://codex-pets.net/" in html


def test_launch_metadata_is_share_ready():
    html = (DOCS / "index.html").read_text()

    assert "<title>Pomo Pet — Focus with an animated companion</title>" in html
    assert 'property="og:title"' in html
    assert 'property="og:image" content="https://placeholder-reset.example.com/assets/preview.png"' in html
    assert 'property="og:image:width" content="1200"' in html
    assert 'property="og:image:height" content="630"' in html
    assert 'name="twitter:card" content="summary_large_image"' in html
    assert 'rel="canonical" href="https://placeholder-reset.example.com/"' in html
    assert 'type="application/ld+json"' in html

    match = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)
    assert match
    structured_data = json.loads(match.group(1))
    assert structured_data["@type"] == "SoftwareApplication"
    assert structured_data["applicationCategory"] == "ProductivityApplication"
    assert structured_data["offers"]["price"] == "0"


def test_manifest_is_installable():
    manifest = json.loads((DOCS / "manifest.webmanifest").read_text())

    assert manifest["name"] == "Pomo Pet"
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "./"
    assert manifest["screenshots"][0]["src"] == "./assets/preview.png"
    assert manifest["screenshots"][0]["sizes"] == "1200x630"
    assert manifest["icons"]
    assert all(icon["src"].startswith("./assets/") for icon in manifest["icons"])


def test_service_worker_precaches_app_shell():
    service_worker = (DOCS / "sw.js").read_text()

    for required_asset in (
        "./index.html",
        "./styles.css?v=14",
        "./app.js?v=14",
        "./manifest.webmanifest",
        "./assets/icons/icon-192.png",
        "./assets/icons/icon-512.png",
        "./assets/preview.png",
        "./assets/pets/avacado/spritesheet.webp",
    ):
        assert required_asset in service_worker

    assert "self.addEventListener(\"fetch\"" in service_worker
    assert "caches.match" in service_worker
    assert "pomo-pet-pwa-v14" in service_worker
    assert 'event.request.mode === "navigate"' in service_worker
    assert '["script", "style", "worker"]' in service_worker


def test_web_app_supports_required_pwa_features():
    app = (DOCS / "app.js").read_text()

    assert "localStorage" in app
    assert "Notification.requestPermission" in app
    assert "navigator.serviceWorker.register" in app
    assert "beforeinstallprompt" in app
    assert "document.title" in app
    assert "wakeLock" in app
    assert "syncWakeLock" in app
    assert "releaseWakeLock" in app
    assert "long_break" in app
    assert "PETS" in app
    assert "DEFAULT_PET_META" in app
    assert "frameHeight: 208" in app
    assert "sheetWidth: 1536" in app
    assert "frames: 1" in app
    assert "applyPetSprite" in app
    assert "spriteAnimationName" in app
    assert "normalizePetMeta" in app
    assert "resolveCodexPetShare" in app
    assert "codexPetSlugFromUrl" in app
    assert "fallbackCodexPetFromUrl" in app
    assert "validationReport" in app
    assert "spritesheetUrl" in app
    assert "parseSize" in app
    assert "blueberry" in app
    assert "sunrise" in app
    assert "hue-rotate" in app
    assert "customPetUrl" in app
    assert "customPetSourceUrl" in app
    assert "customPetMeta" in app
    assert "customPetStatusText" in app
    assert "Paste a direct spritesheet or Codex Pets share link." in app
    assert "renderWeekChart" in app
    assert "renderInsights" in app
    assert "lastNDays" in app
    assert "averageSessionEnergy" in app
    assert "exportStats" in app
    assert "computeBond" in app
    assert "dailyGoalMinutes" in app
    assert "INTENTION_PRESETS" in app
    assert "ACHIEVEMENTS" in app
    assert "currentIntention" in app
    assert "importStatsFromFile" in app
    assert "shareSummary" in app
    assert "buildSummaryText" in app
    assert "completeOnboarding" in app
    assert "renderReadiness" in app
    assert "onboarded" in app
    assert "BREAK_PROMPTS" in app
    assert "normalizeBreakPromptIndex" in app
    assert "currentBreakPrompt" in app
    assert "nextBreakPrompt" in app
    assert "breakPromptIndex" in app
    assert "openSessionReview" in app
    assert "saveSessionReview" in app
    assert "normalizeEnergy" in app
    assert "reflection" in app
    assert "energy" in app


def test_pet_asset_is_deployable_with_docs():
    assert (DOCS / "assets" / "pets" / "avacado" / "spritesheet.webp").exists()
    assert (DOCS / "assets" / "icons" / "icon-192.png").exists()
    assert (DOCS / "assets" / "icons" / "icon-512.png").exists()
    assert (DOCS / "assets" / "preview.png").exists()
