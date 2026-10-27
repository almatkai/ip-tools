#!/bin/sh
set -eu
V2=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$V2/.work/home" "$V2/.work/tmp" "$V2/.work/cargo-home" "$V2/.work/target" "$V2/.work/npm-cache"
# Child process only; use installed toolchain, never install or modify toolchains.
RUSTUP_HOME_RESOLVED=${RUSTUP_HOME:-"$HOME/.rustup"}
exec env HOME="$V2/.work/home" XDG_CACHE_HOME="$V2/.work/home/cache" XDG_CONFIG_HOME="$V2/.work/home/config" XDG_DATA_HOME="$V2/.work/home/data" TMPDIR="$V2/.work/tmp" TMP="$V2/.work/tmp" TEMP="$V2/.work/tmp" CARGO_HOME="$V2/.work/cargo-home" CARGO_TARGET_DIR="$V2/.work/target" RUSTUP_HOME="$RUSTUP_HOME_RESOLVED" PYTHONPYCACHEPREFIX="$V2/.work/pycache" npm_config_cache="$V2/.work/npm-cache" "$@"
