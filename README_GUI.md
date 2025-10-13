# Yupoo Album Downloader 2025 - Versão GUI

Uma interface gráfica intuitiva para baixar imagens de álbuns, categorias e collections do Yupoo em alta resolução (4K).

## 🖥️ Interface Gráfica

### Características da GUI:
- **Interface Intuitiva**: Fácil de usar, sem necessidade de linha de comando
- **Log em Tempo Real**: Acompanhe o progresso do download
- **Configurações Flexíveis**: Ajuste threads, modo headless e pasta de destino
- **Validação de Entrada**: Verifica URLs e configurações automaticamente
- **Executável Standalone**: Não precisa instalar Python

## 🚀 Como Usar

### 1. Testando a Versão GUI (Antes de Compilar)

```bash
# Instalar dependências
pip install -r requirements_gui.txt

# Executar a GUI
python yupoo_gui.py
```

### 2. Compilando o Executável

```bash
# Executar o compilador
python build_executable.py
```

O executável será criado como `YupooDownloader.exe` (50-80 MB).

## 📋 Guia de Uso da Interface

### 1. **URL**
- Cole a URL do álbum, categoria ou collection do Yupoo
- Exemplos:
  - Álbum: `https://nfl-world.x.yupoo.com/albums/100300873?uid=1`
  - Categoria: `https://minkang.x.yupoo.com/categories/2890904`
  - Collection: `https://exemplo.x.yupoo.com/collections/123456`

### 2. **Configurações**
- **Threads**: Número de downloads paralelos (1-8)
  - Recomendado: 4-6 threads
  - CPU limitada: 2-3 threads
  - CPU potente: 6-8 threads
- **Modo Headless**: 
  - ✅ Marcado: Mais rápido, sem interface do navegador
  - ❌ Desmarcado: Mostra o navegador (útil para debug)
- **Pasta de Destino**: Onde salvar as imagens

### 3. **Botões**
- **Iniciar Download**: Começa o processo
- **Parar**: Interrompe o download (limitado)
- **Limpar Log**: Limpa o log de execução

### 4. **Log de Execução**
- Mostra o progresso em tempo real
- Timestamps para cada ação
- Níveis de log: INFO, SUCCESS, ERROR, WARNING

## 🎯 Exemplos de Uso

### Download de Álbum Individual
1. Cole a URL do álbum
2. Configure 4 threads
3. Marque "Modo Headless"
4. Clique "Iniciar Download"

### Download de Categoria Completa
1. Cole a URL da categoria
2. Configure 6-8 threads (para acelerar)
3. Marque "Modo Headless"
4. Clique "Iniciar Download"

### Debug/Teste
1. Cole uma URL pequena
2. Configure 2 threads
3. Desmarque "Modo Headless" (para ver o navegador)
4. Clique "Iniciar Download"

## 📁 Estrutura de Saída

O programa cria automaticamente pastas organizadas:

```
Pasta de Destino/
├── yupoo_nfl-world_album_100300873_uid_1/
│   ├── image_0001_id_85992691.png
│   ├── image_0002_id_85992690.png
│   └── ...
├── yupoo_minkang_category_2890904/
│   ├── image_0001_id_74156148.png
│   ├── image_0002_id_74156147.png
│   └── ...
└── yupoo_exemplo_collection_123456/
    ├── image_0001_id_12345678.png
    ├── image_0002_id_87654321.png
    └── ...
```

## ⚡ Performance

- **Taxa de Download**: 5-15 imagens/minuto
- **Resolução**: 4K (3840x2160)
- **Threads Recomendadas**: 4-6
- **Tamanho do Executável**: 50-80 MB

## 🔧 Requisitos do Sistema

### Para o Executável:
- Windows 10 ou superior
- Chrome/Chromium instalado
- 4 GB RAM mínimo
- 1 GB espaço livre

### Para Desenvolvimento:
- Python 3.7+
- Chrome/Chromium
- Dependências em `requirements_gui.txt`

## 🐛 Solução de Problemas

### Erro: "ChromeDriver não encontrado"
- Instale o Chrome ou Chromium
- O webdriver-manager baixa automaticamente

### Erro: "URL inválida"
- Verifique se é um link de álbum, categoria ou collection
- URLs de páginas individuais não funcionam

### Download muito lento
- Aumente o número de threads
- Verifique sua conexão com a internet
- Use modo headless

### Interface não responde
- O download está em andamento
- Aguarde a conclusão ou feche o programa

## 📊 Log de Exemplo

```
[14:30:15] INFO: Detectado: URL de categoria
[14:30:16] INFO: Pasta criada: C:\Downloads\yupoo_minkang_category_2890904
[14:30:17] INFO: Abrindo categoria: https://minkang.x.yupoo.com/categories/2890904
[14:30:20] INFO: Encontrados 114 links de álbuns
[14:30:21] INFO: Total de 114 álbuns únicos encontrados na categoria
[14:30:22] INFO: Processando 114 álbuns da categoria...
[14:30:25] INFO: [Álbum 1/114] Processando: https://minkang.x.yupoo.com/albums/212707253?uid=1
[14:30:26] INFO: Encontrados 7 imagens no álbum
[14:30:28] SUCCESS: ID 74156148 salvo: image_0001_id_74156148.png
[14:30:29] SUCCESS: ID 74156147 salvo: image_0002_id_74156147.png
[14:30:30] INFO: Álbum 1 concluído: 7 sucessos, 0 falhas
...
[15:15:45] SUCCESS: Download da categoria concluído em 45.2 minutos!
[15:15:46] SUCCESS: Total de sucessos: 684 imagens
[15:15:47] INFO: Total de falhas: 12 imagens
[15:15:48] SUCCESS: Taxa media: 15.4 imagens/minuto
```

## 🎨 Capturas de Tela

A interface inclui:
- Campo de URL com validação
- Configurações ajustáveis
- Log em tempo real
- Barra de status
- Botões intuitivos

## 🔄 Atualizações

Para atualizar o executável:
1. Baixe a nova versão do código
2. Execute `python build_executable.py`
3. Substitua o executável antigo

## ⚠️ Aviso Legal

Este software é apenas para fins educacionais. Respeite os termos de uso do Yupoo e os direitos autorais das imagens. Use por sua própria conta e risco.
