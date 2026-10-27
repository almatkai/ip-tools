use tezbar_ip_tools::net;
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    net::TcpListener,
};
async fn fixture(response: Vec<u8>) -> (String, tokio::task::JoinHandle<String>) {
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let task = tokio::spawn(async move {
        let (mut stream, _) = listener.accept().await.unwrap();
        let mut req = vec![0; 8192];
        let n = stream.read(&mut req).await.unwrap();
        stream.write_all(&response).await.unwrap();
        String::from_utf8(req[..n].to_vec()).unwrap()
    });
    (
        format!("http://{addr}/json/::1?lang=zh-CN&&fields=61151"),
        task,
    )
}
#[tokio::test]
async fn production_http_success_exact_query_and_bounded_failures() {
    let body = r#"{"status":"success","query":"::1","country":"Fixture","lat":1.25}"#;
    let (url, server) = fixture(
        format!(
            "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            body.len(),
            body
        )
        .into_bytes(),
    )
    .await;
    let value = net::fetch(&net::client().unwrap(), &url).await.unwrap();
    assert_eq!(value["country"], "Fixture");
    let request = server.await.unwrap();
    assert!(request.starts_with("GET /json/::1?lang=zh-CN&&fields=61151 HTTP/1.1\r\n"));
    for response in [
        b"HTTP/1.1 500 Nope\r\nContent-Length: 0\r\n\r\n".to_vec(),
        b"HTTP/1.1 200 OK\r\nContent-Length: 999999\r\n\r\n".to_vec(),
        b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nnope".to_vec(),
        format!(
            "HTTP/1.1 200 OK\r\nContent-Length: {}\r\n\r\n{}",
            30, "[1,2]"
        )
        .into_bytes(),
    ] {
        let (url, server) = fixture(response).await;
        let e = net::fetch(&net::client().unwrap(), &url).await.unwrap_err();
        assert!(!e.contains(&url));
        assert!(!e.contains("127.0.0.1"));
        server.await.unwrap();
    }
}
#[tokio::test]
async fn body_structure_limits_and_cancellation() {
    for body in [
        format!("{{\"x\":{}{}}}", "[".repeat(14), "]".repeat(14)),
        format!(
            "{{{}}}",
            (0..129)
                .map(|i| format!("\"k{i}\":{i}"))
                .collect::<Vec<_>>()
                .join(",")
        ),
    ] {
        let (url, server) = fixture(
            format!(
                "HTTP/1.1 200 OK\r\nContent-Length: {}\r\n\r\n{body}",
                body.len()
            )
            .into_bytes(),
        )
        .await;
        assert!(net::fetch(&net::client().unwrap(), &url).await.is_err());
        server.await.unwrap();
    }
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let url = format!("http://{}/", listener.local_addr().unwrap());
    let client = net::client().unwrap();
    let request = net::fetch(&client, &url);
    tokio::pin!(request);
    tokio::select! {r=&mut request=>panic!("unexpected {r:?}"),_ = tokio::time::sleep(std::time::Duration::from_millis(25))=>{}}
    // Whole future is dropped at test return; no detached request tasks.
}
