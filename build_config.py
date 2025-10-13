#!/usr/bin/env python3
"""
Configurações para compilação do executável
"""

# Configurações do PyInstaller
PYINSTALLER_CONFIG = {
    "name": "YupooDownloader",
    "onefile": True,
    "windowed": True,
    "icon": "icon.ico",  # Opcional
    "clean": True,
    "noconfirm": True,
    
    # Arquivos a incluir
    "add_data": [
        "yupoo_parallel_downloader.py;.",
    ],
    
    # Imports ocultos
    "hidden_imports": [
        "selenium",
        "webdriver_manager",
        "webdriver_manager.chrome",
        "PIL",
        "PIL.Image",
        "requests",
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        "queue",
        "threading",
        "concurrent.futures",
        "selenium.webdriver",
        "selenium.webdriver.chrome",
        "selenium.webdriver.chrome.options",
        "selenium.webdriver.common.by",
        "selenium.webdriver.support.ui",
        "selenium.webdriver.support.expected_conditions",
        "selenium.common.exceptions",
    ],
    
    # Excluir módulos desnecessários
    "exclude_modules": [
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "jupyter",
        "IPython",
    ],
    
    # Otimizações
    "optimize": 2,
    "strip": True,
}

# Informações do executável
EXECUTABLE_INFO = {
    "version": "1.0.0",
    "description": "Yupoo Album Downloader 2025 - GUI Version",
    "author": "felcoslop",
    "company": "Yupoo Downloader",
    "copyright": "© 2025 Yupoo Downloader. All rights reserved.",
}

# Arquivos necessários para o executável
REQUIRED_FILES = [
    "yupoo_gui.py",
    "yupoo_parallel_downloader.py",
    "requirements_gui.txt",
]

# Arquivos opcionais
OPTIONAL_FILES = [
    "icon.ico",
    "README_GUI.md",
]

def get_pyinstaller_command():
    """Gera o comando PyInstaller baseado na configuração"""
    cmd = ["pyinstaller"]
    
    # Configurações básicas
    if PYINSTALLER_CONFIG["onefile"]:
        cmd.append("--onefile")
    
    if PYINSTALLER_CONFIG["windowed"]:
        cmd.append("--windowed")
    
    if PYINSTALLER_CONFIG["clean"]:
        cmd.append("--clean")
    
    if PYINSTALLER_CONFIG["noconfirm"]:
        cmd.append("--noconfirm")
    
    # Nome
    cmd.extend(["--name", PYINSTALLER_CONFIG["name"]])
    
    # Ícone (se existir)
    if PYINSTALLER_CONFIG["icon"] and os.path.exists(PYINSTALLER_CONFIG["icon"]):
        cmd.extend(["--icon", PYINSTALLER_CONFIG["icon"]])
    
    # Adicionar dados
    for data in PYINSTALLER_CONFIG["add_data"]:
        cmd.extend(["--add-data", data])
    
    # Imports ocultos
    for imp in PYINSTALLER_CONFIG["hidden_imports"]:
        cmd.extend(["--hidden-import", imp])
    
    # Excluir módulos
    for mod in PYINSTALLER_CONFIG["exclude_modules"]:
        cmd.extend(["--exclude-module", mod])
    
    # Otimizações
    if PYINSTALLER_CONFIG["optimize"]:
        cmd.extend(["--optimize", str(PYINSTALLER_CONFIG["optimize"])])
    
    if PYINSTALLER_CONFIG["strip"]:
        cmd.append("--strip")
    
    # Arquivo principal
    cmd.append("yupoo_gui.py")
    
    return cmd

if __name__ == "__main__":
    import os
    cmd = get_pyinstaller_command()
    print("Comando PyInstaller:")
    print(" ".join(cmd))
