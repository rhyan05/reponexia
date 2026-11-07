use std::collections::BTreeMap;

use crate::models::{Entrypoint, FileEntry};

pub struct RawScriptImport {
    pub module: String,
    pub evidence: String,
}

pub fn detect(
    rel: &str,
    bytes: &[u8],
    entries: &mut Vec<Entrypoint>,
    script_imports: &mut Vec<RawScriptImport>,
) {
    let name = rel.rsplit('/').next().unwrap_or(rel);

    if name == "__main__.py" {
        entries.push(Entrypoint {
            path: rel.to_string(),
            kind: "package_main".to_string(),
            evidence: format!("{rel}:1"),
        });
    } else if name == "main.py" {
        entries.push(Entrypoint {
            path: rel.to_string(),
            kind: "main".to_string(),
            evidence: format!("{rel}:1"),
        });
    } else if rel.ends_with(".py") {
        if let Some(line) = main_guard_line(bytes) {
            entries.push(Entrypoint {
                path: rel.to_string(),
                kind: "main".to_string(),
                evidence: format!("{rel}:{line}"),
            });
        }
    }

    if name == "pyproject.toml" {
        collect_scripts(bytes, script_imports);
    }
}

fn main_guard_line(bytes: &[u8]) -> Option<usize> {
    // ponytail: heuristica textual; trocar por AST (if_statement) se der falso positivo
    let text = String::from_utf8_lossy(bytes);
    text.lines()
        .position(|line| line.contains("__name__") && line.contains("__main__"))
        .map(|index| index + 1)
}

fn collect_scripts(bytes: &[u8], scripts: &mut Vec<RawScriptImport>) {
    let text = String::from_utf8_lossy(bytes);
    let mut in_scripts = false;

    for (index, line) in text.lines().enumerate() {
        let trimmed = line.trim();

        if trimmed.starts_with('[') {
            in_scripts = trimmed == "[project.scripts]" || trimmed == "[tool.poetry.scripts]";
            continue;
        }

        if !in_scripts {
            continue;
        }

        let Some((_, value)) = trimmed.split_once('=') else {
            continue;
        };
        let target = value.trim().trim_matches('"');
        let Some((module, _func)) = target.split_once(':') else {
            continue;
        };

        scripts.push(RawScriptImport {
            module: module.to_string(),
            evidence: format!("pyproject.toml:{}", index + 1),
        });
    }
}

pub fn resolve_script_imports(
    files: &[FileEntry],
    script_imports: &[RawScriptImport],
    entries: &mut Vec<Entrypoint>,
) {
    let index = crate::resolve::build_index(files);

    for script_import in script_imports {
        if let Some(path) = index.get(&script_import.module) {
            entries.push(Entrypoint {
                path: path.clone(),
                kind: "console_script".to_string(),
                evidence: script_import.evidence.clone(),
            });
        }
    }
}

pub fn dedupe(entries: Vec<Entrypoint>) -> Vec<Entrypoint> {
    fn priority(kind: &str) -> u8 {
        match kind {
            "package_main" => 3,
            "console_script" => 2,
            "main" => 1,
            _ => 0,
        }
    }

    let mut by_path: BTreeMap<String, Entrypoint> = BTreeMap::new();
    for entry in entries {
        let replace = match by_path.get(&entry.path) {
            Some(old) => priority(&entry.kind) > priority(&old.kind),
            None => true,
        };
        if replace {
            by_path.insert(entry.path.clone(), entry);
        }
    }

    let mut result: Vec<Entrypoint> = by_path.into_values().collect();
    result.sort_by(|a, b| {
        (&a.path, &a.kind, &a.evidence).cmp(&(&b.path, &b.kind, &b.evidence))
    });
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn entry(path: &str) -> FileEntry {
        FileEntry {
            path: path.to_string(),
            language: "python".to_string(),
            loc: 1,
            hash: String::new(),
            parse_errors: Vec::new(),
        }
    }

    #[test]
    fn detecta_main_e_package_main() {
        let mut entries = Vec::new();
        let mut scripts = Vec::new();

        detect("pkg/__main__.py", b"", &mut entries, &mut scripts);
        detect("src/main.py", b"", &mut entries, &mut scripts);

        assert_eq!(entries[0].kind, "package_main");
        assert_eq!(entries[0].path, "pkg/__main__.py");
        assert_eq!(entries[1].kind, "main");
        assert_eq!(entries[1].path, "src/main.py");
    }

    #[test]
    fn detecta_guarda_com_linha_real() {
        let mut entries = Vec::new();
        let mut scripts = Vec::new();
        let source = b"x = 1\n\nif __name__ == \"__main__\":\n    pass\n";

        detect("app/run.py", source, &mut entries, &mut scripts);

        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].kind, "main");
        assert_eq!(entries[0].evidence, "app/run.py:3");
    }

    #[test]
    fn coleta_script_do_pyproject() {
        let mut entries = Vec::new();
        let mut scripts = Vec::new();
        let source =
            b"[project]\nname = \"x\"\n\n[project.scripts]\nreponexia = \"reponexia.cli:main\"\n";

        detect("pyproject.toml", source, &mut entries, &mut scripts);

        assert_eq!(scripts.len(), 1);
        assert_eq!(scripts[0].module, "reponexia.cli");
        assert_eq!(scripts[0].evidence, "pyproject.toml:5");
    }

    #[test]
    fn resolve_script_para_arquivo() {
        let files = vec![entry("src/reponexia/cli.py")];
        let scripts = vec![RawScriptImport {
            module: "reponexia.cli".to_string(),
            evidence: "pyproject.toml:5".to_string(),
        }];
        let mut entries = Vec::new();

        resolve_script_imports(&files, &scripts, &mut entries);

        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].path, "src/reponexia/cli.py");
        assert_eq!(entries[0].kind, "console_script");
        assert_eq!(entries[0].evidence, "pyproject.toml:5");
    }

    #[test]
    fn dedupe_prefere_package_main() {
        let entries = vec![
            Entrypoint {
                path: "p/__main__.py".to_string(),
                kind: "main".to_string(),
                evidence: "p/__main__.py:3".to_string(),
            },
            Entrypoint {
                path: "p/__main__.py".to_string(),
                kind: "package_main".to_string(),
                evidence: "p/__main__.py:1".to_string(),
            },
        ];

        let result = dedupe(entries);

        assert_eq!(result.len(), 1);
        assert_eq!(result[0].kind, "package_main");
    }
}
