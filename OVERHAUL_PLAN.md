# Pomo Pet overhaul

## Product intent
A dependable, local-first focus companion: start a session immediately, keep time
accurately across reloads and backgrounding, and trust the saved work. Preserve
the dark charcoal and avocado identity, with clearer hierarchy and compact,
reachable controls on phones. Keep the existing Python companion supported.

## Implementation sequence
1. **Timer and state reliability:** persist an absolute deadline and the session's
   original duration/context; preserve paused progress when preferences change;
   stop at phase boundaries so unattended time never earns focus credit; recover
   safely from malformed storage and use local calendar dates/streaks.
2. **Interaction and data integrity:** render only the clock during ticks; preserve
   text-entry and keyboard focus; validate imports before replacing data, confirm
   destructive actions, avoid silently dropping tasks, guard stale pet requests,
   and make dialogs keyboard accessible. Synchronize multiple tabs safely.
3. **Experience:** simplify route headings, add an always-visible timer shortcut
   outside Focus, improve mobile control placement and scrolling, label controls,
   and make progress, empty states, and persistence feedback understandable.
4. **Offline and desktop fixes:** scope caches to this app, preserve healthy cached
   responses during server failures, test upgrades/offline use, and correct
   independently reproducible desktop timer/configuration defects.
5. **Validation and publication:** add targeted regression workflows, run the full
   Python and browser suites, check desktop/mobile layouts and keyboard flows,
   build the Python package, gate Pages deployment on CI, deploy through the
   existing GitHub Pages workflow, and smoke-test the actual published revision.

## Constraints
Preserve the staged package migration and existing user work. Keep the existing
hosting URL and local storage key, migrate old data defensively, and add no backend
or external data sharing. A complete test run is evidence of covered workflows,
not a claim that every possible browser/device condition has been tested.

## Initial findings
- Reload forces `running: false`; interval ticks rebuild every list and input.
- Any setting change resets a paused timer; mid-session duration changes inflate
  recorded minutes. Work automatically restarts after unattended breaks.
- UTC dates misclassify local days; streaks vanish until the first session today.
- Arbitrary JSON can erase history; malformed stored data can crash rendering.
- Adding a 31st task silently discards a task; Clear deletes history immediately.
- Pet requests race with newer selections; dialogs have no focus trap.
- Service worker activation deletes unrelated origin caches and caches errors.
- Narrow screens push Start far below the timer; short desktop views clip content.

Implementation and final validation results are recorded below.

## Implemented
Implementation, validation, and publication are complete. Preserved the pre-existing staged
package migration in its own commit. Added deadline-based browser timers and
single-tab editing, validated storage/imports, protected destructive actions,
restored text-entry focus, improved responsive routes, scoped offline caches,
fixed desktop elapsed-time/configuration/skip bugs, and bundled wheel resources.

## Validation record
- 189 Python tests pass, including desktop clock, config, atomic persistence, and
  static PWA checks. Tests now isolate real user preferences.
- PWA audit passes all five checks; Python source compiles; wheel and source
  distribution build, and wheel contents include required sprites and sounds.
- All 93 browser tests pass locally: 31 workflows across Chromium, Firefox, and
  WebKit, including automated WCAG checks on onboarding and all five routes.
- All three service-worker lifecycle and outage tests pass. The final wheel also
  passes installation in an isolated environment with its CLI and bundled assets.
- Desktop and phone screenshots inspected; controls tested at 320x568, 390x844,
  1024x600, and 1280x720. Fixed clipped small-phone controls and an unlabeled input.
- Verified WebKit offline recovery with the origin server stopped. Protocol
  offline emulation failed before service-worker dispatch, so the regression test
  now shuts down an isolated origin for all engines.
- GitHub CI passed for commit `624fc35075ea07c10d622b9ae6c99c21dae4bf00`:
  [CI run](https://github.com/someshfengde/pomo_pet/actions/runs/34677970875).
  Linux ran 187 Python tests with the two macOS-only tests skipped, all 93 browser
  tests, and all three service-worker tests. All 189 Python tests passed on macOS.
- GitHub Pages deployed that tested revision successfully:
  [deployment run](https://github.com/someshfengde/pomo_pet/actions/runs/34678099127).
- Production verified on 2026-09-12 at 06:27 UTC. The live HTML, JavaScript, CSS,
  and service worker exactly match the tested checkout. Onboarding, task creation
  and selection, timer start/pause/reload, all five routes, mobile controls, and
  offline reload passed with no JavaScript errors.
- [Live app](https://someshfengde.github.io/pomo_pet/) and
  [v1.2.38 release](https://github.com/someshfengde/pomo_pet/releases/tag/v1.2.38).
  The release automation changed only the package version and lockfile; the final
  source distribution and wheel build successfully at that version.
- GitHub reports zero open dependency alerts after the dependency updates.

## Behavior notes
Session phases now wait for the user to begin the next phase. Settings affect
future sessions. Imported backups replace history/tasks after confirmation.
Only one tab edits at once; other tabs retain navigation and take over on close.
Real OS notifications, installed iOS PWA behavior, and manual macOS window/tray
interactions require device-level validation beyond the automated suites.

- Updated Pillow to 12.3.0 and setuptools to 84.0.0 in the lockfile to address the
  14 dependency alerts reported by GitHub; Pillow's declared minimum is also patched.
- Added deterministic service-worker checks for scoped cache upgrades, server
  failures, network outages, and unrelated origins.
