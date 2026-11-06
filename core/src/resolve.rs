use std::collections::{BTreeMap, BTreeSet};

use crate::models::{Edge, FileEntry};
use crate::parse::RawImport;

pub fn build_index(files: &[FileEntry]) -> BTreeMap<String, String> {
    let mut index = BTreeMap::new();

    for file in files {
        if file.language != "python" {
            continue;
        }
        let Some(stem) = file.path.strip_suffix(".py") else {
            continue;
        };
        let mut parts: Vec<&str> = stem.split('/').collect();
        if parts.last() == Some(&"__init__") {
            parts.pop();
        }
        if parts.is_empty() {
            continue;
        }
        for start in (0..parts.len()).rev() {
            let module = parts[start..].join(".");
            index.entry(module).or_insert_with(|| file.path.clone());
        }
    }

    index
}

fn resolve_one(
    index: &BTreeMap<String, String>,
    known: &BTreeSet<&str>,
    importer: &str,
    raw: &RawImport,
) -> Option<String> {
    if raw.level == 0 {
        return index.get(&raw.module).cloned();
    }

    let dir = importer.rsplit_once('/').map(|(d, _)| d).unwrap_or("");
    let mut parts: Vec<&str> = if dir.is_empty() {
        Vec::new()
    } else {
        dir.split('/').collect()
    };

    let up = raw.level.saturating_sub(1);
    if up > parts.len() {
        return None;
    }
    parts.truncate(parts.len() - up);

    if !raw.module.is_empty() {
        parts.extend(raw.module.split('.'));
    }

    let base = parts.join("/");
    if base.is_empty() {
        return None;
    }

    let file = format!("{base}.py");
    if known.contains(file.as_str()) {
        return Some(file);
    }

    let init = format!("{base}/__init__.py");
    if known.contains(init.as_str()) {
        return Some(init);
    }

    None
}

pub fn resolve_imports(files: &[FileEntry], imports: &[RawImport]) -> Vec<Edge> {
    let index = build_index(files);
    let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();

    let mut edges = Vec::new();
    for raw in imports {
        let Some(to) = resolve_one(&index, &known, &raw.file, raw) else {
            continue;
        };
        if to == raw.file {
            continue;
        }
        edges.push(Edge {
            from: raw.file.clone(),
            to,
            kind: "import".to_string(),
            line: raw.line,
            symbol: if raw.module.is_empty() {
                None
            } else {
                Some(raw.module.clone())
            },
        });
    }

    edges.sort_by(|a, b| (&a.from, &a.to, a.line).cmp(&(&b.from, &b.to, b.line)));
    edges
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
    fn registra_sufixos_do_layout_src() {
        let files = vec![entry("src/reponexia/core_runner.py")];
        let index = build_index(&files);
        assert_eq!(
            index.get("reponexia.core_runner").unwrap(),
            "src/reponexia/core_runner.py"
        );
        assert_eq!(
            index.get("core_runner").unwrap(),
            "src/reponexia/core_runner.py"
        );
        assert_eq!(
            index.get("src.reponexia.core_runner").unwrap(),
            "src/reponexia/core_runner.py"
        );
    }

    #[test]
    fn registra_init_como_pacote() {
        let files = vec![entry("src/reponexia/__init__.py")];
        let index = build_index(&files);
        assert_eq!(
            index.get("reponexia").unwrap(),
            "src/reponexia/__init__.py"
        );
        assert!(index.get("__init__").is_none());
    }

    #[test]
    fn resolve_import_relativo() {
        let files = vec![entry("src/pkg/app.py"), entry("src/pkg/util.py")];
        let index = build_index(&files);
        let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
        let raw = RawImport {
            file: "src/pkg/app.py".into(),
            module: "util".into(),
            level: 1,
            line: 3,
        };
        assert_eq!(
            resolve_one(&index, &known, &raw.file, &raw),
            Some("src/pkg/util.py".to_string())
        );
    }

    #[test]
    fn resolve_import_relativo_subindo() {
        let files = vec![entry("src/pkg/sub/app.py"), entry("src/pkg/util.py")];
        let index = build_index(&files);
        let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
        let raw = RawImport {
            file: "src/pkg/sub/app.py".into(),
            module: "util".into(),
            level: 2,
            line: 3,
        };
        assert_eq!(
            resolve_one(&index, &known, &raw.file, &raw),
            Some("src/pkg/util.py".to_string())
        );
    }

    #[test]
    fn externo_nao_resolve() {
        let files = vec![entry("src/pkg/app.py")];
        let index = build_index(&files);
        let known: BTreeSet<&str> = files.iter().map(|f| f.path.as_str()).collect();
        let raw = RawImport {
            file: "src/pkg/app.py".into(),
            module: "json".into(),
            level: 0,
            line: 1,
        };
        assert_eq!(resolve_one(&index, &known, &raw.file, &raw), None);
    }

    #[test]
    fn descarta_self_import() {
        let files = vec![entry("src/pkg/app.py")];
        let imports = vec![RawImport {
            file: "src/pkg/app.py".into(),
            module: "app".into(),
            level: 0,
            line: 1,
        }];
        assert!(resolve_imports(&files, &imports).is_empty());
    }
}
