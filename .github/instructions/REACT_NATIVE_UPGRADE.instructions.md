---
description: "Use when: upgrading React Native and dependencies in DevExMobileTestApp, aligning its mobile build workflow, migrating iOS and Android native templates and toolchains, or validating upgrade builds and emulator runtime behavior."
applyTo: "DevExMobileTestApp/**"
---

# React Native Full Upgrade Workflow

Use this workflow for requests such as "Upgrade React Native in DevExMobileTestApp
to the latest version". A dependency install is not a complete upgrade: migrate
both native projects, build them, and verify the app actually runs.

## 1. Establish scope and protect existing work

- Inspect the current branch, staged and unstaged diffs, and untracked files:
  ```bash
  git branch --show-current
  git status --short
  git diff
  git diff --cached
  ```
- Confirm the intended upgrade branch. If a new branch is needed, agree on it
  before creating it. If the tree is dirty, ask whether to proceed while
  preserving existing work; never automatically stash, revert, or commit it.
- Scope changes to the app and directly related build/documentation surfaces.
  Do not stage entire directories containing unrelated user changes.
- Keep changes uncommitted unless the user explicitly requests commits. Do not
  push, rewrite history, or create a PR during this phase.

## 2. Research a compatible target set

- Query the registry for the latest stable React Native release; exclude
  prereleases unless requested. Read its release notes, migration guidance, and
  version-matched community template. Use Upgrade Helper to compare the current
  and target native projects.
- Determine compatible React, renderer/test utilities, type definitions,
  React Native ecosystem packages, CLI/platform packages, Babel, TypeScript,
  Metro, Jest, and ESLint versions. Do not independently choose each package's
  latest version when peer or template constraints require a matched set.
- Check the CLI compatibility table and native launcher support for the installed
  Xcode and Android tooling. Upgrading React Native does not automatically
  upgrade its separately declared CLI packages.
- Inspect manifests, lockfiles, `.tool-versions`, native build files, and app CI.
  Include engine requirements, SDK selectors, and CI setup steps in the migration
  when they would otherwise disagree.
- Declare only runtime versions the app is intended and able to support. Keep
  package engine ranges aligned with React Native's requirements, the team's
  local runtime selection, and CI; do not imply compatibility with unsupported
  runtimes or leave the declared range broader than the tested support policy.
- For native tools, establish compatibility across:
  - Node and the repository's package manager.
  - Ruby, Bundler, CocoaPods, xcodeproj, Xcode, and simulator runtimes.
  - JDK, Gradle wrapper, Android Gradle Plugin (AGP), Kotlin, compile/target/min
    SDK levels, SDK build-tools, NDK, and CMake.
- Use official compatibility matrices and published stable releases. Prefer the
  newest mutually compatible set, not untested combinations. If a newer tool is
  blocked by React Native's included plugin or Kotlin metadata compatibility,
  record the reason for choosing an earlier compatible release.
- Derive versions anew for each upgrade. Do not reuse versions from a previous
  run or treat this guide as a version pin.

## 3. Capture a baseline

- Use the existing package manager and lockfile. Install/restore dependencies
  only if needed for validation or after manifest changes; do not generate a
  second lockfile or install global tools as an incidental workaround.
- Before version changes, capture the available baseline:
  ```bash
  # From DevExMobileTestApp/
  yarn tsc --noEmit
  yarn lint
  yarn test --runInBand
  ```
- Capture native build and runtime behavior where the environment permits.
  Separate pre-existing failures from upgrade regressions and missing tools.
  If a baseline cannot run, report that limitation instead of claiming a pass.
- Confirm actual tool selection in the shell and IDE:
  ```bash
  node --version
  java -version
  xcode-select -p
  xcodebuild -version
  bundle exec pod --version
  # From android/
  ./gradlew --version
  ```
  Run platform-specific commands only on supported hosts.

## 4. Upgrade JavaScript dependencies and configuration

1. Upgrade React Native and its compatible React runtime together. Keep the
   renderer and related typings compatible with React.
2. Update the React Native ecosystem and CLI/platform packages as a compatible
   group. Apply the version-matched template's configuration changes.
3. Update Babel, TypeScript, type definitions, Metro, testing, and lint tooling as
   required by the target. Revalidate coherent groups before proceeding.
4. Regenerate the existing lockfile through the package manager and inspect peer
   warnings. Resolve causes before considering narrow, justified resolutions.
   Do not add blanket overrides to force unsupported dependency combinations.
5. Preserve shared React Native TypeScript configuration by extending the
  version-matched base and overriding only intentional app-specific settings.
  If new library definitions or JSX types fail, first check compiler/type
  version compatibility rather than copying the base config, adding casts, or
  changing application behavior to conceal the errors.
6. Follow the target release's supported Jest preset and keep test dependencies
  compatible with the runner. Tests should exercise the real JavaScript
  implementations under test; limit mocks to native or external boundaries that
  cannot run in Jest. Do not replace an entire framework module, add an
  unrelated environment, polyfill around a misconfigured test setup, or
  suppress errors merely to manufacture a passing result.
7. Remove experiments and unused setup files created during troubleshooting.
   Never edit installed dependency files as a purported persistent fix.

