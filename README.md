# IP Tools for Tezbar

Convert, validate, and calculate IP subnets in Tezbar on Windows or macOS.

## Commands

- **Convert IP Address to Number** (`ip2long`) — IPv4 or IPv6 → decimal (choose version via dropdown).
- **Convert Number to IP Address** (`long2ip`) — decimal → IPv4/IPv6.
- **Convert IP Address to Bin and Hex** (`ip2BinHex`) — IP → decimal, hex (`0x...`), binary.
- **Convert CIDR to IP Range** (`parseCIDR`) — CIDR → network range details (uses `ip-toolkit`).
- **Verify IP Address Is Valid** (`isValidIP`) — validates IPv4/IPv6.
- **Verify CIDR Is Valid** (`isValidCIDR`) — validates CIDR.
- **Converts IPv4 to IPv6 Address** (`toIPv6Format`) — maps IPv4 to IPv6 representation.
- **Converts IPv6 to Expanded or Compressed** (`toIPv6Expand`) — toggles long vs short IPv6 form.
- **Query IP Geolocation Information** (`geoLocation`) — queries `http://ip-api.com/json/{ip}?lang={en|zh-CN}` and displays fields.

All commands accept an optional `keywork` text argument and throttle search input. Geolocation uses `axios` + `json-bigint` for response handling.

## Compatibility

- Windows: built and exercised in Tezbar on Windows 11.
- macOS: uses only cross-platform `@raycast/api`, `@raycast/utils`, `axios`, `ip-toolkit`, `json-bigint` (all pure JS) and retains the upstream macOS-compatible design.
- Linux: not currently declared.

## Local verification

```powershell
pnpm install
pnpm typecheck
pnpm test
pnpm build
```

## Credits

Adapted for Tezbar from Raycast's MIT-licensed `ip-tools` extension at upstream commit `6734d85992290066fd31a7f5bee3cca3d3545a1a`. Original author `meguoe` and contributors remain credited in `package.json`.

Standalone external Rust V2: [implementation and validation](v2/README.md).
