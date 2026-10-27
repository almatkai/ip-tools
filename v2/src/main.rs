fn main() {
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(2)
        .enable_all()
        .build()
        .expect("IP Tools runtime unavailable");
    let result = runtime.block_on(tezbar_extension_sdk::serve(
        tezbar_ip_tools::Adapter::default(),
    ));
    // System DNS may use an OS-owned blocking resolver. Never hold process EOF
    // indefinitely while Tokio waits for such a resolver to finish.
    runtime.shutdown_timeout(std::time::Duration::from_secs(2));
    if result.is_err() {
        eprintln!("IP Tools protocol stopped");
        std::process::exit(1);
    }
}
