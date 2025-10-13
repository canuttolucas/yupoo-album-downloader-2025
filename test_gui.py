#!/usr/bin/env python3
"""
Script de teste para a versão GUI
"""

import sys
import os

def test_imports():
    """Testa se todos os imports necessários estão funcionando"""
    print("Testando imports...")
    
    try:
        import tkinter as tk
        print("[OK] tkinter")
    except ImportError as e:
        print(f"[ERRO] tkinter: {e}")
        return False
    
    try:
        import selenium
        print("[OK] selenium")
    except ImportError as e:
        print(f"[ERRO] selenium: {e}")
        return False
    
    try:
        import webdriver_manager
        print("[OK] webdriver_manager")
    except ImportError as e:
        print(f"[ERRO] webdriver_manager: {e}")
        return False
    
    try:
        import PIL
        print("[OK] PIL (Pillow)")
    except ImportError as e:
        print(f"[ERRO] PIL: {e}")
        return False
    
    try:
        import requests
        print("[OK] requests")
    except ImportError as e:
        print(f"[ERRO] requests: {e}")
        return False
    
    return True

def test_files():
    """Testa se todos os arquivos necessários existem"""
    print("\nTestando arquivos...")
    
    required_files = [
        "yupoo_gui.py",
        "yupoo_parallel_downloader.py",
        "requirements_gui.txt",
        "build_executable.py",
        "build_config.py"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[ERRO] {file} - não encontrado")
            all_exist = False
    
    return all_exist

def test_gui_import():
    """Testa se a GUI pode ser importada"""
    print("\nTestando importação da GUI...")
    
    try:
        # Adicionar diretório atual ao path
        sys.path.insert(0, os.getcwd())
        
        # Importar tkinter primeiro
        import tkinter as tk
        
        # Tentar importar a GUI
        from yupoo_gui import YupooDownloaderGUI
        print("[OK] GUI importada com sucesso")
        
        # Testar criação básica (sem mostrar)
        root = tk.Tk()
        root.withdraw()  # Esconder janela
        app = YupooDownloaderGUI(root)
        root.destroy()
        print("[OK] GUI criada com sucesso")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao importar/criar GUI: {e}")
        return False

def test_downloader_import():
    """Testa se o downloader pode ser importado"""
    print("\nTestando importação do downloader...")
    
    try:
        from yupoo_parallel_downloader import YupooParallelDownloader
        print("[OK] Downloader importado com sucesso")
        
        # Testar criação básica
        downloader = YupooParallelDownloader(headless=True, max_workers=2)
        print("[OK] Downloader criado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao importar/criar downloader: {e}")
        return False

def main():
    """Função principal de teste"""
    print("=" * 60)
    print("TESTE DA VERSÃO GUI - YUPOO DOWNLOADER")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Arquivos", test_files),
        ("Importação da GUI", test_gui_import),
        ("Importação do Downloader", test_downloader_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("RESULTADOS DOS TESTES")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "[OK] PASSOU" if result else "[ERRO] FALHOU"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("TODOS OS TESTES PASSARAM!")
        print("A GUI está pronta para uso e compilação.")
        print("\nPróximos passos:")
        print("1. Teste a GUI: python yupoo_gui.py")
        print("2. Compile o executável: python build_executable.py")
    else:
        print("ALGUNS TESTES FALHARAM!")
        print("Corrija os problemas antes de continuar.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
