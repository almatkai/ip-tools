/// <reference types="@raycast/api">

/* 🚧 🚧 🚧
 * This file is auto-generated from the extension's manifest.
 * Do not modify manually. Instead, update the `package.json` file.
 * 🚧 🚧 🚧 */

/* eslint-disable @typescript-eslint/ban-types */

type ExtensionPreferences = {}

/** Preferences accessible in all the extension's commands */
declare type Preferences = ExtensionPreferences

declare namespace Preferences {
  /** Preferences accessible in the `ip2long` command */
  export type Ip2Long = ExtensionPreferences & {}
  /** Preferences accessible in the `long2ip` command */
  export type Long2Ip = ExtensionPreferences & {}
  /** Preferences accessible in the `ip2BinHex` command */
  export type Ip2BinHex = ExtensionPreferences & {}
  /** Preferences accessible in the `parseCIDR` command */
  export type ParseCIDR = ExtensionPreferences & {}
  /** Preferences accessible in the `isValidIP` command */
  export type IsValidIP = ExtensionPreferences & {}
  /** Preferences accessible in the `isValidCIDR` command */
  export type IsValidCIDR = ExtensionPreferences & {}
  /** Preferences accessible in the `toIPv6Format` command */
  export type ToIPv6Format = ExtensionPreferences & {}
  /** Preferences accessible in the `toIPv6Expand` command */
  export type ToIPv6Expand = ExtensionPreferences & {}
  /** Preferences accessible in the `geoLocation` command */
  export type GeoLocation = ExtensionPreferences & {}
}

declare namespace Arguments {
  /** Arguments passed to the `ip2long` command */
  export type Ip2Long = {
  /** IP Address */
  "keywork": string
}
  /** Arguments passed to the `long2ip` command */
  export type Long2Ip = {
  /** IP Number */
  "keywork": string
}
  /** Arguments passed to the `ip2BinHex` command */
  export type Ip2BinHex = {
  /** IP Address */
  "keywork": string
}
  /** Arguments passed to the `parseCIDR` command */
  export type ParseCIDR = {
  /** CIDR */
  "keywork": string
}
  /** Arguments passed to the `isValidIP` command */
  export type IsValidIP = {
  /** IP Address */
  "keywork": string
}
  /** Arguments passed to the `isValidCIDR` command */
  export type IsValidCIDR = {
  /** CIDR */
  "keywork": string
}
  /** Arguments passed to the `toIPv6Format` command */
  export type ToIPv6Format = {
  /** IPv4 Address */
  "keywork": string
}
  /** Arguments passed to the `toIPv6Expand` command */
  export type ToIPv6Expand = {
  /** IPv6 Address */
  "keywork": string
}
  /** Arguments passed to the `geoLocation` command */
  export type GeoLocation = {
  /** IP Address */
  "keywork": string
}
}

