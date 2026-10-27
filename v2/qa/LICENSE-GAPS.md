# QA npm license-text evidence

The audit verifies every exact-lock archive SRI/SHA256, records all regular member names and scans member contents for complete MIT/Apache grant markers. It copies authentic named grant files and complete README grants without inventing license text. See `npm-archive-audit.json` and `schema-npm-archive-audit.json`.

56 original-lock archives have no named or detected embedded grant:

| Package | Exact version | Evidence |
|---|---|---|
| `node_modules/@esbuild/aix-ppc64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/android-arm` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/android-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/android-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/darwin-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/darwin-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/freebsd-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/freebsd-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-arm` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-ia32` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-loong64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-mips64el` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-ppc64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-riscv64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-s390x` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/linux-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/netbsd-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/netbsd-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/openbsd-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/openbsd-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/openharmony-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/sunos-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/win32-arm64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/win32-ia32` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@esbuild/win32-x64` | 0.27.7 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@raycast/api` | 1.104.25 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/@raycast/utils` | 2.3.0 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/filelist` | 1.0.6 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/jake` | 10.9.4 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/aix-ppc64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/android-arm` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/android-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/android-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/darwin-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/darwin-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/freebsd-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/freebsd-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-arm` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-ia32` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-loong64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-mips64el` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-ppc64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-riscv64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-s390x` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/linux-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/netbsd-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/netbsd-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/openbsd-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/openbsd-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/openharmony-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/sunos-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/win32-arm64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/win32-ia32` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |
| `node_modules/tsx/node_modules/@esbuild/win32-x64` | 0.28.2 | No grant file or detected full embedded grant in hash-bound archive |

The 52 esbuild platform archives are paired with the authentic parent `esbuild` MIT grants for 0.27.7 and 0.28.2 under `notices/npm/`. The four remaining packages are `@raycast/api`, `@raycast/utils`, `filelist`, and `jake`. No private Raycast runtime resource is evaluated or shipped; producers are replaced before source evaluation.

Complete MIT grants embedded in agent-base 6.0.2 and https-proxy-agent 5.0.1 README files are retained verbatim as `README.grant.md`. They are not missing-grant cases. bignumber.js uses the authentic British-spelled `LICENCE.md`, which is also retained.

All six schema-QA archives have authentic grant files. All production Cargo registry archives have retained authentic grants, including r-efi's full MIT permission/copyright text in `AUTHORS`. QA Cargo locks and their archive audits/notices are separate. These findings describe archive contents, not license equivalence or release approval.
