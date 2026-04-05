---
name: create-ios-apps
description: Scaffold and build iOS/macOS apps from the terminal. Generates Xcode projects via XcodeGen, installs Makefile-based build/test/run tooling, and auto-resolves iOS simulators. Use when creating a new iOS or macOS app, adopting an existing Xcode project for CLI builds, or when the user needs to build, test, or run an Xcode project.
---

# Create iOS Apps

## Workflow

### 1. Verify the toolchain

```bash
skills/create-ios-apps/scripts/doctor.sh
```

Checks for Xcode, xcodebuild, xcrun, python3, and XcodeGen. Exits non-zero if any required tool is missing.

If XcodeGen is missing: `brew install xcodegen`

### 2. Scaffold or adopt

**New project:**

```bash
skills/create-ios-apps/scripts/scaffold.sh \
  --mode new \
  --name MyApp \
  --bundle-id com.example.MyApp \
  --platform ios \
  --ui swiftui \
  --output /path/to/MyApp
```

Renders a XcodeGen template, generates the `.xcodeproj`, and installs a Makefile + build scripts into the project.

| Flag | Required | Default | Notes |
|------|----------|---------|-------|
| `--name` | yes | | App and scheme name |
| `--bundle-id` | yes | | e.g. `com.example.MyApp` |
| `--platform` | yes | | `ios` or `macos` |
| `--ui` | no | `swiftui` | `swiftui`, `uikit` (ios only), `appkit` (macos only) |
| `--output` | yes | | Target directory (must be empty or nonexistent) |
| `--deployment-target` | no | `18.0` / `15.4` | iOS / macOS defaults |
| `--sim-name` | no | `auto` | iOS simulator name; `auto` picks newest iPhone |
| `--dry-run` | no | | Preview without writing files |

**Adopt existing project:**

```bash
skills/create-ios-apps/scripts/scaffold.sh \
  --mode adopt \
  --platform ios \
  --output /path/to/ExistingProject
```

Installs only the Makefile + build scripts. Does not touch source files. Auto-detects `--name` from the `.xcodeproj` if omitted. Pass `--force` to replace an existing Makefile and scripts.

### 3. Build, test, run

```bash
cd /path/to/project
make build              # Strict warnings-as-errors build
make test               # Unit tests
make run                # Launch (requires prior build)
make build-and-run      # Build then launch
make build-and-run-background  # Build then launch without blocking
make clean              # Remove build/ directory
make diagnose           # Print toolchain + project config
```

Auto-detects `.xcworkspace` over `.xcodeproj` (handles CocoaPods/SPM). iOS builds auto-resolve the best available simulator.

## Build artifacts

All output is isolated under `build/`:

```
build/
├── DerivedData/    # Xcode derived data
├── logs/           # Build/test logs (archived with timestamps)
│   ├── build.log
│   ├── test.log
│   └── archive/
└── cache/          # Module caches (clang, swift, SPM)
```

## Installed project scripts

After scaffolding, these are installed into the project's `scripts/` directory:

| Script | Purpose |
|--------|---------|
| `xcbuild.sh` | xcodebuild wrapper with logging, result bundles, and cache isolation |
| `resolve_sim_destination.sh` | Finds the best available iOS Simulator (prefers booted, then newest model) |
| `diagnose.sh` | Prints project configuration and tool versions |
| `run_app_ios_sim.sh` | Boots simulator, installs, and launches the app |
| `run_app_macos.sh` | Launches a macOS app |
| `clean.sh` | Removes the `build/` directory |
