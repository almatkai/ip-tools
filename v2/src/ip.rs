//! Compatibility port of ip-toolkit 1.0.20; not std::net parsing.
use num_bigint::BigUint;
use num_traits::{FromPrimitive, One, ToPrimitive, Zero};
use regex::Regex;
use serde_json::{json, Map, Value};
use std::sync::LazyLock;

static V6: LazyLock<Regex> = LazyLock::new(|| Regex::new(include_str!("ipv6.regex")).unwrap());
fn ws(c: char) -> bool {
    matches!(c, '\u{0009}'..='\u{000d}' | ' ' | '\u{00a0}' | '\u{1680}' | '\u{2000}'..='\u{200a}' | '\u{2028}' | '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}' | '\u{feff}')
}
pub fn trim(s: &str) -> &str {
    s.trim_matches(ws)
}
fn dollar(s: &str) -> &str {
    s
}

pub fn v4(s: &str) -> bool {
    let p: Vec<_> = dollar(s).split('.').collect();
    p.len() == 4
        && p.iter().all(|p| {
            !p.is_empty()
                && p.len() <= 3
                && p.bytes().all(|c| c.is_ascii_digit())
                && p.parse::<u16>().is_ok_and(|n| n <= 255)
                && (p.len() != 3 || p.as_bytes()[0] <= b'1' || p.parse::<u16>().unwrap() >= 200)
        })
}
pub fn v6(s: &str) -> bool {
    V6.is_match(s)
}
pub fn valid(s: &str, version: &str) -> bool {
    if version == "IPv4" {
        v4(s)
    } else {
        v6(s)
    }
}
fn n4(s: &str) -> u32 {
    dollar(s)
        .split('.')
        .fold(0u32, |a, b| (a << 8) + b.parse::<u32>().unwrap())
}
fn ip4(n: u32) -> String {
    format!(
        "{}.{}.{}.{}",
        n >> 24,
        (n >> 16) & 255,
        (n >> 8) & 255,
        n & 255
    )
}
pub fn expanded(s: &str) -> Result<String, String> {
    if s == "::" {
        return Ok("0000:0000:0000:0000:0000:0000:0000:0000".into());
    }
    let mut p: Vec<String> = s.split(':').map(String::from).collect();
    let mut i = 0;
    while i + 1 < p.len() {
        if p[i].is_empty() && p[i + 1].is_empty() {
            p.remove(i);
        }
        i += 1;
    }
    if p.last().is_some_and(|s| v4(s)) {
        let n = n4(p.last().unwrap());
        p.pop();
        p.push(format!("{:04x}", n >> 16));
        p.push(format!("{:04x}", n & 65535));
    }
    let len = p.len();
    let mut output = Vec::new();
    for value in p {
        if value.is_empty() {
            let repeats = 9usize
                .checked_sub(len)
                .ok_or("Source IPv6 expansion throws for this zone suffix")?;
            output.push(vec!["0000"; repeats].join(":"));
        } else {
            let padding = 4usize.saturating_sub(value.encode_utf16().count());
            output.push(format!("{}{value}", "0".repeat(padding)));
        }
    }
    Ok(output.join(":"))
}

fn parse_hex_prefix(s: &str) -> Result<BigUint, String> {
    let s = trim(s);
    let (negative, s) = if let Some(s) = s.strip_prefix('-') {
        (true, s)
    } else {
        (false, s.strip_prefix('+').unwrap_or(s))
    };
    let s = s
        .strip_prefix("0x")
        .or_else(|| s.strip_prefix("0X"))
        .unwrap_or(s);
    let digits: String = s.chars().take_while(|c| c.is_ascii_hexdigit()).collect();
    let value = BigUint::parse_bytes(digits.as_bytes(), 16)
        .ok_or("Source IPv6 conversion throws for this accepted address")?;
    if negative && !value.is_zero() {
        return Err("Source IPv6 conversion throws for signed zone group".into());
    }
    let number = value
        .to_f64()
        .filter(|n| n.is_finite())
        .ok_or("Source IPv6 conversion throws for oversized zone group")?;
    BigUint::from_f64(number)
        .ok_or_else(|| "Source IPv6 conversion throws for this accepted address".into())
}

