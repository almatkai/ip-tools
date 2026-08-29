import { IPv4, IPv6, IP } from "ip-toolkit";
import JSONbig from "json-bigint";

export function isValidIP(ip: string, version: "IPv4" | "IPv6" = "IPv4"): boolean {
  return version === "IPv4" ? IPv4.isValidIP(ip) : IPv6.isValidIP(ip);
}

export function isValidIPAny(ip: string): boolean {
  return IP.isValidIP(ip);
}

export function isValidCIDR(cidr: string, version: "IPv4" | "IPv6" = "IPv4"): boolean {
  return version === "IPv4" ? IPv4.isCIDR(cidr) : IPv6.isCIDR(cidr);
}

export function ip2long(ip: string, version: "IPv4" | "IPv6" = "IPv4"): string {
  const v = version === "IPv4" ? IPv4.ip2long(ip) : IPv6.ip2long(ip);
  return v.toString();
}

export function long2ip(numStr: string, version: "IPv4" | "IPv6" = "IPv4"): string | false {
  if (!/^\d+$/.test(numStr)) return false;
  try {
    if (version === "IPv4") {
      return IPv4.long2ip(parseInt(numStr, 10));
    } else {
      return IPv6.long2ip(BigInt(numStr));
    }
  } catch {
    return false;
  }
}

export function ip2BinHex(
  ip: string,
  version: "IPv4" | "IPv6" = "IPv4",
): { decimal: bigint | number; hex: string; binary: string } | null {
  const valid = version === "IPv4" ? IPv4.isValidIP(ip) : IPv6.isValidIP(ip);
  if (!valid) return null;
  const dec = (version === "IPv4" ? IPv4.ip2long(ip) : IPv6.ip2long(ip)) as number | bigint;
  const big = typeof dec === "bigint" ? dec : BigInt(dec as number);
  return {
    decimal: dec,
    hex: `0x${big.toString(16)}`,
    binary: big.toString(2),
  };
}

export function parseCIDR(cidr: string, version: "IPv4" | "IPv6" = "IPv4"): Record<string, unknown> {
  const valid = version === "IPv4" ? IPv4.isCIDR(cidr) : IPv6.isCIDR(cidr);
  if (!valid) return {};
  return version === "IPv4"
    ? (IPv4.parseCIDR(cidr) as unknown as Record<string, unknown>)
    : (IPv6.parseCIDR(cidr) as unknown as Record<string, unknown>);
}

export function toIPv6Format(ipv4: string): Record<string, unknown> {
  if (!IPv4.isValidIP(ipv4)) return {};
  return IPv4.toIPv6Format(ipv4) as unknown as Record<string, unknown>;
}

export function toIPv6Expand(ipv6: string, format: "expanded" | "compressed" = "expanded"): string | null {
  if (!IPv6.isValidIP(ipv6)) return null;
  return format === "expanded" ? IPv6.expandedForm(ipv6).toString() : IPv6.compressedForm(ipv6).toString();
}

export function stringifyWithBigInt(value: unknown): string {
  return JSONbig.stringify(value, null, 2);
}

export function parseWithBigInt(text: string): unknown {
  return JSONbig.parse(text);
}