## 5. Migrate and validate iOS

- Compare the actual compiled native sources with the target template. Inspect
  Xcode source membership and paths: duplicate AppDelegate files may exist, and
  changing an uncompiled copy will not change the app.
- Apply required AppDelegate/SceneDelegate, React Native factory, dependency
  provider, Info.plist, scene manifest, deployment target, and project changes.
  Preserve app identifiers, URL handling, orientations, and intended behavior.
  If scene lifecycle adoption is required, register the delegate and initialize
  the window and React Native from the appropriate lifecycle callback.
- Check Xcode selection, first-launch setup, installed runtimes, and available
  simulators. If the CLI tries to open an obsolete simulator application path,
  check whether the installed Xcode changed its launcher (such as Device Hub)
  and use a compatible published CLI. Do not create system-app symlinks or
  reinstall Xcode without establishing that its installation is actually broken.
- Update Gemfile constraints only as required. Keep Ruby, CocoaPods, and
  xcodeproj compatible with the Xcode project format. Use Bundler and update
  affected locked gems deliberately rather than updating every gem.
- Install gems after Gemfile changes, then install pods from `ios/`:
  ```bash
  # From DevExMobileTestApp/
  bundle install
  cd ios
  bundle exec pod install
  ```
  Diagnose failures before updating repositories or clearing caches; avoid
  indiscriminate cache deletion.
- A missing global `pod` does not mean CocoaPods is absent. Check
  `bundle exec pod --version`; run CLI doctor under Bundler when appropriate.
- Build and launch with `yarn ios`. To reuse Metro and select a known simulator,
  use the installed CLI's supported flags, for example:
  ```bash
  yarn ios --no-packager --udid <simulator-udid>
  ```
- Verify the app remains open and renders its UI. A successful CLI launch can
  still be followed by an immediate crash or blank screen. Inspect simulator
  logs/crash reports and capture the rendered screen; test the counter button.

## 6. Migrate and validate Android

- React Native CLI does **not** automatically migrate the Gradle wrapper or
  native project. Compare root/app Gradle files, settings, properties, manifests,
  MainApplication, and MainActivity with the target template.
- Select a JDK supported by the chosen Gradle/AGP combination. Distinguish the
  JVM running Gradle from the Java/Kotlin compilation target; they need not have
  the same version. A CLI doctor's supported range alone is not authoritative
  evidence for the entire build toolchain.
- Align `.tool-versions`, `JAVA_HOME`, any existing `JDK_HOME`, and Android
  Studio's Gradle JDK. Confirm selection with `./gradlew --version`. Do not
  commit machine-specific JDK paths or rely solely on ignored IDE settings.
- Update Gradle through wrapper tooling where possible and keep its generated
  files consistent. Update AGP/Kotlin together according to their migration
  guides. If AGP provides built-in Kotlin, migrate away from conflicting external
  Kotlin Android plugin configuration instead of applying both.
- Check Kotlin compatibility for both the app and React Native's included Gradle
  build. Do not force incompatible compiler versions or suppress metadata checks.
- Select compile SDK, target SDK, and build-tools deliberately; they are separate
  settings. Preserve the supported minimum unless a change is required, and
  test behavior changes caused by raising the target SDK.
- Inventory `$ANDROID_HOME` with SDK Manager or `sdkmanager --list_installed`.
  Install missing platforms, build-tools, platform-tools, command-line tools,
  NDK, and CMake as needed. Derive exact package IDs from current SDK metadata,
  not assumed directory names. Verify official downloads and obtain approval
  for SDK installation/license acceptance or machine-wide changes.
- Apply source-level API migrations needed by the target React Native/Kotlin
  versions, including host initialization and explicit outer receivers where
  Kotlin receiver resolution has changed. Do not stop at a successful task list.
- Update removed AGP APIs/default ProGuard configuration as required. Use
  explicit `property = value` Gradle DSL assignments for properties; preserve
  genuine method calls such as dependency and ProGuard-file declarations.
- Build and run the project's Android tests:
  ```bash
  # From android/
  ./gradlew assembleDebug testDebugUnitTest --warning-mode all --console=plain
  ```
  Report `NO-SOURCE` accurately: it means no tests ran, not that tests passed.
  Verify the APK exists. Run a release build as well if release configuration
  was changed, subject to available signing credentials; do not alter signing
  or add production credentials to make validation pass.
- Inspect the generated Problems report and, when needed, deprecation stack
  traces. Fix app-owned warnings. Attribute dependency warnings to their actual
  callers and check upstream compatible fixes. Never edit generated HTML or
  disable warnings to claim resolution. Ask before adding maintained dependency
  patches or expanding the agreed dependency scope; record accepted warnings.

## 7. Validate Metro connectivity and Android runtime

- Check `adb devices`, the intended device ID, and Metro's status on its
  configured port. Reuse an existing project Metro server rather than starting
  a competing server or terminating unrelated processes.
- Launch with `yarn android` (or install the built APK and launch its activity).
  Watch device logs and confirm the screen renders, not just that installation
  or activity launch succeeds.
