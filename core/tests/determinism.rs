use std::process::Command;

fn run_index(dir: &str) -> Vec<u8> {
    let exe = env!("CARGO_BIN_EXE_reponexia-core");

    let output = Command::new(exe)
        .args(["index", dir])
        .output()
        .expect("falha ao executar o reponexia-core");

    assert!(
        output.status.success(),
        "core falhou: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    output.stdout
}

#[test]
fn duas_execucoes_produzem_saida_identica() {
    let dir = env!("CARGO_MANIFEST_DIR");
    assert_eq!(run_index(dir), run_index(dir));
}

#[test]
fn warnings_saem_em_ordem_estavel() {
    let dir = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/fixtures/broken");
    let first = run_index(dir);
    let second = run_index(dir);

    assert_eq!(first, second, "duas execucoes divergiram");

    let graph: serde_json::Value = serde_json::from_slice(&first).unwrap();
    let warnings = graph["warnings"].as_array().unwrap();
    assert_eq!(warnings.len(), 2, "esperava um warning por arquivo invalido");

    let paths: Vec<&str> = warnings
        .iter()
        .map(|warning| warning["path"].as_str().unwrap())
        .collect();
    assert_eq!(paths, vec!["a_bad.py", "z_bad.py"]);
}
