[![Lifecycle:Experimental](https://img.shields.io/badge/Lifecycle-Experimental-339999)](<Redirect-URL>)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Build Status](https://github.com/bcgov/developer-experience-team/actions/workflows/build-mobile-app.yaml/badge.svg)](https://github.com/bcgov/developer-experience-team/actions/workflows/build-mobile-app.yaml)


This is the Developer Experience Team's mobile app for testing workflows. It is a basic React Native app and is not distributed to users.

See the [.github/workflows/build.yaml](.github/workflows/build.yaml) file for a basic CI/CD build.

It was built with [React Native](https://reactnative.dev), bootstrapped using [`@react-native-community/cli`](https://github.com/react-native-community/cli).  The code is from the [React Native Tutorial](https://reactnative.dev/docs/tutorial).

Below is the generic README text that is created with each new project. It is kept here for future reference on how to run the project locally.

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

For iOS, remember to install CocoaPods dependencies (this only needs to be run on first clone or after updating native deps).

The first time you create a new project, run the Ruby bundler to install CocoaPods itself:

```sh
bundle install
```

Then, and every time you update your native dependencies, run:

```sh
bundle exec pod install
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

Copilot will automatically:
1. **Scan** current versions and identify upgrade targets
2. **Baseline** pre-upgrade state (compile, tests, runtime)
3. **Upgrade** packages in correct order (React Native → ecosystem → tooling → native managers)
4. **Validate** TypeScript compilation, ESLint, Jest tests, iOS CocoaPods, Android Gradle
5. **Report** completed changes with git branch and commit info

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

If you're having issues getting the above steps to work, see the [Troubleshooting](https://reactnative.dev/docs/troubleshooting) page.

# Learn More

To learn more about React Native, take a look at the following resources:

- [React Native Website](https://reactnative.dev) - learn more about React Native.
- [Getting Started](https://reactnative.dev/docs/environment-setup) - an **overview** of React Native and how setup your environment.
- [Learn the Basics](https://reactnative.dev/docs/getting-started) - a **guided tour** of the React Native **basics**.
- [Blog](https://reactnative.dev/blog) - read the latest official React Native **Blog** posts.
- [`@facebook/react-native`](https://github.com/facebook/react-native) - the Open Source; GitHub **repository** for React Native.
