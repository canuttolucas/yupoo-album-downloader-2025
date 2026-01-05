# Yupoo Album Downloader 2025 - Modern Edition

Downloader profissional, paralelo e otimizado para baixar imagens do Yupoo em alta resolução (4K), com interface gráfica (GUI) e funcionalidades avançadas de detecção.

## 🚀 Principais Atributos

- **Interface Gráfica (GUI)**: Interface intuitiva em Python/CustomTkinter (Dark Mode).
- **Download Paralelo**: Múltiplas imagens simultâneas com `ThreadPoolExecutor`.
- **Alta Resolução**: Captura automática em 4K (3840x2160) via Selenium.
- **Scroll de Teclado (Focado)**: Técnica de simulação de clique + teclado para carregar 100% dos álbuns (Lazy Loading).
- **Extração Inteligente de Nomes**: Captura automática dos nomes reais dos álbuns diretamente da categoria.
- **Botão de Parar (Nuclear)**: Encerramento imediato do processo e de todas as janelas do navegador.
- **Paginação Avançada**: Suporte completo para navegar em múltiplas páginas de categorias.

## 📋 Requisitos do Sistema

- **OS**: Windows 10/11.
- **Browser**: Google Chrome instalado.
- **Python**: 3.8+ (para execução via script).

## 🛠️ Instalação e Uso

1. Clone o repositório:
   ```bash
   git clone https://github.com/felcoslop/yupoo-album-downloader-2025.git
   cd yupoo-album-downloader-2025
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o programa:
   ```bash
   python yupoo_gui.py
   ```

### 🎯 Guia de Uso

1. **URL**: Insira o link do álbum, categoria ou coleção.
2. **Scroll Automático**: O programa agora aguarda 5s e realiza um scroll de 10s simulando o teclado para garantir que todos os álbuns sejam carregados.
3. **Parar**: Clique em "PARAR DOWNLOAD" ou feche a janela para encerrar todos os processos instantaneamente.

## 📁 Saída
Os arquivos são salvos na pasta raiz do projeto, organizados por:
- `[NOME_DO_ALBUM]_CAPA_HQ.png` (Para downloads de capas).
- Pastas individuais por álbum (Para downloads completos).

## 🔧 Desenvolvido para 2026
Estabilidade aprimorada contra bloqueios e mudanças de layout do Yupoo.

---
*Atualizado em Janeiro de 2026.*
