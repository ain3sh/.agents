---
name: react-doctor
description: Background knowledge for running react-doctor as part of the quality-ship gate. React-specific diagnostics on a changed-files diff. Not invoked directly.
user-invocable: false
---

# React Doctor

## When this skill applies

[#when-this-skill-applies](#when-this-skill-applies)

Detection signal (any one is sufficient): `react`, `react-dom`, `next`, `@remix-run/*`, `@tanstack/react-router`, or `@tanstack/react-start` listed as a dep, devDep, or peerDep in `package.json`. The `react` row in the quality-ship checklist binds to this signal.

No signal -> tag `no signal` in the gate checklist; do not run.

## Run

[#run](#run)

Always scope to the diff. Full-repo scans are slow and bury current-PR findings under legacy noise.

    npx -y react-doctor@latest . --diff <base-ref> --verbose

In monorepos with `turbo.json` or `pnpm-workspace.yaml`, scope to the affected workspace package:

    npx -y react-doctor@latest . --diff <base-ref> --project <pkg> --verbose

Required Node version: >=22. If the agent host is on Node 20, pass `--node-version 22` and react-doctor will provision via nvm:

    npx -y react-doctor@latest . --diff <base-ref> --node-version 22 --verbose

Never use `--fix` or `--ami`. Those flags hand off to Ami (millionco's coding agent) and conflict with the host agent (droid / claude code / codex).

## What it catches

[#what-it-catches](#what-it-catches)

react-doctor is a 177-rule oxlint plugin + knip dead-code in one CLI. Rules toggle automatically by detected framework, React version, and compiler setup. Category breakdown of the upstream plugin (under `packages/react-doctor/src/plugin/rules/`):

| Category | Rule count | Examples |
| --- | --- | --- |
| `state-and-effects` | 23 | `noFetchInEffect`, `noDerivedStateEffect`, `noCascadingSetState`, `noMirrorPropEffect`, `effectNeedsCleanup` |
| `performance` + `js-performance` | ~40 | `jsHoistRegexp`, `jsBatchDomCss`, `asyncParallel`, `asyncAwaitInLoop`, `noInlinePropOnMemoComponent` |
| `nextjs` | ~17 | `nextjsNoImgElement`, `nextjsNoUseSearchParamsWithoutSuspense`, `nextjsMissingMetadata`, `nextjsNoClientFetchForServerData` |
| `react-native` | ~25 | `rnNoRawText`, `rnPreferExpoImage`, `rnNoInlineFlatlistRenderitem` |
| `server` | 8 | `serverAuthActions`, `serverNoMutableModuleState`, `serverSequentialIndependentAwait` |
| `tanstack-query` + `tanstack-start` | ~20 | `queryMutationMissingInvalidation`, `tanstackStartServerFnValidateInput`, `tanstackStartNoUseEffectFetch` |
| `architecture` | ~10 | `noGiantComponent`, `noRenderInRender`, `noNestedComponentDefinition`, `noBarrelImport` |
| `correctness` | ~15 | `noLegacyClassLifecycles`, `noReactDomDeprecatedApis`, `noArrayIndexAsKey`, `noUncontrolledInput` |
| `security` | 2 | `noEval`, `noSecretsInClientCode` |
| `design` | ~25 | `noPureBlackBackground`, `noTinyText`, `noEmDashInJsxText`, `noJustifiedText` |
| `bundle-size` | ~6 | `noFullLodashImport`, `noMoment`, `preferDynamicImport` |
| knip | n/a | unused files, unused exports, unused types, duplicate exports |

## Triage policy

[#triage-policy](#triage-policy)

Diagnostics come tagged `{ plugin, rule, severity, category }`. Gate by category, not by total count:

- **`severity: "error"`** -> blocking, regardless of category.
- **`severity: "warning"`**:
  - `security/*`, `correctness/*`, `state-and-effects/*`, `server/*` -> blocking.
  - `performance/*`, `js-performance/*`, `bundle-size/*` -> blocking unless provably irrelevant (one-shot script, internal tool with single user, etc.). Document the rationale in the commit body if waived.
  - `architecture/*`, `nextjs/*`, `react-native/*`, `tanstack-*` -> blocking.
  - `design/*` -> advisory by default. Most are taste rules (`noEmDashInJsxText`, `noThreePeriodEllipsis`, `noPureBlackBackground`) and fight intentional design tokens. Enable per-repo if the project has a design system that aligns.
  - `knip/*` -> blocking if the unused export was added in the current diff; advisory if pre-existing.
- New violations only. `--diff <base-ref>` already scopes the scan; do not block on findings in unchanged files. If react-doctor reports findings outside the diff (it occasionally surfaces transitive dead-code from knip), filter to changed paths before gating.

The 0-100 score (75+ Great / 50-74 Needs work / <50 Critical) is **informational**. Do not gate on the score. The upstream leaderboard shows Sentry at 64 and tldraw at 84; both ship daily. Gate on individual diagnostics, not the rollup.

## Suppressing rules

[#suppressing-rules](#suppressing-rules)

Add `react-doctor.config.json` at repo root only when a rule fires repeatedly on legitimate patterns. Prefer file-scoped ignores over global rule disables:

    {
      "ignore": {
        "rules": ["react/no-danger"],
        "files": ["src/generated/**", "**/*.codegen.ts", "**/__mocks__/**"]
      }
    }

CLI flags always override config values. If a rule produces >5 false positives per scan across the repo, file an upstream issue at `millionco/react-doctor` rather than ignoring -- the project is v0.1.x and accepts rule-level feedback.

## What this skill does **not** do

[#what-this-skill-does-not-do](#what-this-skill-does-not-do)

- Do **not** run `curl -fsSL https://react.doctor/install-skill.sh | bash`. That installs vendor-authored agent rules globally into Cursor / Claude Code / Codex / Gemini CLI / etc. -- redundant with this skill, and unattended curl-pipe-bash from a third-party domain is not how this repo onboards tooling.
- Do **not** install `millionco/react-doctor@main` as a GitHub Action unless quality-ship runs are bypassed in CI. Local gate is sufficient.
- Do **not** treat this as a slop-scan replacement. The rule sets are disjoint: slop-scan flags structural noise (boilerplate density, pass-through wrappers, swallowed errors); react-doctor flags concrete React correctness/perf bugs. Both rows in the quality-ship table stay.

## Caveats

[#caveats](#caveats)

- v0.1.6, pre-1.0. CLI flags, rule IDs, and output format can change between minor versions. If a workflow breaks on upgrade, pin: `react-doctor@0.1.6` not `@latest`.
- Vendor (millionco) has pivoted twice: Million.js -> Million Lint -> react-doctor. Bus-factor risk is non-zero. The Node API is the most stable surface for custom integrations.
- First run downloads an oxlint binary (~10 MB). In CI, cache `~/.npm` or use `pnpm dlx` with a project-local store.
- The framework auto-detection occasionally misclassifies hybrid setups (Next.js + Remix in the same monorepo). Pass `--project <pkg>` to disambiguate.

## Programmatic use

[#programmatic-use](#programmatic-use)

For custom tooling -- PR-comment aggregation, multi-package rollup, feeding diagnostics into another agent -- use the Node API instead of parsing CLI text:

    import { diagnose } from "react-doctor/api";

    const result = await diagnose("./apps/web", {
      lint: true,
      deadCode: true,
    });

    // result.score        -> { score: 82, label: "Good" } | null
    // result.diagnostics  -> Diagnostic[]
    // result.project      -> { framework, reactVersion, hasCompiler, ... }

`Diagnostic` shape:

    interface Diagnostic {
      filePath: string;
      plugin: string;
      rule: string;
      severity: "error" | "warning";
      message: string;
      help: string;
      line: number;
      column: number;
      category: string;
    }

The API is what to wrap if integrating react-doctor into a custom MCP server or sleeptime-proxy flow -- not the CLI.
