[![Lifecycle:Experimental](https://img.shields.io/badge/Lifecycle-Experimental-339999)](<Redirect-URL>)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Build Status](https://github.com/bcgov/developer-experience-team/actions/workflows/build-mobile-app.yaml/badge.svg)](https://github.com/bcgov/developer-experience-team/actions/workflows/build-mobile-app.yaml)


This is the Developer Experience Team's mobile app for testing workflows. It is a basic React Native app and is not distributed to users.

It was built with [React Native](https://reactnative.dev), bootstrapped using [`@react-native-community/cli`](https://github.com/react-native-community/cli).  The code is from the [React Native Tutorial](https://reactnative.dev/docs/tutorial).

Below is the generic README text that is created with each new project. It is updated as needed when the project is updated.

This is a new [**React Native**](https://reactnative.dev) project, bootstrapped using [`@react-native-community/cli`](https://github.com/react-native-community/cli).

# Getting Started

> **Note**: Make sure you have completed the [Set Up Your Environment](https://reactnative.dev/docs/set-up-your-environment) guide before proceeding.

## Step 1: Start Metro

First, you will need to run **Metro**, the JavaScript build tool for React Native.

To start the Metro dev server, run the following command from the root of your React Native project:

```sh
yarn start
```

## Step 2: Build and run your app

With Metro running, open a new terminal window/pane from the root of your React Native project, and use one of the following commands to build and run your Android or iOS app:

### Android

```sh
yarn android
```

To view logs:

```
adb logcat | grep -i DevExMobileTestApp
```

### iOS

For iOS, use the Ruby pinned in `.tool-versions`, not macOS's system Ruby.
With [asdf](https://asdf-vm.com/guide/getting-started.html) installed and its shims
on your `PATH`, run these commands from `DevExMobileTestApp`:

```sh
asdf plugin add ruby https://github.com/asdf-vm/asdf-ruby.git # Only if not already added
asdf install ruby
gem install bundler -v 4.0.23 --no-document
asdf reshim ruby
ruby --version
bundle --version
bundle install
```

The Bundler version above must match `BUNDLED WITH` in `Gemfile.lock`.
Ruby compilation may require build dependencies; see the
[asdf Ruby prerequisites](https://github.com/asdf-vm/asdf-ruby#before-asdf-install).
Other Ruby managers can use the same Ruby pin.

Install the locked CocoaPods dependencies from the iOS directory:

```sh
cd ios
bundle exec pod install --deployment
cd ..
```

After intentionally changing native dependencies, update the Pods lockfile with:

```sh
cd ios
bundle exec pod install
cd ..
```

For more information, please visit [CocoaPods Getting Started guide](https://guides.cocoapods.org/using/getting-started.html).

```sh
yarn ios
```

If everything is set up correctly, you should see your new app running in the Android Emulator, iOS Simulator, or your connected device.

This is one way to run your app — you can also build it directly from Android Studio or Xcode.

## Step 3: Modify your app

Now that you have successfully run the app, let's make changes!

Open `App.tsx` in your text editor of choice and make some changes. When you save, your app will automatically update and reflect these changes — this is powered by [Fast Refresh](https://reactnative.dev/docs/fast-refresh).

When you want to forcefully reload, for example to reset the state of your app, you can perform a full reload:

- **Android**: Press the <kbd>R</kbd> key twice or select **"Reload"** from the **Dev Menu**, accessed via <kbd>Ctrl</kbd> + <kbd>M</kbd> (Windows/Linux) or <kbd>Cmd ⌘</kbd> + <kbd>M</kbd> (macOS).
- **iOS**: Press <kbd>R</kbd> in iOS Simulator.

## Congratulations! :tada:

You've successfully run and modified your React Native App. :partying_face:

### Now what?

- If you want to add this new React Native code to an existing application, check out the [Integration guide](https://reactnative.dev/docs/integration-with-existing-apps).
- If you're curious to learn more about React Native, check out the [docs](https://reactnative.dev/docs/getting-started).

# Dependency Upgrades

This project uses AI-agent-driven automation for periodic React Native and npm package upgrades.

## Automated Upgrade Workflow

The upgrade process is split into two phases: **upgrade & validate**, then **review & create PR**.

### Phase 1: Upgrade and Validate

Ask Copilot to upgrade dependencies:
```
"Upgrade React Native in DevExMobileTestApp to the latest version"
```

Following the [full upgrade instructions](../.github/instructions/REACT_NATIVE_UPGRADE.instructions.md),
Copilot will:

1. **Protect existing work** - Inspect the branch and staged/unstaged changes,
   confirm scope, and preserve unrelated edits. Changes remain uncommitted unless
   explicitly requested; this phase does not push or create a PR.
2. **Research compatible targets** - Check current stable releases, migration
   guides, native templates, and toolchain compatibility rather than independently
   selecting the latest version of every package.
3. **Capture a baseline** - Run available TypeScript, lint, test, native build,
   and runtime checks, distinguishing existing failures from missing tools.
4. **Upgrade and migrate** - Update compatible JavaScript dependencies and
   lockfiles, migrate the compiled iOS and Android native projects, and align
   required Ruby/Bundler, CocoaPods, Xcode, Java, Gradle, and Android SDK tooling.
   Obtain approval before installing SDKs or making machine-wide changes.
5. **Review CI alignment** - Update
   [the mobile build workflow](../.github/workflows/build-mobile-app.yaml) when
   needed to match project runtime declarations, lockfiles, SDK requirements,
   dependency installation, and validation, preserving signing/upload behavior.
6. **Validate builds and behavior** - Run TypeScript, lint, Jest, CocoaPods,
   affected native tests/builds, and release builds when relevant and credentials
   permit. Launch both platforms where available, verify a cold start and the
   counter interaction, and diagnose Metro connectivity and Gradle warnings.
7. **Document and report evidence** - Update existing documentation and report
   actual versions, migrations, check results, remaining warnings, environment
   limits, and git status. Identify checks that failed, were blocked, or did not
   run; distinguish local validation from hosted CI execution.

An upgrade is not considered fully validated if native builds or app runtime
remain unverified. Any blockers are reported explicitly before handoff.

### Phase 2: Local Testing and PR Creation

After the upgrade is complete:

1. **Test locally** (you test, not agent):
   ```bash
   git diff                         # Review changes
   yarn ios                         # Test on iOS simulator
   yarn android                     # Test on Android emulator
   ```

2. **Verify everything works** - Check both platforms for functionality

3. **Approve and create PR** - Ask Copilot when ready:
   ```
   "Create a pull request for the React Native upgrade"
   ```
   
   Copilot will:
   - Organize commits in logical order
   - Write detailed PR description
   - Open PR on GitHub
   - Add appropriate labels

### Upgrade Sequence (Critical Order)
1. React Native core + React (tightly coupled)
2. React Native ecosystem (`@react-native/*` packages)
3. Babel & TypeScript compiler toolchain
4. Testing & linting tools (Jest, ESLint)
5. Native managers (CocoaPods for iOS, Gradle for Android)

### Manual Testing Commands
After upgrade is complete, use these to test locally:
```bash
# Test iOS
yarn ios                          # Build and run iOS simulator

# Test Android
yarn android                      # Build and run Android emulator

# Run validations
yarn tsc --noEmit                 # TypeScript check
yarn lint                         # ESLint check
yarn test                         # Run test suite
```

### Agent Instructions

The upgrade workflow is defined in two instruction files, automatically loaded by agents:

- **`.github/instructions/REACT_NATIVE_UPGRADE.instructions.md`** - Handles scanning, upgrading, and validating
- **`.github/instructions/REACT_NATIVE_CREATE_PR.instructions.md`** - Handles PR creation after local testing

# Troubleshooting

## Android emulator: Unable to load script

The debug app loads JavaScript from Metro; it does not include a release bundle.
If Metro is running but emulator logs show a timeout to `10.0.2.2:8081`, use
ADB forwarding instead:

1. Run `yarn start` from the app directory if Metro is not already running.
2. Run `adb -s emulator-5554 reverse tcp:8081 tcp:8081` (replace the device ID
   with the one from `adb devices`).
3. Open the app's developer menu (`adb -s emulator-5554 shell input keyevent 82`),
   choose **Change Bundle Location**, enter `localhost:8081`, and apply changes.

The bundle location is saved for this app on the emulator. Reapply ADB forwarding
after reconnecting or restarting the emulator. This does not change release builds.

## Xcode 27: Simulator.app not found

Xcode 27 replaces Simulator with Device Hub. Older React Native CLI versions
still try to open `Contents/Developer/Applications/Simulator.app`, causing
`yarn ios` to fail before the build starts.

This project pins the React Native CLI and its Android/iOS platform packages to
20.2.0, which supports Device Hub. After pulling the dependency update, run
`yarn install --frozen-lockfile`, then `yarn ios`. There is no need to reinstall
Xcode or create a Simulator.app symlink.

## iOS 27: UIScene lifecycle required

Apps built with the iOS 27 SDK must use the scene lifecycle. This project's
`SceneDelegate` in `ios/AppDelegate.swift` creates the window
and starts React Native when the scene connects. It is registered in
`ios/DevExMobileTestApp/Info.plist`, with multiple scenes disabled.

The Xcode project compiles `ios/AppDelegate.swift`, not the older duplicate at
`ios/DevExMobileTestApp/AppDelegate.swift`.

## Android build toolchain

The Android build configuration uses stable Android Gradle Plugin 9.5.0,
compile SDK 37, build-tools 37.0.0, target SDK 36, and the React Native 0.88.1
template's NDK 27.1.12297006. The project selects Java 26.0.2.1 in
`.tool-versions`. Gradle 9.6.1 supports Java 26 and is the newest stable
wrapper compatible with the React Native Gradle-plugin Kotlin version.
AGP 9.5.0 supplies built-in Kotlin support (Kotlin Gradle Plugin 2.2.10), so
the app no longer applies the separate Kotlin Android plugin or overrides its
AGP-managed Kotlin version.

The Android SDK setup was completed on 2026-11-03. `sdkmanager --list_installed`
confirms command-line tools 23.0.0, platform `android-37.0`, and CMake 3.30.5;
build-tools 37.0.0 and NDK 27.1.12297006 were already installed. Google
repository metadata uses the stable package ID `platforms;android-37.0`; the
shorthand `platforms;android-37` is not a package ID.

The host constructor in `MainApplication.kt` explicitly passes
`this@MainApplication` to avoid Kotlin resolving `this` to the host companion.
`./gradlew assembleDebug testDebugUnitTest` completed successfully on Java 26.
The debug APK is written to `android/app/build/outputs/apk/debug/app-debug.apk`.
No Android unit-test source files exist, so the unit-test task reports
`NO-SOURCE`; this is not evidence that device or emulator tests passed.
React Native's native build selected and installed CMake 3.22.1, alongside
the separately installed 3.30.5. Native code built for all four configured ABIs.
Gradle and React Native deprecation warnings remain; emulator testing is still
required.

### Gradle Problems report

The app's Gradle configuration uses explicit `property = value` assignments
to avoid Gradle 10's removal of Groovy space-assignment syntax.
After rebuilding with `./gradlew assembleDebug --warning-mode all`, the report
contains six remaining `Project.getProperties` deprecation warnings from
dependencies: four in Kotlin plugin internals during React Native Gradle-plugin
configuration, and two in React Native's dev-server IP/port lookups.
The debug build succeeds on Gradle 9.6.1. These warnings require upstream fixes
before moving to Gradle 10; they are not suppressed or patched locally.
See the [AGP 9.5 compatibility notes](https://developer.android.com/build/releases/agp-9-5-0-release-notes),
[Gradle Java compatibility table](https://docs.gradle.org/9.6.1/userguide/compatibility.html),
[AGP built-in Kotlin migration guide](https://developer.android.com/build/migrate-to-built-in-kotlin),
and [AGP 9.5 Kotlin Gradle Plugin dependency](https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/9.5.0/gradle-9.5.0.pom).

If you're having issues getting the above steps to work, see the [Troubleshooting](https://reactnative.dev/docs/troubleshooting) page.

# Learn More

To learn more about React Native, take a look at the following resources:

- [React Native Website](https://reactnative.dev) - learn more about React Native.
- [Getting Started](https://reactnative.dev/docs/environment-setup) - an **overview** of React Native and how setup your environment.
- [Learn the Basics](https://reactnative.dev/docs/getting-started) - a **guided tour** of the React Native **basics**.
- [Blog](https://reactnative.dev/blog) - read the latest official React Native **Blog** posts.
- [`@facebook/react-native`](https://github.com/facebook/react-native) - the Open Source; GitHub **repository** for React Native.

# Workflow

The repository's mobile build workflow is
[build-mobile-app.yaml](../.github/workflows/build-mobile-app.yaml).
Both jobs read Node from `.tool-versions`. Android CI selects Temurin Java 26
(the same Java feature release as the local asdf JDK), uses the checked-in
Gradle wrapper, and installs the required SDK platform, build-tools, NDK, and
CMake explicitly. Update these SDK selectors alongside `android/build.gradle`.
The Android job also runs TypeScript, lint, and Jest checks before the release build.
iOS CI selects the runner's latest stable Xcode, reads Ruby from `.tool-versions`,
and installs the Bundler version recorded in `Gemfile.lock`. The `Gemfile` reads
the same Ruby pin, keeping local development and CI aligned. CocoaPods runs through
`bundle exec pod install --deployment`. Signing and upload steps require
the repository's existing secrets and variables.