- For "Unable to load script", first determine whether this is a debug build
  expecting Metro or a release build expecting packaged JavaScript. Do not
  bundle JavaScript into debug assets merely to mask a connection failure.
- If Metro is running but the emulator's host alias times out, route the app
  through ADB reverse forwarding:
  ```bash
  adb -s <device-id> reverse tcp:<metro-port> tcp:<metro-port>
  adb -s <device-id> reverse --list
  adb -s <device-id> shell input keyevent 82
  ```
  In the developer menu, set **Change Bundle Location** (or the equivalent
  debug-server setting) to `localhost:<metro-port>`, then reload.
- Explain that the app-local server preference persists but forwarding may need
  reapplying after reconnecting/restarting the emulator. Keep this development
  setting out of release code and do not hard-code a developer's LAN address.
- Cold-start the app, verify the button/counter UI, tap the button, and confirm
  the count increments. Use screenshots or UI hierarchy assertions as evidence.
  Clean temporary device files created for validation.

## 8. Review CI alignment when needed

Review [the mobile build workflow](../workflows/build-mobile-app.yaml) against
the upgraded project. Change only what the upgrade requires; the following are
review considerations, not a fixed sequence or a requirement to replace working
actions.

- Prefer shared project declarations for local and CI runtime selection where
  the setup action supports them. Check action inputs and working-directory
  behavior rather than assuming a version file is read automatically. Keep
  Node/package-manager, JDK/Gradle, and Ruby/Bundler selection compatible with
  the checked-in manifests, wrapper, and lockfiles.
- For Android, derive required SDK packages from the Gradle configuration and
  actual native build, including dependency-selected NDK/CMake requirements.
  Distinguish tools needed to produce the artifact from device/emulator tools
  needed only for installation or testing. Do not copy every locally installed
  SDK package into CI.
- Prefer the Android setup action's package input when it supports the required
  packages; avoid a duplicate installation command unless there is a specific
  need. Verify package IDs against Google's SDK metadata. If selecting a
  command-line tools release explicitly, check whether the action expects its
  download build number rather than its human-readable release version.
- For iOS, check runner/Xcode availability and project compatibility. Prefer a
  shared Ruby pin and the Bundler recorded in the lockfile over a CI-only
  override. If legacy metadata prevents this, migrate it with compatible
  Ruby/Bundler tooling, preserving locked gems unless compatibility requires
  changes. Verify frozen gem installation and CocoaPods deployment installation
  without unintended lockfile changes.
- Reconsider caches, dependency-install modes, and workflow path filters when
  affected by the upgrade. Ensure relevant project and workflow changes trigger
  the build, stale native caches do not conceal failures, and required quality
  checks remain covered. Preserve signing, upload behavior, secrets, and artifact
  paths unless a related change is required.
- Validate changed workflow syntax and action inputs, then exercise the affected
  build/install commands where feasible. Report local command results separately
  from hosted runner execution; static checks or a local release build do not
  prove that hosted signing and uploads work.

## 9. Final checks, documentation, and handoff

- Rerun TypeScript, lint, Jest, and the affected native builds after the last
  code change. Keep JavaScript tests, native unit tests, native builds, launch,
  and real UI interaction as separate validation results.
- Review the final diff and run `git diff --check`. Confirm existing user work
  remains intact. Persist dependency/native configuration changes and lockfiles,
  not generated reports, local SDK paths, build caches, or temporary test files.
- Update the existing app documentation with resolved versions, setup changes,
  troubleshooting, compatibility constraints, and observed outcomes. Use the
  actual date. Do not create a new upgrade report unless requested.
- Report:
  - Actual dependency/native tool versions before and after the upgrade.
  - Source/configuration migrations and why they were needed.
  - Each check as passed, failed, blocked, or not run; include test counts,
    platform/device coverage, and build artifact paths where useful.
  - Remaining upstream warnings and any environment, signing, or runtime limits.
  - Branch, current commit, and whether upgrade changes remain uncommitted.
- Do not declare the full upgrade complete while native builds or app runtime
  remain unverified. If blocked, state the exact blocker and next action.
- Offer user testing and diff review on both platforms. Only after explicit user
  approval, follow [the PR workflow](REACT_NATIVE_CREATE_PR.instructions.md).
  Its example checklists are not evidence: mark only checks actually performed,
  preserve unrelated work, and obtain permission before history rewriting.

## References

- [React Native releases](https://github.com/facebook/react-native/releases)
- [React Native community template](https://github.com/react-native-community/template)
- [Upgrade Helper](https://react-native-community.github.io/upgrade-helper/)
- [React Native environment setup](https://reactnative.dev/docs/set-up-your-environment)
- [React Native CLI compatibility](https://github.com/react-native-community/cli#compatibility)
- [Gradle compatibility](https://docs.gradle.org/current/userguide/compatibility.html)
- [Android Gradle Plugin releases](https://developer.android.com/build/releases/gradle-plugin)
- [Android SDK Manager](https://developer.android.com/tools/sdkmanager)
- [Android Debug Bridge](https://developer.android.com/tools/adb)
- [CocoaPods and Bundler](https://guides.cocoapods.org/using/a-gemfile.html)
