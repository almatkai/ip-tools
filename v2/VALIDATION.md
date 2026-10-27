# Validation and review handoff

Selected clone: `rust-extension-ports/ip-tools` only. Branch `feat/native-v2-rust`; HEAD/base `95d41603aa6fccefe31f507c70f21e35e24c69f4`. No stage, commit, push, PR, install, publication, host integration, registration or ledger change was performed. The parent owns review and cleanup.

The final full reproducible runner completed **28 passing stages and 2 tooling blocks** after the round-2 fixes. Exact structured results are in [qa/validation-results.json](qa/validation-results.json). Build inputs and Cargo.lock were checked unchanged before/after a new empty distinct CargoHome/Target HTTPS release build; all fetched SDK fixture files matched the immutable reference. The DEV ZIP was rebuilt, freshly extracted and tested against every command, the entire source oracle and the current renderer/process regressions.

| Check | Measured result |
|---|---|
| Original V1 disposable exact-copy, exact npm lock | 13 tests passed; typecheck passed; no baseline defect observed |
| Rust stable 1.98.0 and MSRV 1.85.0 | 3 tests passed on each; fmt and strict all-target Clippy passed |
| Actual-source TSX + locked-library oracle through real SDK pipes | 2,708 vectors; 4,220 exact clipboard payloads; 0 mismatches |
| Original throwing cases | 21 source exceptions, represented as explicit safe conversion errors |
| Protocol lifecycle/action checks | 246 checks, including 160 cancelled opens, A/B/A, invalid/nonstring/oversized input, duplicates/foreign tokens, unknown ACK, cancellation/rollback, timeout, late ACK, EOF and shutdown |
| Extracted production executable | All nine command smoke checks and entire oracle passed; no real OS effect invoked |
| Actual full pinned renderer functions | Original ownership failure reproduced; 177 ownership/recovery/process/list/menu checks passed, plus actual default action-title producer check |
| Pinned compiler/wire contracts | Complete component + actual desktop bridge/shared definitions; no new diagnostics; four unchanged isolated-harness namespace diagnostics documented below |
| Actual full pinned ClipboardCore producer | 8 checks passed with OS producer replaced before compilation; full source and exact text-argument function retained |
| Whole-adapter + actual SDK HTTP helper | 13 checks passed: successful fetch/copy, JS numeric rounding, empty lookup, language, stale response cancellation, atomic full drafts and no duplicate requests from refresh/stale revisions |
| Production HTTP client | Own loopback HTTP success, exact path/query and bounded malformed/error/cancellation tests passed |
| TLS | Genuine production client rejected own private CA; separate unshipped trusted helper succeeded |
| Locked axios 1.20.0 | Own HTTP/TLS success plus 8 actual geo source producer/request cases passed |
| Full pinned draft-2020 schema | Source and packaged positives; 21 meaningful negatives passed |
| References/assets | 60 V1/fixture/export/icon hash checks passed; fresh original PNG download equals V1 |
| Cargo archive audits | 155 production registry archives, plus 45 host-QA and 155 TLS-QA lock entries; actual archive SHA256 checks and authentic grants retained, including target crates; zero missing grants detected |
| npm archive audits | All 172 original-lock and 6 schema-QA archives verified by lock SRI and SHA256; complete member-name/embedded-grant evidence retained |
| Candidate boundaries | Only root README discovery link and new `v2/`; index empty; no unexpected ignored durable fixture |

Corpus JSON SHA256: `33107b8ca926425be8e3f7d7047ed7d62f83ce1f245f478bcd0fb290fb1ab4f8`. Actual-source oracle JSON SHA256: `8e09920a9c749f589e832b6ffc0b220100edd3a80741b01cf786a86f3ffe9ed6`. Conversion sources, main/transport/settings/regex, manifest, locks, corpus/oracle producers, icon and 829 fixture/lock/grant candidates matched the previous inventory byte for byte; only adapter state/render and the documented QA/host-proposal/report files changed in this round.

The corpus uses deterministic seed 6734, normal/random addresses and boundary/malformed/optional inputs: leading zeros, IPv6 compression ties, whitespace/zone quirks, unusually long zone groups with JS Number coercion, decimal/hex/binary values, u128 endpoints and overflow, `/0`, `/32`, `/128`, coercible/fractional/out-of-range masks and json-bigint serialization. The oracle evaluates actual command producers after replacing React/Raycast/network producers, not a rewritten expected-value implementation. The finite corpus does not establish universal parity.

## Development artifacts

The latest deterministic development ZIP is `.work/ip-tools-2.0.0-dev.1-aarch64-apple-darwin-DEV.zip`.

