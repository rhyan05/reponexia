use tree_sitter::{Node, Parser};

use crate::models::Symbol;

pub struct RawImport {
    pub file: String,
    pub module: String,
    pub level: usize,
    pub line: usize,
}

pub struct ParsedFile {
    pub symbols: Vec<Symbol>,
    pub imports: Vec<RawImport>,
}

pub fn new_parser() -> Result<Parser, tree_sitter::LanguageError> {
    let mut parser = Parser::new();
    parser.set_language(&tree_sitter_python::LANGUAGE.into())?;
    Ok(parser)
}

pub fn parse_python(
    file: &str,
    bytes: &[u8],
    parser: &mut Parser,
) -> Result<ParsedFile, String> {
    let tree = parser
        .parse(bytes, None)
        .ok_or_else(|| "parser nao retornou arvore".to_string())?;

    let root = tree.root_node();
    if root.has_error() {
        return Err("erro de sintaxe no arquivo".to_string());
    }

    let mut symbols = Vec::new();
    let mut imports = Vec::new();

    let mut cursor = root.walk();
    for child in root.named_children(&mut cursor) {
        let child = unwrap_decorated(child);
        match child.kind() {
            "function_definition" => {
                push_symbol(&mut symbols, file, bytes, child, "function", None);
            }
            "class_definition" => {
                let Some(name_node) = child.child_by_field_name("name") else {
                    continue;
                };
                let class_name = text(name_node, bytes);
                push_symbol(&mut symbols, file, bytes, child, "class", None);

                let Some(body) = child.child_by_field_name("body") else {
                    continue;
                };
                let mut body_cursor = body.walk();
                for item in body.named_children(&mut body_cursor) {
                    let item = unwrap_decorated(item);
                    if item.kind() == "function_definition" {
                        push_symbol(
                            &mut symbols,
                            file,
                            bytes,
                            item,
                            "method",
                            Some(&class_name),
                        );
                    }
                }
            }
            "import_statement" => {
                let mut import_cursor = child.walk();
                for item in child.named_children(&mut import_cursor) {
                    let target = if item.kind() == "aliased_import" {
                        item.child_by_field_name("name").unwrap_or(item)
                    } else {
                        item
                    };
                    imports.push(RawImport {
                        file: file.to_string(),
                        module: text(target, bytes),
                        level: 0,
                        line: child.start_position().row + 1,
                    });
                }
            }
            "import_from_statement" => {
                if let Some(module_node) = child.child_by_field_name("module_name") {
                    let raw = text(module_node, bytes);
                    let level = raw.chars().take_while(|c| *c == '.').count();
                    imports.push(RawImport {
                        file: file.to_string(),
                        module: raw[level..].to_string(),
                        level,
                        line: child.start_position().row + 1,
                    });
                }
            }
            _ => {}
        }
    }

    symbols.sort_by(|a, b| (&a.id, a.line).cmp(&(&b.id, b.line)));
    Ok(ParsedFile { symbols, imports })
}

fn push_symbol(
    out: &mut Vec<Symbol>,
    file: &str,
    bytes: &[u8],
    node: Node<'_>,
    kind: &str,
    parent: Option<&str>,
) {
    let Some(name_node) = node.child_by_field_name("name") else {
        return;
    };
    let name = text(name_node, bytes);
    if name.is_empty() {
        return;
    }

    let id = match parent {
        Some(parent) => format!("{file}::{parent}.{name}"),
        None => format!("{file}::{name}"),
    };

    out.push(Symbol {
        id,
        file: file.to_string(),
        name: name.clone(),
        kind: kind.to_string(),
        line: node.start_position().row + 1,
        exported: !name.starts_with('_'),
    });
}

fn text(node: Node<'_>, bytes: &[u8]) -> String {
    node.utf8_text(bytes).unwrap_or("").to_string()
}

fn unwrap_decorated(node: Node<'_>) -> Node<'_> {
    if node.kind() == "decorated_definition" {
        node.child_by_field_name("definition").unwrap_or(node)
    } else {
        node
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extrai_imports_absolutos_e_relativos() {
        let src = b"import os, sys\nimport pkg.sub as ps\nfrom .util import x\nfrom ..core import y\n";
        let mut parser = new_parser().unwrap();
        let out = parse_python("pkg/app.py", src, &mut parser).unwrap();

        let got: Vec<(&str, usize)> = out
            .imports
            .iter()
            .map(|i| (i.module.as_str(), i.level))
            .collect();

        assert_eq!(
            got,
            vec![("os", 0), ("sys", 0), ("pkg.sub", 0), ("util", 1), ("core", 2)]
        );
    }
}
