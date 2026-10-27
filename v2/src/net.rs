use serde_json::Value;
use std::time::Duration;

pub fn client() -> Result<reqwest::Client, String> {
    reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .connect_timeout(Duration::from_secs(3))
        .redirect(reqwest::redirect::Policy::limited(5))
        .user_agent("axios/1.20.0")
        .build()
        .map_err(|_| "Geolocation transport unavailable".into())
}
/// Shared production HTTP implementation; caller owns cancellation by dropping it.
/// Production caller constructs only the original provider URL from validated input.
pub async fn fetch(client: &reqwest::Client, url: &str) -> Result<Value, String> {
    let mut response = client
        .get(url)
        .header("Accept", "application/json, text/plain, */*")
        .send()
        .await
        .map_err(|_| "Geolocation request failed".to_string())?;
    if !response.status().is_success() {
        return Err("Geolocation request failed".into());
    }
    if response.content_length().is_some_and(|n| n > 65536) {
        return Err("Geolocation response exceeds limit".into());
    }
    let mut body = Vec::new();
    while let Some(chunk) = response
        .chunk()
        .await
        .map_err(|_| "Geolocation response failed".to_string())?
    {
        if body.len() + chunk.len() > 65536 {
            return Err("Geolocation response exceeds limit".into());
        }
        body.extend_from_slice(&chunk);
    }
    let value: Value =
        serde_json::from_slice(&body).map_err(|_| "Geolocation response invalid".to_string())?;
    fn bounded(v: &Value, depth: usize, items: &mut usize) -> bool {
        *items += 1;
        if depth > 12 || *items > 512 {
            return false;
        }
        match v {
            Value::Array(a) => a.iter().all(|v| bounded(v, depth + 1, items)),
            Value::Object(o) => o.values().all(|v| bounded(v, depth + 1, items)),
            _ => true,
        }
    }
    if !value.is_object()
        || value.as_object().is_some_and(|o| o.len() > 128)
        || !bounded(&value, 0, &mut 0)
    {
        return Err("Geolocation response exceeds structure limit".into());
    }
    fn js_numbers(value: Value) -> Result<Value, String> {
        Ok(match value {
            Value::Number(n) => {
                let f = n
                    .as_f64()
                    .filter(|n| n.is_finite())
                    .ok_or("Geolocation response has nonfinite number")?;
                serde_json::from_str(ryu_js::Buffer::new().format(f))
                    .map_err(|_| "Geolocation response invalid")?
            }
            Value::Array(a) => Value::Array(
                a.into_iter()
                    .map(js_numbers)
                    .collect::<Result<Vec<_>, _>>()?,
            ),
            Value::Object(o) => {
                let mut entries: Vec<_> = o.into_iter().collect();
                entries.sort_by_key(|(k, _)| {
                    k.parse::<u32>()
                        .ok()
                        .filter(|n| *n < u32::MAX && n.to_string() == *k)
                        .map_or((1, 0), |n| (0, n))
                });
                Value::Object(
                    entries
                        .into_iter()
                        .map(|(k, v)| Ok((k, js_numbers(v)?)))
                        .collect::<Result<_, String>>()?,
                )
            }
            v => v,
        })
    }
    js_numbers(value)
}
pub fn provider_url(ip: &str, lang: &str) -> String {
    // Original source uses interpolation (including &&), not encodeURIComponent.
    format!("http://ip-api.com/json/{ip}?lang={lang}&&fields=61151")
}
