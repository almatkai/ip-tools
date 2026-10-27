"""Compile the entire pinned clipboard producer; replace OS providers before loading."""
import pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];p=ROOT/'.work/host-producer';(p/'src').mkdir(parents=True,exist_ok=True)
source=ROOT/'qa/fixtures/host/src-tauri/src/native_core/launcher/clipboard.rs'
(p/'src/clipboard.rs').write_text('use crate::arboard;\n'+source.read_text())
(p/'Cargo.toml').write_text('''[package]
name="ip-tools-unshipped-host-producer-qa"
version="0.0.0"
edition="2021"
rust-version="1.85"
[workspace]
[dependencies]
serde_json="1"
tokio={version="1",features=["rt-multi-thread","macros","sync"]}
base64="0.22"
sha1="0.10"
regex="1"
image={version="=0.25.6",default-features=false,features=["png"]}
log="0.4"
''')
(p/'src/text_arg.rs').write_bytes((ROOT/'qa/fixtures/host/exports/text_arg.rs').read_bytes())
(p/'src/main.rs').write_text(r'''
#![allow(dead_code)]
use serde_json::{json,Value};
use std::sync::{Mutex,atomic::{AtomicBool,Ordering}};
static WRITES:Mutex<Vec<String>>=Mutex::new(vec![]);
static FAIL:AtomicBool=AtomicBool::new(false);
mod arboard {
 use std::borrow::Cow;
 #[derive(Debug)]pub enum Error {ContentNotAvailable,FixtureFailure}
 impl std::fmt::Display for Error {fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result {write!(f,"{self:?}")}}
 pub struct Clipboard;
 pub struct ImageData<'a>{pub width:usize,pub height:usize,pub bytes:Cow<'a,[u8]>}
 impl Clipboard {
 pub fn new()->Result<Self,Error>{Ok(Self)}
 pub fn get_text(&self)->Result<String,Error>{Err(Error::ContentNotAvailable)}
 pub fn get_image(&self)->Result<ImageData<'static>,Error>{Err(Error::ContentNotAvailable)}
 pub fn set_image(&mut self,_:ImageData<'_>)->Result<(),Error>{panic!("Image OS boundary forbidden")}
 pub fn set_text(&mut self,text:String)->Result<(),Error>{if crate::FAIL.load(std::sync::atomic::Ordering::SeqCst){return Err(Error::FixtureFailure)}crate::WRITES.lock().unwrap().push(text);Ok(())}
 }
}
mod native_core {pub mod common {
 use serde_json::{Value,json};use std::path::{Path,PathBuf};
 pub type CoreResult=Result<Value,String>;
 #[derive(Clone)] pub struct CorePaths{pub data_dir:PathBuf}
 #[derive(Clone)] pub struct Config;
 impl Config{pub fn read(&self)->CoreResult{Ok(json!({}))}}
 #[derive(Clone)] pub struct CoreContext {pub paths:CorePaths,pub config:Config}
 impl CoreContext{pub fn emit(&self,_:&str,_:Value){panic!("Unexpected event")}}
 pub fn now_ms()->u64 {0}
 pub fn write_json_atomic(_:&Path,_:&Value)->Result<(),String>{panic!("Host fixture persistence forbidden")}
}}
mod clipboard_native {pub fn sequence()->Option<u64>{None}pub fn files()->Vec<String>{vec![]}pub fn write_files(_:&[String])->Result<(),String>{panic!("Files OS boundary forbidden")}}
mod stores {use serde_json::Value;use std::path::Path;pub fn read_or(_:&Path,_:Value)->Result<Value,String>{panic!("Host fixture storage forbidden")}
 include!("text_arg.rs");}
mod clipboard;
#[tokio::main(worker_threads=2)] async fn main(){
 let root=std::env::args().nth(1).unwrap();let c=clipboard::ClipboardCore::new(native_core::common::CoreContext{paths:native_core::common::CorePaths{data_dir:root.into()},config:native_core::common::Config});
 for text in ["", "340282366920938463463374607431768211455", "{\n  \"ipCount\": 340282366920938463463374607431768211456\n}","复制"] {
 assert_eq!(c.handle("clipboard:write",&[json!(text)]).await.unwrap(),json!({"ok":true}));assert_eq!(WRITES.lock().unwrap().last().unwrap(),text);
 }
 for bad in [Value::Null,json!(1),json!({})] {assert!(c.handle("clipboard:write",&[bad]).await.is_err());}
 FAIL.store(true,Ordering::SeqCst);assert!(c.handle("clipboard:write",&[json!("x")]).await.is_err());assert_eq!(WRITES.lock().unwrap().len(),4);c.shutdown().await;
 println!("Full pinned ClipboardCore producer: 8 checks; OS writes replaced, no real clipboard/files");
}
''')
(p/'Cargo.lock').write_bytes((ROOT/'qa/locks/host-producer.Cargo.lock').read_bytes())
subprocess.run([str(ROOT/'qa/env.sh'),'cargo','build','--locked','--manifest-path',str(p/'Cargo.toml'),'--config','resolver.incompatible-rust-versions="fallback"'],check=True,stdout=open(ROOT/'.work/host-producer-build.log','w'),stderr=subprocess.STDOUT)
subprocess.run([str(ROOT/'.work/target/debug/ip-tools-unshipped-host-producer-qa'),str(ROOT/'.work/host-producer-private')],check=True)
