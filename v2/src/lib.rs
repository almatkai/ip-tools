pub mod ip;
pub mod net;
mod settings;
use serde_json::{json, Value};
use std::{
    collections::HashMap,
    sync::{Arc, Mutex, Weak},
};
use tezbar_extension_sdk::{BoxFuture, CoreResult, Extension, ExtensionContext};
use tokio::sync::watch;

pub const COMMANDS: &[&str] = &[
    "ip2long",
    "long2ip",
    "ip2BinHex",
    "parseCIDR",
    "isValidIP",
    "isValidCIDR",
    "toIPv6Format",
    "toIPv6Expand",
    "geoLocation",
];
type Sessions = Arc<Mutex<HashMap<String, Weak<Mutex<Session>>>>>;
#[derive(Default)]
pub struct Adapter {
    sessions: Sessions,
}
struct Cleanup {
    id: String,
    sessions: Sessions,
    session: Arc<Mutex<Session>>,
}
impl Drop for Cleanup {
    fn drop(&mut self) {
        let mut map = self.sessions.lock().unwrap();
        if map
            .get(&self.id)
            .and_then(Weak::upgrade)
            .is_some_and(|s| Arc::ptr_eq(&s, &self.session))
        {
            map.remove(&self.id);
        }
        self.session.lock().unwrap().cancel.send_replace(u64::MAX);
    }
}
#[derive(Clone)]
struct Effect {
    text: Arc<str>,
    title: String,
}
#[derive(Clone)]
struct Row {
    title: String,
    subtitle: String,
    copies: Vec<Effect>,
}
struct Session {
    query: String,
    choice: String,
    rows: Vec<Row>,
    empty: Option<(String, String)>,
    tokens: HashMap<String, Effect>,
    row_tokens: Vec<Vec<String>>,
    epoch: u64,
    client_revision: u64,
    client_owned: bool,
    cancel: watch::Sender<u64>,
    loading: bool,
    notice: Option<String>,
    uncertain: Option<Effect>,
}
impl Session {
    fn new(command: &str) -> Self {
        Self {
            query: String::new(),
            choice: match command {
                "toIPv6Expand" => "expanded",
                "geoLocation" => "en",
                _ => "IPv4",
            }
            .into(),
            rows: vec![],
            empty: None,
            tokens: HashMap::new(),
            row_tokens: vec![],
            epoch: 0,
            client_revision: 0,
            client_owned: false,
            cancel: watch::channel(0).0,
            loading: false,
            notice: None,
            uncertain: None,
        }
    }
    fn revoke(&mut self) {
        self.epoch += 1;
        self.cancel.send_replace(self.epoch);
        self.tokens.clear();
        self.row_tokens.clear();
        self.rows.clear();
        self.empty = None;
        self.notice = None;
        self.uncertain = None;
        self.loading = false;
    }
    fn issue(&mut self) {
        self.tokens.clear();
        self.row_tokens = self
            .rows
            .iter()
            .map(|row| {
                row.copies
                    .iter()
                    .map(|effect| {
                        let id = format!("copy:{}", uuid::Uuid::new_v4());
                        self.tokens.insert(id.clone(), effect.clone());
                        id
                    })
                    .collect()
            })
            .collect();
    }
}
fn choices(command: &str) -> Option<Vec<(&'static str, &'static str)>> {
    match command {
        "toIPv6Format" => None,
        "geoLocation" => Some(vec![("en", "English"), ("zh-CN", "Chinese")]),
        "toIPv6Expand" => Some(vec![("expanded", "expanded"), ("compressed", "compressed")]),
        _ => Some(vec![("IPv4", "IPv4"), ("IPv6", "IPv6")]),
    }
}
fn single(result: String, input: &str) -> Row {
    Row {
        title: result.clone(),
        subtitle: input.into(),
        copies: vec![Effect {
            text: result.into(),
            title: "Copy to Clipboard".into(),
        }],
    }
}
fn records(value: &Value, all: String, sort: bool) -> Vec<Row> {
    let all: Arc<str> = all.into();
    let Some(map) = value.as_object() else {
        return vec![];
    };
    let mut entries: Vec<_> = map.iter().collect();
    if sort {
        entries.sort_by(|a, b| a.0.cmp(b.0));
    }
    entries
        .into_iter()
        .filter(|(_, v)| v.as_str() != Some(""))
        .map(|(k, v)| {
            let text = ip::js_string(v);
            Row {
                title: k.clone(),
                subtitle: text.clone(),
                copies: vec![
                    Effect {
                        text: text.into(),
                        title: "Copy to Clipboard".into(),
                    },
                    Effect {
                        text: all.clone(),
                        title: "Copy All to Clipboard".into(),
                    },
                ],
            }
        })
        .collect()
}
fn pretty(value: &Value) -> String {
    serde_json::to_string_pretty(value).unwrap()
}
fn empty(s: &mut Session, title: String, icon: &str) {
    s.empty = Some((title, icon.into()));
}
fn compute(command: &str, s: &mut Session) -> Result<(), String> {
    let q = s.query.as_str();
    let is_empty = ip::trim(q).is_empty();
    let version = s.choice.as_str();
    if matches!(command, "isValidIP" | "isValidCIDR") {
        let cidr = command == "isValidCIDR";
        let noun = if cidr { "CIDR" } else { "address" };
        let valid = if is_empty {
            false
        } else if cidr {
            ip::cidr(q, version)?.is_some()
        } else {
            ip::valid(q, version)
        };
        let title = if is_empty {
            format!("Please enter the {version} {noun} you want to validate！")
        } else {
            format!(
                "This {version} {noun} is {}！",
                if valid { "valid" } else { "invalid" }
            )
        };
        empty(
            s,
            title,
            if is_empty {
                "Warning"
            } else if valid {
                "CheckCircle"
            } else {
                "XMarkCircle"
            },
        );
        return Ok(());
    }
    let noun = match command {
        "long2ip" => "Number",
        "parseCIDR" => "CIDR",
        "toIPv6Format" => "IPv4 address",
        "toIPv6Expand" => "IPv6 address",
        _ => "IP address",
    };
    if is_empty {
        empty(
            s,
            format!("Please enter the {noun} that needs to be converted！"),
            "Warning",
        );
        return Ok(());
    }
    let valid = match command {
        "long2ip" => ip::long(q, version).is_some(),
        "parseCIDR" => ip::cidr(q, version)?.is_some(),
        "toIPv6Format" => ip::v4(q),
        "toIPv6Expand" => ip::v6(q),
        _ => ip::valid(q, version),
    };
    if !valid {
        empty(s, format!("Please enter a valid {noun}！"), "XMarkCircle");
        return Ok(());
    }
    s.rows = match command {
        "ip2long" => vec![single(ip::number(q, version)?.to_string(), q)],
        "long2ip" => vec![single(ip::long(q, version).unwrap(), q)],
        "ip2BinHex" => {
            let (value, all) = ip::binhex(q, version)?;
            records(&value, all, false)
        }
        "parseCIDR" => {
            let value = ip::cidr(q, version)?.unwrap();
            records(&value, pretty(&value), false)
        }
        "toIPv6Format" => {
            let value = ip::mapped(q)?;
            records(&value, pretty(&value), false)
        }
        "toIPv6Expand" => vec![single(
            if version == "expanded" {
                ip::expanded(q)?
            } else {
                ip::compressed(q)?
            },
            q,
        )],
        _ => vec![],
    };
    Ok(())
}
fn placeholder(command: &str, s: &Session) -> String {
    match command {
        "isValidIP" => format!("Input {} address that needs to be validate！", s.choice),
        "isValidCIDR" => format!("Input {} CIDR that needs to be validate！", s.choice),
        "long2ip" => "Input Number that needs to be converted！".into(),
        "parseCIDR" => "Input CIDR that needs to be converted！".into(),
        "toIPv6Format" => "Input IPv4 address that needs to be converted！".into(),
        "toIPv6Expand" => "Input IPv6 address that needs to be converted！".into(),
        "geoLocation" => "Input IP address that needs to be query！".into(),
        _ => "Input IP address that needs to be converted！".into(),
    }
}
fn render(command: &str, s: &mut Session) -> Value {
    // A dropped/cancelled RPC leaves uncertainty outside SDK transactional state.
    if let Some(effect) = s.uncertain.clone() {
        if !s.tokens.values().any(|v| v.title == "Retry Exact Copy") {
            let id = format!("copy:{}", uuid::Uuid::new_v4());
            s.tokens.insert(
                id,
                Effect {
                    title: "Retry Exact Copy".into(),
                    ..effect
                },
            );
        }
    }
    let mut actions = vec![];
    let mut children = vec![];
    for (i, row) in s.rows.iter().enumerate() {
        let mut ids = s.row_tokens.get(i).cloned().unwrap_or_default();
        for id in &ids {
            if let Some(e) = s.tokens.get(id) {
                actions.push(json!({"id":id,"title":e.title,"kind":"copy"}));
            }
        }
        // Recovery is global and frozen, but the pinned surface only displays
        // actions included in the selected row. Keep it reachable from every
        // retained row, including a row whose consumed copy ID is now absent.
        ids.extend(
            s.tokens
                .iter()
                .filter(|(_, effect)| effect.title == "Retry Exact Copy")
                .map(|(id, _)| id.clone()),
        );
        children.push(json!({"type":"List.Item","props":{"id":format!("row:{i}"),"title":row.title,"subtitle":row.subtitle,"icon":"Clipboard","actionIds":ids.iter().filter(|id|s.tokens.contains_key(*id)).collect::<Vec<_>>()}}));
    }
    for (id, e) in &s.tokens {
        if e.title == "Retry Exact Copy" {
            actions.push(json!({"id":id,"title":e.title,"kind":"action"}));
        }
    }
    if let Some((title, icon)) = &s.empty {
        children.push(json!({"type":"List.EmptyView","props":{"title":title,"icon":{"source":icon,"tintColor":match icon.as_str(){"Warning"=>"yellow","CheckCircle"=>"green",_=>"red"}}}}));
    }
    let mut props = json!({"__clientInputAction":"control:input","__clientRevision":if s.client_owned { s.client_revision } else { 0 },"__clientChoice":s.choice,"searchText":s.query,"searchBarPlaceholder":placeholder(command,s),"__hasServerSearch":true,"throttle":true,"isLoading":s.loading});
    if let Some(options) = choices(command) {
        let id = "control:choice";
        actions.push(json!({"id":id,"title":"Select IP Version","kind":"action"}));
        props["searchBarAccessory"] = json!({"type":"List.Dropdown","props":{"actionId":id,"value":s.choice,"tooltip":"Select IP Version","storeValue":true},"children":options.into_iter().map(|(value,title)|json!({"type":"List.Dropdown.Item","props":{"value":value,"title":title}})).collect::<Vec<_>>()});
    }
    let mut value = tezbar_extension_sdk::view(
        "IP Tools",
        json!({"type":"List","props":props,"children":children}),
        actions,
    );
    value["refreshMs"] = Value::Null;
    if let Some(notice) = &s.notice {
        value["message"] = json!(notice);
    }
    value
}
impl Adapter {
    fn lookup(&self, id: &str) -> Result<Arc<Mutex<Session>>, String> {
        self.sessions
            .lock()
            .unwrap()
            .get(id)
            .and_then(Weak::upgrade)
            .ok_or_else(|| "Session unavailable".into())
    }
    fn create(
        &self,
        ctx: &ExtensionContext,
        id: &str,
        command: &str,
    ) -> Result<Arc<Mutex<Session>>, String> {
        let s = Arc::new(Mutex::new(Session::new(command)));
        if choices(command).is_some() {
            let mut state = s.lock().unwrap();
            match settings::load(&ctx.paths.data_dir, command) {
                Ok(Some(value)) => state.choice = value,
                Ok(None) => {}
                Err(error) => state.notice = Some(error),
            }
        }
        self.sessions
            .lock()
            .unwrap()
            .insert(id.into(), Arc::downgrade(&s));
        let cleanup = Cleanup {
            id: id.into(),
            sessions: self.sessions.clone(),
            session: s.clone(),
        };
        ctx.spawn(async move {
            let _cleanup = cleanup;
            std::future::pending::<()>().await;
        })?;
        Ok(s)
    }
    fn update(
        &self,
        ctx: &ExtensionContext,
        command: &str,
        session: &Arc<Mutex<Session>>,
    ) -> Result<Value, String> {
        let mut s = session.lock().unwrap();
        if command != "geoLocation" {
            if let Err(e) = compute(command, &mut s) {
                empty(
                    &mut s,
                    "Conversion failed for this source-accepted input".into(),
                    "XMarkCircle",
                );
                s.notice = Some(e);
            }
            s.issue();
            return Ok(render(command, &mut s));
        }
        if !ip::trim(&s.query).is_empty() && !ip::v4(&s.query) && !ip::v6(&s.query) {
            empty(
                &mut s,
                "Please enter a valid IP address！".into(),
                "XMarkCircle",
            );
            return Ok(render(command, &mut s));
        }
        s.loading = true;
        let epoch = s.epoch;
        let url = net::provider_url(&s.query, &s.choice);
        let mut changed = s.cancel.subscribe();
        let target = Arc::downgrade(session);
        let task_ctx = ctx.clone();
        ctx.spawn(async move {
            let request = async {
                tokio::time::sleep(std::time::Duration::from_millis(200)).await;
                let client = net::client()?;
                net::fetch(&client, &url).await
            };
            let result =
                tokio::select! {biased;_ = changed.changed()=>return,result=request=>result};
            if let Some(target) = target.upgrade() {
                let mut s = target.lock().unwrap();
                if s.epoch != epoch {
                    return;
                }
                s.loading = false;
                let value = result.unwrap_or_else(|_| json!({"status":"fail"}));
                s.rows = records(&value, pretty(&value), true);
                s.issue();
                let _ = task_ctx.invalidate();
            }
        })?;
        Ok(render(command, &mut s))
    }
}
fn input(value: Option<&Value>) -> Result<String, String> {
    match value {
        None => Ok(String::new()),
        Some(Value::String(s)) if s.len() <= 4096 => Ok(s.clone()),
        _ => Err("Input must be text of at most 4096 UTF-8 bytes".into()),
    }
}
fn ack(value: &Value) -> bool {
    value.as_object().is_some_and(|o| {
        o.get("ok") == Some(&json!(true))
            && o.keys().all(|k| k == "ok" || k == "message")
            && o.get("message").is_none_or(Value::is_string)
    })
}
impl Extension for Adapter {
    fn id(&self) -> &'static str {
        "com.tezbar.native.ip-tools"
    }
    fn version(&self) -> &'static str {
        env!("CARGO_PKG_VERSION")
    }
    fn commands(&self) -> &'static [&'static str] {
        COMMANDS
    }
    fn handle<'a>(
        &'a self,
        ctx: &'a ExtensionContext,
        command: &'a str,
        operation: &'a str,
        payload: &'a Value,
        _state: &'a mut Value,
    ) -> BoxFuture<'a, CoreResult> {
        Box::pin(async move {
            let id = payload["sessionId"].as_str().ok_or("Missing session")?;
            if operation == "extension:dispose-session" {
                if let Ok(s) = self.lookup(id) {
                    s.lock().unwrap().revoke();
                }
                self.sessions.lock().unwrap().remove(id);
                return Ok(tezbar_extension_sdk::no_view("Disposed"));
            }
            let session = if operation == "extension:run-command" {
                self.create(ctx, id, command)?
            } else {
                self.lookup(id)?
            };
            match operation {
                "extension:run-command" | "extension:search-text-changed" => {
                    let mut s = session.lock().unwrap();
                    let storage_notice = if operation == "extension:run-command" {
                        s.notice.clone()
                    } else {
                        None
                    };
                    s.revoke();
                    s.client_owned = false;
                    s.notice = storage_notice;
                    // SDK launch always includes searchText:null. Original argument still wins.
                    let value = if operation == "extension:run-command" {
                        payload
                            .get("searchText")
                            .filter(|v| !v.is_null())
                            .or_else(|| payload["argumentValues"].get("keywork"))
                    } else {
                        payload.get("searchText")
                    };
                    match input(value) {
                        Ok(q) => s.query = q,
                        Err(message) => {
                            s.query = String::new();
                            empty(&mut s, message, "XMarkCircle");
                            return Ok(render(command, &mut s));
                        }
                    }
                    drop(s);
                    self.update(ctx, command, &session)
                }
                "extension:invoke-action" => {
                    let token = payload["actionId"].as_str().unwrap_or("");
                    if token == "control:input" {
                        let form = &payload["formValues"];
                        let mut s = session.lock().unwrap();
                        // Client revisions are independent of model/effect epochs. A full
                        // draft makes crossed query/control arrivals atomic, including A/B/A.
                        let revision = form["revision"]
                            .as_u64()
                            .filter(|n| *n <= 9_007_199_254_740_991);
                        if revision.is_some_and(|n| n <= s.client_revision) {
                            return Ok(tezbar_extension_sdk::unchanged());
                        }
                        s.revoke(); // malformed new input revokes effects before validation
                        let Some(revision) = revision.filter(|n| *n > 0) else {
                            empty(&mut s, "Invalid client revision".into(), "XMarkCircle");
                            return Ok(render(command, &mut s));
                        };
                        s.client_revision = revision;
                        s.client_owned = true;
                        match input(form.get("searchText")) {
                            Ok(q) => s.query = q,
                            Err(message) => {
                                s.query.clear();
                                empty(&mut s, message, "XMarkCircle");
                                return Ok(render(command, &mut s));
                            }
                        }
                        if let Some(options) = choices(command) {
                            let value = form["value"].as_str();
                            if !options.iter().any(|(id, _)| Some(*id) == value) {
                                empty(&mut s, "Invalid selection".into(), "XMarkCircle");
                                return Ok(render(command, &mut s));
                            }
                            let value = value.unwrap();
                            if s.choice != value {
                                if let Err(error) =
                                    settings::save(&ctx.paths.data_dir, command, value)
                                {
                                    s.notice = Some(error);
                                }
                            }
                            s.choice = value.into();
                        }
                        drop(s);
                        return self.update(ctx, command, &session);
                    }
                    if token == "control:choice" {
                        let value = payload["formValues"]["value"].as_str();
                        let mut s = session.lock().unwrap();
                        s.revoke();
                        s.client_owned = false;
                        let valid = choices(command)
                            .is_some_and(|opts| opts.iter().any(|(id, _)| Some(*id) == value));
                        if !valid {
                            empty(&mut s, "Invalid selection".into(), "XMarkCircle");
                            return Ok(render(command, &mut s));
                        }
                        if let Err(error) =
                            settings::save(&ctx.paths.data_dir, command, value.unwrap())
                        {
                            s.notice = Some(error);
                        }
                        s.choice = value.unwrap().into();
                        drop(s);
                        return self.update(ctx, command, &session);
                    }
                    let (effect, epoch) = {
                        let mut s = session.lock().unwrap();
                        let Some(effect) = s.tokens.remove(token) else {
                            return Ok(tezbar_extension_sdk::unchanged());
                        };
                        s.uncertain = Some(effect.clone());
                        s.notice = Some(
                            "Copy outcome unknown. Retry Exact Copy may duplicate delivery.".into(),
                        );
                        (effect, s.epoch)
                    };
                    let result = tokio::time::timeout(
                        std::time::Duration::from_secs(3),
                        ctx.host("host.clipboard.write", json!({"text":effect.text.as_ref()})),
                    )
                    .await;
                    let mut s = session.lock().unwrap();
                    if s.epoch != epoch {
                        return Ok(tezbar_extension_sdk::unchanged());
                    }
                    if matches!(result,Ok(Ok(ref value)) if ack(value)) {
                        s.uncertain = None;
                        s.notice = Some("Copied to clipboard".into());
                        s.issue();
                    } // fresh tokens only after deliberate completed action
                    Ok(render(command, &mut s))
                }
                "extension:refresh-session" | "extension:load-more" => {
                    Ok(render(command, &mut session.lock().unwrap()))
                }
                _ => Err("Unsupported operation".into()),
            }
        })
    }
}
