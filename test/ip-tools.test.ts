import assert from "node:assert/strict";
import test, { describe, it } from "node:test";
import {
  ip2BinHex,
  ip2long,
  isValidCIDR,
  isValidIP,
  isValidIPAny,
  long2ip,
  parseCIDR,
  stringifyWithBigInt,
  toIPv6Expand,
  toIPv6Format,
} from "../src/lib/ip";

describe("isValidIP", () => {
  it("validates IPv4 and IPv6", () => {
    assert.equal(isValidIP("192.168.0.1", "IPv4"), true);
    assert.equal(isValidIP("999.999.999.999", "IPv4"), false);
    assert.equal(isValidIP("::1", "IPv6"), true);
    assert.equal(isValidIP("2001:db8::1", "IPv6"), true);
    assert.equal(isValidIP("not-an-ip", "IPv6"), false);
    assert.equal(isValidIPAny("192.168.0.1"), true);
    assert.equal(isValidIPAny("::1"), true);
    assert.equal(isValidIPAny("invalid"), false);
  });
});

describe("isValidCIDR", () => {
  it("validates CIDR", () => {
    assert.equal(isValidCIDR("192.168.0.0/24", "IPv4"), true);
    assert.equal(isValidCIDR("192.168.0.0/33", "IPv4"), false);
    assert.equal(isValidCIDR("2001:db8::/32", "IPv6"), true);
    assert.equal(isValidCIDR("2001:db8::/129", "IPv6"), false);
  });
});

describe("ip2long and long2ip", () => {
  it("IPv4 round-trips", () => {
    assert.equal(ip2long("192.168.0.1", "IPv4"), "3232235521");
    assert.equal(ip2long("0.0.0.0", "IPv4"), "0");
    assert.equal(ip2long("255.255.255.255", "IPv4"), "4294967295");
    assert.equal(long2ip("3232235521", "IPv4"), "192.168.0.1");
    assert.equal(long2ip("0", "IPv4"), "0.0.0.0");
    assert.equal(long2ip("not-a-number", "IPv4"), false);
  });
  it("IPv6 round-trips", () => {
    const ip = "2001:db8::1";
    const long = ip2long(ip, "IPv6");
    assert.ok(long.length > 0);
    assert.match(long, /^\d+$/);
    const back = long2ip(long, "IPv6");
    assert.ok(typeof back === "string");
    // compressed vs expanded may differ but should be valid
    assert.equal(isValidIP(back as string, "IPv6"), true);
    const zero = ip2long("::1", "IPv6");
    assert.ok(zero);
    assert.equal(long2ip(zero, "IPv6"), "::1");
  });
});

describe("ip2BinHex", () => {
  it("converts IPv4 to hex and binary", () => {
    const r = ip2BinHex("192.168.0.1", "IPv4")!;
    assert.equal(r.hex, "0xc0a80001");
    assert.equal(r.binary, BigInt(3232235521).toString(2));
    assert.equal(r.decimal.toString(), "3232235521");
  });
  it("converts IPv6 to hex and binary", () => {
    const r = ip2BinHex("::1", "IPv6")!;
    assert.equal(r.hex, "0x1");
    assert.equal(r.binary, "1");
  });
  it("returns null for invalid", () => {
    assert.equal(ip2BinHex("invalid", "IPv4"), null);
  });
});

describe("parseCIDR", () => {
  it("parses IPv4 CIDR", () => {
    const r = parseCIDR("192.168.0.0/24", "IPv4");
    assert.ok(Object.keys(r).length > 0);
    // should contain network info; just check it has some keys
    const keys = Object.keys(r);
    assert.ok(keys.length >= 2);
  });
  it("parses IPv6 CIDR and returns empty for invalid", () => {
    const r = parseCIDR("2001:db8::/32", "IPv6");
    assert.ok(Object.keys(r).length > 0);
    assert.deepEqual(parseCIDR("invalid", "IPv4"), {});
  });
});

describe("toIPv6Format", () => {
  it("converts IPv4 to IPv6 format", () => {
    const r = toIPv6Format("192.168.0.1");
    assert.ok(Object.keys(r).length > 0);
    assert.deepEqual(toIPv6Format("999.999.999.999"), {});
    assert.deepEqual(toIPv6Format("invalid"), {});
  });
});

describe("toIPv6Expand", () => {
  it("expands and compresses IPv6", () => {
    const expanded = toIPv6Expand("2001:db8::1", "expanded");
    assert.ok(expanded);
    assert.match(expanded!, /0000/);
    const compressed = toIPv6Expand("2001:0db8:0000:0000:0000:0000:0000:0001", "compressed");
    assert.ok(compressed);
    assert.equal(compressed, "2001:db8::1");
    assert.equal(toIPv6Expand("invalid", "expanded"), null);
  });
});

describe("json-bigint", () => {
  it("stringifies and parses big ints", () => {
    const obj = { a: BigInt("9007199254740993") };
    const s = stringifyWithBigInt(obj);
    assert.match(s, /9007199254740993/);
    const parsed = stringifyWithBigInt({ decimal: BigInt("340282366920938463463374607431768211455") });
    assert.ok(parsed.includes("340282366920938463463374607431768211455"));
  });
});

test("package.json declares Windows+macOS and Tezbar metadata", async () => {
  const pkg = await import("../package.json", { with: { type: "json" } });
  const data = (pkg as unknown as { default: Record<string, unknown> }).default ??
    (pkg as unknown as Record<string, unknown>);
  assert.deepEqual((data as { platforms: string[] }).platforms, ["macOS", "Windows"]);
  const tezbar = (data as { tezbar: { platforms: string[]; repository: string; upstream: { commit: string; path: string } } }).tezbar;
  assert.deepEqual(tezbar.platforms, ["macos", "windows"]);
  assert.equal(tezbar.repository, "https://github.com/almatkai/ip-tools");
  assert.equal(tezbar.upstream.path, "extensions/ip-tools");
  assert.equal(tezbar.upstream.commit, "6734d85992290066fd31a7f5bee3cca3d3545a1a");
  const commands = (data as { commands: { platforms: string[] }[] }).commands;
  assert.equal(commands.length, 9);
  for (const cmd of commands) {
    assert.deepEqual(cmd.platforms, ["macOS", "Windows"]);
  }
  const deps = (data as { dependencies: Record<string, string> }).dependencies;
  assert.ok(deps["@raycast/api"]);
  assert.ok(deps["@raycast/utils"]);
  assert.ok(deps["axios"]);
  assert.ok(deps["ip-toolkit"]);
  assert.ok(deps["json-bigint"]);
});