pub fn number(s: &str, version: &str) -> Result<BigUint, String> {
    if version == "IPv4" {
        return Ok(BigUint::from(n4(s)));
    }
    let mut bits = String::new();
    for part in expanded(s)?.split(':') {
        let b = parse_hex_prefix(part)?.to_str_radix(2);
        bits.push_str(&format!("{:0>16}", b));
    }
    BigUint::parse_bytes(bits.as_bytes(), 2).ok_or_else(|| "Source IPv6 conversion failed".into())
}
pub fn compressed(s: &str) -> Result<String, String> {
    if number(s, "IPv6")?.is_zero() {
        return Ok("::".into());
    }
    let p = expanded(s)?
        .split(':')
        .map(|p| {
            parse_hex_prefix(p).map(|n| {
                if n.is_zero() {
                    "X".into()
                } else {
                    n.to_str_radix(16)
                }
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    let mut out = p.join(":");
    for n in (2..=7).rev() {
        let pat = vec!["X"; n].join(":");
        if out.contains(&pat) {
            out = out.replacen(&pat, ":", 1).replacen(":::", "::", 1);
            break;
        }
    }
    Ok(out.replace('X', "0"))
}
pub fn ip6(n: &BigUint) -> Result<String, String> {
    let hex = format!("{:0>32}", n.to_str_radix(16));
    compressed(
        &hex.as_bytes()
            .chunks(4)
            .map(|p| std::str::from_utf8(p).unwrap())
            .collect::<Vec<_>>()
            .join(":"),
    )
}
fn js_number(s: &str) -> f64 {
    let s = trim(s);
    if s.is_empty() {
        return 0.0;
    }
    if s.len() > 2 {
        let radix = match s.get(..2).unwrap_or("") {
            "0x" | "0X" => 16,
            "0b" | "0B" => 2,
            "0o" | "0O" => 8,
            _ => 0,
        };
        if radix != 0 {
            return BigUint::parse_bytes(&s.as_bytes()[2..], radix)
                .and_then(|n| n.to_f64())
                .unwrap_or(f64::NAN);
        }
    }
    if matches!(s, "Infinity" | "+Infinity") {
        return f64::INFINITY;
    }
    if s == "-Infinity" {
        return f64::NEG_INFINITY;
    }
    // Rust also accepts inf; ECMAScript Number does not.
    if s.to_ascii_lowercase().contains("inf") {
        return f64::NAN;
    }
    s.parse().unwrap_or(f64::NAN)
}
fn big_value(n: &BigUint) -> Value {
    serde_json::from_str(&n.to_string()).unwrap()
}
fn object(entries: Vec<(&str, Value)>) -> Value {
    Value::Object(
        entries
            .into_iter()
            .map(|(k, v)| (k.into(), v))
            .collect::<Map<_, _>>(),
    )
}
pub fn cidr(s: &str, version: &str) -> Result<Option<Value>, String> {
    let mut parts = s.split('/');
    let ip = parts.next().unwrap_or("");
    let Some(mask) = parts.next() else {
        return Ok(None);
    };
    if mask.is_empty() || !valid(ip, version) {
        return Ok(None);
    }
    let m = js_number(mask);
    let max = if version == "IPv4" { 32.0 } else { 128.0 };
    if !m.is_finite() || m < 0.0 || m > max {
        return Ok(None);
    }
    if m.fract() != 0.0 {
        return Err("Source CIDR conversion throws for fractional prefix".into());
    }
    let m = m as u32;
    let shift = max as u32 - m;
    let count = BigUint::one() << shift;
    let ip = number(ip, version)?;
    let first = (&ip >> shift) << shift;
    let last = &first + &count - BigUint::one();
    if version == "IPv6" {
        return Ok(Some(object(vec![
            ("ipCount", big_value(&count)),
            ("firstHost", json!(ip6(&first)?)),
            ("lastHost", json!(ip6(&last)?)),
            ("prefixLength", json!(m)),
        ])));
    }
    let n = first.to_u32().unwrap();
    let end = last.to_u32().unwrap();
    let count = count.to_u64().unwrap();
    let usable = if m < 31 { count - 2 } else { count };
    Ok(Some(object(vec![
        ("ipCount", json!(count)),
        ("cidrMask", json!(m)),
        ("usableCount", json!(usable)),
        (
            "subnetMask",
            json!(ip4(if m == 0 { 0 } else { u32::MAX << (32 - m) })),
        ),
        (
            "networkAddress",
            json!(if m < 31 { ip4(n) } else { String::new() }),
        ),
        (
            "broadcastAddress",
            json!(if m < 31 { ip4(end) } else { String::new() }),
        ),
        ("firstHost", json!(ip4(n + u32::from(m < 31)))),
        ("lastHost", json!(ip4(end - u32::from(m < 31)))),
    ])))
}
pub fn digit(s: &str) -> bool {
    let s = dollar(s);
    !s.is_empty() && s.bytes().all(|b| b.is_ascii_digit())
}
pub fn long(s: &str, version: &str) -> Option<String> {
    if !digit(s) {
        return None;
    }
    let n = BigUint::parse_bytes(dollar(s).as_bytes(), 10)?;
    if version == "IPv4" {
        n.to_u32().map(ip4)
    } else if n.bits() <= 128 {
        ip6(&n).ok()
    } else {
        None
    }
}
pub fn mapped(s: &str) -> Result<Value, String> {
    let mapped = format!("::ffff:{}", ip4(n4(s)));
    Ok(object(vec![
        ("mapped", json!(mapped)),
        ("comperssed", json!(compressed(&mapped)?)),
        ("expanded", json!(expanded(&mapped)?)),
    ]))
}
pub fn binhex(s: &str, version: &str) -> Result<(Value, String), String> {
    let n = number(s, version)?;
    Ok((
        object(vec![
            ("decimal", big_value(&n)),
            ("hex", json!(format!("0x{}", n.to_str_radix(16)))),
            ("binary", json!(n.to_str_radix(2))),
        ]),
        n.to_string(),
    ))
}
pub fn js_string(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Object(_) => "[object Object]".into(),
        Value::Array(a) => a
            .iter()
            .map(|x| {
                if x.is_null() {
                    String::new()
                } else {
                    js_string(x)
                }
            })
            .collect::<Vec<_>>()
            .join(","),
        _ => v.to_string(),
    }
}
