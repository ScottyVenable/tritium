# DesktopPal — pre-merge smoke checklist

Manual smoke. Run this on any PR that touches startup, windowing,
tray, hotkeys, persistence, or onboarding. Run it on `main` after
any merge wave. ~3 minutes start to finish if nothing is wrong.

If anything in this list fails, the build is not mergeable. There
are no "probably fine" items here.

---

## 0. Pre-flight

- [ ] Working tree clean (`git status` empty) or known-state.
- [ ] On the branch / SHA you intend to test. Note it:
      `Branch: ____________  SHA: ____________`

## 1. Clean build

- [ ] `dotnet build DesktopPal\DesktopPal.csproj -c Debug
      -p:EnableWindowsTargeting=true -nologo -v:m`
- [ ] Exit code 0.
- [ ] 0 errors, 0 warnings reported in minimal verbosity.

## 2. Launch + process liveness

- [ ] Delete or rename `%LOCALAPPDATA%\DesktopPal\logs\desktoppal.log`
      so the smoke log starts fresh. Keep the rest of the data dir.
- [ ] Launch the just-built exe and capture the PID:
      ```
      $p = Start-Process .\DesktopPal\bin\Debug\net10.0-windows\DesktopPal.exe -PassThru
      $pid = $p.Id
      ```
- [ ] Wait 10 seconds.
- [ ] `Get-Process -Id $pid` still returns the process. (If not:
      hard fail. Process died on startup. Check event log + log
      file. Stop here.)

## 3. Window + tray presence

- [ ] `(Get-Process -Id $pid).MainWindowHandle` is non-zero.
- [ ] System-tray icon visible in the notification area
      (manual eye check).
- [ ] Companion sprite drawn somewhere on screen
      (manual eye check).

## 4. Hotkey + interaction

- [ ] Default toggle hotkey hides the companion.
- [ ] Same hotkey shows it again.
- [ ] Tray icon's right-click menu opens.

## 5. First-run onboarding (only if testing first-run path)

- [ ] With `%LOCALAPPDATA%\DesktopPal\` deleted, launch the exe.
- [ ] Onboarding window appears.
- [ ] Completing onboarding writes `pet_state.json` under
      `%LOCALAPPDATA%\DesktopPal\` (NOT next to the exe).
- [ ] Re-launch: onboarding does not re-appear.

## 6. Persistence path sanity

- [ ] `%LOCALAPPDATA%\DesktopPal\pet_state.json` exists and is
      non-empty after a normal run.
- [ ] No `pet_state.json` written next to `DesktopPal.exe` in
      the bin output. (Old path. If it appears, something
      regressed back to a hard-coded path.)

## 7. Log file is clean

- [ ] `%LOCALAPPDATA%\DesktopPal\logs\desktoppal.log` contains
      `[MainWindow] Startup complete.`
- [ ] No lines matching `Exception`, `Unhandled`, `FATAL`, or
      `XamlParseException`.
- [ ] No lines matching `Cannot set Owner property`.
      (Specific to issue #52. Keep this assertion permanently;
      the cost is one grep.)

## 8. Event log is clean

- [ ] No new entries under Windows Application log, source
      `.NET Runtime`, IDs 1026 / 1023, since the launch
      timestamp.

## 9. Clean exit

- [ ] Close the app from tray (Quit) or `Stop-Process -Id $pid`.
- [ ] Process exits within 5 seconds.
- [ ] No new error entries in the log file or event log written
      during shutdown.

---

## Verdict

- [ ] **PASS** — all of the above green. Mergeable from a smoke
      perspective.
- [ ] **FAIL** — one or more items red. File / mailbox details
      with exact file:line where determinable. Do not merge.

Tester: ________  Date/time: ________  PID seen: ________

— Rook
