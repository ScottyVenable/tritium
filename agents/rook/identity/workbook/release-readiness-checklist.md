# Release-readiness checklist (early stub)

Status: **DRAFT**. This is what a real release gate will look
like once we are tagging real builds. Several items are deferred
to later milestones and are marked `[deferred]`. Do not treat
this as the active gate yet — the active gate today is the
smoke checklist.

A release is gated on every item in the **Required** section
being green. Deferred items are tracked but do not block until
the milestone they are tied to.

---

## Required (when active)

### Source & history

- [ ] Target branch (`alpha` for alpha cuts, `main` for stable)
      points at the SHA you intend to ship. Note it:
      `Tag SHA: ____________`
- [ ] No open P0 issues in the target milestone.
- [ ] No open P1 issues in the target milestone.
- [ ] All PRs intended for this release are merged. No
      "we'll just sneak this in" PRs after the gate starts.

### Versioning

- [ ] `<Version>` in `DesktopPal\DesktopPal.csproj` matches the
      intended release version. (Today: not present. See note.)
- [ ] CHANGELOG.md has a top section for this version, dated,
      with categories (Added / Changed / Fixed / Removed) where
      they apply.
- [ ] CHANGELOG entries cite issue or PR numbers where
      applicable.
- [ ] Tag name matches version exactly (e.g. `v0.2.0` ↔
      `Version = 0.2.0`).

### Build

- [ ] `dotnet build` on the csproj: 0 errors, 0 warnings.
- [ ] CI workflow on the target SHA is green end-to-end.
- [ ] `scripts/build-release.ps1 -Version <ver>` succeeds
      locally on a clean working tree.
- [ ] Resulting `DesktopPal.exe` reports the expected version
      string in its file properties (right-click → Details).
- [ ] Artifact filename matches the contract:
      `DesktopPal-v<version>-win-x64\DesktopPal.exe`.

### Smoke

- [ ] `workbook\smoke-test-checklist.md` run against the
      release artifact (not just the dev build). All items
      pass. Tester signs.
- [ ] Smoke run on a clean machine or VM where DesktopPal has
      not been installed before. First-run onboarding path
      exercised.

### Packaging

- [ ] Single-file self-contained exe extracts and runs on a
      target machine without a separate .NET runtime install.
- [ ] App writes data to `%LOCALAPPDATA%\DesktopPal\` and
      nowhere else.
- [ ] Uninstall / removal is documented (delete folder + data
      dir). Until there is an installer, this is the contract.

### Release notes

- [ ] Human-readable release notes drafted. Not the changelog
      verbatim — a summary a non-technical user could read.
- [ ] Known issues section listed honestly. SmartScreen warning
      stays in the notes until the cert lands.

---

## Deferred (will be required later)

### Code signing `[deferred — needs cert]`

- [ ] EXE signed with a valid Authenticode certificate.
- [ ] Timestamp server used so the signature outlives cert
      expiry.
- [ ] SmartScreen reputation seeded (this takes time and
      downloads; cannot be checklist-completed in one shot).

### Installer `[deferred — Phase B]`

- [ ] Inno Setup `.iss` builds an installer.
- [ ] Installer signed with the same cert as the exe.
- [ ] Uninstaller removes program files, optionally preserves
      `%LOCALAPPDATA%\DesktopPal\`.
- [ ] Installer artifact published alongside the portable exe.

### Auto-update `[deferred — Phase C or later]`

- [ ] Update channel decided (alpha / stable).
- [ ] Update endpoint reachable from the release artifact.
- [ ] Rollback story documented.

### Distribution `[deferred]`

- [ ] GitHub Release page created with both portable exe and
      installer attached.
- [ ] SHA-256 of each artifact published in the release notes.
- [ ] Download link in README updated.

### Localization, telemetry, crash reporting `[deferred]`

Listed for completeness. None of these block alpha. They will
block 1.0.

---

## Sign-off

- Build verified by: ________  Date: ________
- Smoke verified by: ________  Date: ________
- Release approved by Scotty: ________  Date: ________

No unsigned releases reach a non-technical audience without an
explicit Scotty override and a SmartScreen warning in the
release notes. That is the rule until the cert lands.

— Rook
