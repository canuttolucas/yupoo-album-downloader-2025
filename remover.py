import os
import shutil
import logging

class PhotoCleaner:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.stats = {"processed": 0, "moved": 0}

    def log(self, message, level="INFO"):
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")

    def cleanup(self, root_path, keywords_str, exclude_folders_str):
        """
        Traverses directories, moves files matching keywords to 'ANTIGAS' folders.
        """
        self.stats = {"processed": 0, "moved": 0}
        
        # Parse inputs
        keywords = [k.strip() for k in keywords_str.split(';') if k.strip()]
        exclude_folders = [e.strip() for e in exclude_folders_str.split(';') if e.strip()]
        # Fallback for comma separated if no semicolon found and commas exist
        if not exclude_folders and ',' in exclude_folders_str:
            exclude_folders = [e.strip() for e in exclude_folders_str.split(',') if e.strip()]
        
        target_folder_name = "ANTIGAS (TALVEZ NÃO TENHA ESTOQUE)"
        
        if not keywords:
            self.log("Nenhuma palavra-chave informada.", "ERROR")
            return self.stats

        if not os.path.exists(root_path):
            self.log(f"Caminho não encontrado: {root_path}", "ERROR")
            return self.stats

        self.log(f"Iniciando limpeza em: {root_path}")
        self.log(f"Palavras-chave: {keywords}")
        self.log(f"Pastas excluídas: {exclude_folders}")

        for root, dirs, files in os.walk(root_path):
            # Exclude folders
            # We modify dirs in-place to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in exclude_folders and d != target_folder_name]

            # Current folder being scanned
            files_to_move = []
            for file in files:
                self.stats["processed"] += 1
                match = any(kw.lower() in file.lower() for kw in keywords)
                if match:
                    files_to_move.append(file)

            if files_to_move:
                dest_dir = os.path.join(root, target_folder_name)
                if not os.path.exists(dest_dir):
                    try:
                        os.makedirs(dest_dir)
                        self.log(f"Criada pasta: {dest_dir}", "DEBUG")
                    except Exception as e:
                        self.log(f"Erro ao criar pasta {dest_dir}: {e}", "ERROR")
                        continue

                for file in files_to_move:
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(dest_dir, file)
                    
                    # Handle name collisions
                    if os.path.exists(dst_path):
                        base, ext = os.path.splitext(file)
                        dst_path = os.path.join(dest_dir, f"{base}_{int(os.path.getmtime(src_path))}{ext}")

                    try:
                        shutil.move(src_path, dst_path)
                        self.stats["moved"] += 1
                    except Exception as e:
                        self.log(f"Erro ao mover {file}: {e}", "ERROR")

        self.log(f"Limpeza concluída. Processados: {self.stats['processed']}, Movidos: {self.stats['moved']}")
        return self.stats

if __name__ == "__main__":
    # Test block
    import sys
    if len(sys.argv) > 1:
        cleaner = PhotoCleaner()
        path = sys.argv[1]
        kws = sys.argv[2] if len(sys.argv) > 2 else ""
        excl = sys.argv[3] if len(sys.argv) > 3 else ""
        cleaner.cleanup(path, kws, excl)
