# Active Systems — Sol

Living doc. State as of 2026-05-05, late. Next-session-me, start here.

## Persistence (Paths.cs / PetState.cs)
**State:** Done. On main. Shipped 2026-05-05 ~02:30.
JSON state file at `%LOCALAPPDATA%\DesktopPal\state.json`, atomic write
via temp + replace. Paths.cs centralises every on-disk location so we
stop sprinkling `Environment.GetFolderPath` across the codebase.
PetState.cs is the serialisable snapshot. Load on startup, save on
significant change + on close. No issues observed in smoke tests.
Backwards-compat path is "missing file = first run."

## Companion window flow (lazy-init, deferred to Loaded)
**State:** Fixed tonight. On main.
`_companionWindow` is nullable, constructed in `MainWindow_OnLoaded`
via `EnsureCompanionWindow()`. All pre-Loaded callers (global hotkey,
tray toggle, settings, surface refresh, OnClosing) go through Ensure
and are null-safe. Pattern note in memories. .NET 10 owner-before-show
will not bite us again here, but audit any new Window class that sets
Owner in its ctor.

## Pet visuals (blue bear, idle bob/blink)
**State:** Shipped. On main.
Reference art `reference_buddy_blue_bear.png` at repo root. Idle bob
and blink driven by simple per-frame timer in CompanionWindow. Looks
right at the three target widths. No follow-up planned unless animation
state machine work changes the driver.

## Hotkey system (Ctrl+Alt+B)
**State:** Shipped. On main.
RegisterHotKey via WndProc, set up in OnSourceInitialized. Toggles
companion visibility. Important constraint: this fires before Loaded,
so the handler MUST route through EnsureCompanionWindow(). Documented
in build-flow preference and the owner-deferral memory.

## Onboarding window (first-run flow)
**State:** Shipped. On main.
Triggered from `ContentRendered` (already deferred, untouched by the
P0 fix). Runs once when state.json is absent, then sets the
"onboarded" flag and saves. Don't move the trigger off ContentRendered
without re-auditing — it's correct where it is.

## Garden plots (MVP)
**State:** Shipped. On main.
Minimal interactable plot surface. Plant / wait / harvest loop. Data
flows through the persistence layer so plots survive restart. Visual
polish and content density are Vex's domain from here; mechanics are
stable.

## AI service degraded mode
**State:** Shipped. On main.
When the AI service is unreachable or returns an error, we fall back
to scripted responses without surfacing a crash to the user. Logged,
not modal. Confirmed working through smoke tests with the network
disabled.

## Animation state machine
**State:** Groundwork only. Open follow-up.
Skeleton types and a state enum exist; no real transitions wired up.
Currently the pet has hardcoded idle behaviour driven by a timer.
Need to: define the transition table, integrate with the simulation
fixed-step service (when it exists), replace the ad-hoc timer in
CompanionWindow. Next-session candidate. File an issue before starting.

## Simulation fixed-step service
**State:** Designed in head, not on disk. Open follow-up.
Plan: accumulator-based fixed-dt update loop, render interpolation,
single service that owns "tick" and broadcasts to subscribers (pet
mood, garden growth, animation state machine). Nothing committed yet.
This is the keystone for the animation state machine — they should
land in that order. File an issue, draft the interface, then build.

---

## Next-session priorities (when fresh)
1. File issues for animation state machine and fixed-step service.
2. Wire fixed-step service first, animation second.
3. Audit any other `new XWindow(this, …)` call sites in MainWindow.
4. Look at CompanionWindow's idle timer — first candidate to migrate
   onto the fixed-step service when it exists.
