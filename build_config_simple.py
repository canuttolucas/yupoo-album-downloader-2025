#!/usr/bin/env python3
"""
Configurações simplificadas para compilação do executável
"""

def get_pyinstaller_command():
    """Gera o comando PyInstaller simplificado para melhor compatibilidade"""
    import os
    cmd = ["python", "-m", "PyInstaller"]
    
    # Configurações básicas
    cmd.extend([
        "--onefile",
        "--windowed", 
        "--clean",
        "--noconfirm",
        "--name", "YupooDownloader",
        "--noupx",  # Desabilita UPX para evitar problemas de DLL
        "--debug=all",  # Modo debug para identificar problemas
    ])
    
    # Adicionar dados
    cmd.extend(["--add-data", "yupoo_parallel_downloader.py;."])
    cmd.extend(["--add-data", "yupoo_gui_downloader.py;."])
    cmd.extend(["--add-data", "yupoo_advanced_downloader.py;."])
    
    # Imports essenciais
    essential_imports = [
        "selenium",
        "webdriver_manager", 
        "PIL",
        "requests",
        "tkinter",
        "queue",
        "threading",
        "concurrent.futures",
    ]
    
    for imp in essential_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Arquivo principal
    cmd.append("yupoo_gui.py")
    
    return cmd

if __name__ == "__main__":
    import os
    cmd = get_pyinstaller_command()
    print("Comando PyInstaller:")
    print(" ".join(cmd))