- ZIP SHA256: `23d49409042100fc8f2f6c8cbfb891887fb115b16c26146f83fb1e73d75a0950`
- ARM64 production executable SHA256: `4e4ff1c344266989c0d6c39b73e3315b48f36e3fc99b734216d65f9e0a8ec677`
- Closed archive: 298 regular files; deterministic timestamps/modes/order and every file hash checked. `extension.json.files` covers every other member; manifest self-hashing is intentionally excluded.
- Production source artifacts: `{}`. Native verification: macOS `not-run`, Windows `not-run`.
- Fresh CargoHome/Target and executable path are recorded relatively in `qa/validation-results.json`; detailed logs and package inventory remain in ignored `.work/`.

The archive is a DEV review artifact, not a published release or host installation. No live provider request, real clipboard, browser, focus, native profile or GUI acceptance was exercised. HTTP and TLS tests use only controlled loopback fixtures. TLS helper trust injection is absent from the production executable. The full-adapter HTTP helper changes only the provider origin before compilation; it does not prove production public-service acceptance.

## Remaining gaps and explicit adaptations

Windows GNU check and Clippy were attempted because that Rust target is installed. Both are blocked by missing `x86_64-w64-mingw32-gcc`; `dlltool` is also absent. Windows MSVC target/native execution is unrun. Nothing was installed to bypass those tooling blocks.

The separate [renderer ownership patch](integration/renderer-ownership.patch) is **unapplied** and remains a host prerequisite. It is tested against retained exact full functions, not the dirty host checkout or an accepted app build. Native model/input ownership, source empty-state messages and `unchanged` result handling require that patch. The wire uses existing list/row/dropdown/action shapes and original stock-icon tokens; native host symbol geometry and layout are UI adaptations. The original extension-owned PNG itself is exact.

Round 2 resolves both remaining [parent findings](qa/parent-review-findings.json): rapid dropdown intent is no longer dropped, and failed input no longer leaves busy ownership stuck. Every native input sends one complete client query/choice/revision using existing formValues. The native monotonic floor rejects crossed old arrivals; renderer sequence/session fences reject crossed old completions. New input clears visible stale rows/effects immediately. Terminal failure frees only its own busy state, while exact-revision view acknowledgement remains necessary to re-enable effects. A visible Refresh button supports read-only recovery without automatic input replay. The parent's multi-action frozen retry remains reachable in every retained row and preserves exact bytes.

Evidence includes A/B/A, A/B and repeated equal controls, query→kind and kind→query, invalid→valid, mixed A/B/A, forward/reverse real SDK wire order, independently reversed host completions, failed/no-view/unchanged/rejected input, exact versus stale recovery, stale errors after successful notice/model, replaced owner/generation, unmount, same-owner model changes, preference-session replacement, foreign value-action rejection, consumed tokens and repeated deliberate Copy after success. The same component/process checks run against the fresh extracted production executable. Whole-adapter language/HTTP checks use an origin-replaced unshipped loopback helper. This finite schedule set is not exhaustive concurrency verification or a live GUI claim.

The isolated TypeScript 5.9.3 check uses complete immutable bridge/shared definitions, full component source, exact extracted Surface props, locked V1 React types and an explicit UI-primitives declaration boundary. Baseline and proposed sources each retain three `JSX` namespace diagnostics in the pinned component and one `NodeJS` namespace diagnostic in the isolated shared-type context; there are no additional proposed diagnostics. These context diagnostics were recorded rather than changing unrelated host source. This is not a successful full-host build; the dirty host working files were neither read nor built. Object hashes and full diagnostics are retained in the structured results. No new shared top-level request fields were introduced; the existing `Record<string, unknown>` formValues/root props contract carries the draft metadata.

The original geolocation provider is HTTP, unchanged. Bounded response/timeout/redirect/input policies, immediate input-time revocation with 200 ms geo debounce, safe handling of original exceptions, explicit uncertain-copy retry, per-command private dropdown persistence and nonfinite/non-object response rejection are documented precisely in [README.md](README.md). They are deliberate adaptations, not claims of byte-equivalent behavior outside the tested source domains.

[QA license gaps](qa/LICENSE-GAPS.md) records 56 original npm archives with no named or detected embedded license grant: 52 optional esbuild platform archives and four other QA packages. The two esbuild parent versions' authentic MIT grants are retained. Full MIT grants found in agent-base/https-proxy-agent README files are retained verbatim, so those packages are not falsely counted missing. This is archive-content evidence, not synthesized replacement license text or a legal conclusion. None of those JS packages is shipped in the production DEV ZIP.

XERJ coverage is incomplete: canonical-prefix autoindex received HTTP 429/RSS memory shedding. It was stopped without changing prefix/schema/settings or restarting the server. No-match output was not treated as absence; complete source reads, Git objects, rg, locked archives and hashes supplied the verification.

[Candidate inventory](qa/candidate-inventory.json) covers all Git-visible root README/V2 candidate files except itself. It hashes **worktree bytes**, not staged blobs. The parent must rehash the actual staged blobs before its commit. Source, lock, fixture, notice and icon provenance hashes remain inspectable separately.
