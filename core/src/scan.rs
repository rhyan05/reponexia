use std::fs::read_dir;
use std::path::{Path, PathBuf};

pub fn collect_files(root: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    
    if let Ok(entries) = read_dir(root){
        // Itera sobre cada entrada no diretório
        for entry in entries.flatten() {
            let Ok(ft) = entry.file_type() else {
                continue;
            };
            if ft.is_dir(){
                let name = entry.file_name();
                if name == ".git" || name == "node_modules" || name == "target" || name == "__pycache__" {
                    continue; // pula a recursão, mas NÃO adiciona ao resultado (é diretório, não arquivo)
                }
                files.extend(collect_files(&entry.path())); // recursão para subdiretórios
            } else if ft.is_file() {
                files.push(entry.path()); // adiciona o arquivo ao resultado
            }


        }
    }
    files
}
