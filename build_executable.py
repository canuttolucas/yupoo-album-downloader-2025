#!/usr/bin/env python3
"""
Script para compilar o Yupoo Downloader em executável
"""

import os
import sys
import subprocess
import shutil

def check_requirements():
    """Verifica se os requisitos estão instalados"""
    try:
        import PyInstaller
        print("✓ PyInstaller encontrado")
    except ImportError:
        print("✗ PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller instalado")

def build_executable():
    """Compila o executável"""
    print("Iniciando compilação do executável...")
    
    # Importar configurações
    try:
        from build_config import get_pyinstaller_command
        cmd = get_pyinstaller_command()
        print(f"Comando: {' '.join(cmd)}")
    except ImportError:
        # Fallback para comando básico
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=YupooDownloader",
            "--add-data=yupoo_parallel_downloader.py;.",
            "--hidden-import=selenium",
            "--hidden-import=webdriver_manager",
            "--hidden-import=PIL",
            "--hidden-import=requests",
            "--hidden-import=tkinter",
            "--clean",
            "yupoo_gui.py"
        ]
        
        # Adicionar ícone se existir
        if os.path.exists("icon.ico"):
            cmd.insert(-1, "--icon=icon.ico")
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ Compilação concluída com sucesso!")
        print("✓ Executável criado em: dist/YupooDownloader.exe")
        
        # Copiar para pasta raiz
        if os.path.exists("dist/YupooDownloader.exe"):
            shutil.copy2("dist/YupooDownloader.exe", "YupooDownloader.exe")
            print("✓ Executável copiado para pasta raiz")
            
            # Mostrar tamanho do arquivo
            size_mb = os.path.getsize("YupooDownloader.exe") / (1024 * 1024)
            print(f"✓ Tamanho do executável: {size_mb:.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro durante a compilação: {e}")
        return False
    
    return True

def cleanup():
    """Limpa arquivos temporários"""
    print("Limpando arquivos temporários...")
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Removido: {dir_name}")
    
    # Remover arquivos .spec
    for file in os.listdir("."):
        if file.endswith(".spec"):
            os.remove(file)
            print(f"✓ Removido: {file}")

def main():
    """Função principal"""
    print("=" * 60)
    print("YUPOO DOWNLOADER - COMPILADOR DE EXECUTÁVEL")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("yupoo_gui.py"):
        print("✗ Erro: yupoo_gui.py não encontrado!")
        print("Execute este script no diretório do projeto.")
        return
    
    # Verificar requisitos
    check_requirements()
    
    # Compilar
    if build_executable():
        print("\n" + "=" * 60)
        print("COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("Executável criado: YupooDownloader.exe")
        print("Tamanho aproximado: 50-80 MB")
        print("Requisitos: Windows 10+ com Chrome/Chromium instalado")
        print("=" * 60)
        
        # Perguntar se quer limpar
        response = input("\nDeseja limpar arquivos temporários? (s/n): ").lower()
        if response in ['s', 'sim', 'y', 'yes']:
            cleanup()
    else:
        print("\n✗ Compilação falhou!")

if __name__ == "__main__":
    main()
