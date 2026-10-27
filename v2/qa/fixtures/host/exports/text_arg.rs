pub fn text_arg(args: &[Value], n: usize) -> Result<&str, String> {
    args.get(n)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("Argument {} must be a string", n + 1))
}
