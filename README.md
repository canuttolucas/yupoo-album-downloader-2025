# Yupoo Album Downloader 2025

Um downloader paralelo e otimizado para baixar imagens de álbuns do Yupoo em alta resolução (4K).

## 🚀 Características

- **Download Paralelo**: Processa múltiplas imagens simultaneamente usando ThreadPoolExecutor
- **Alta Resolução**: Captura imagens em resolução 4K (3840x2160)
- **Modo Headless**: Executa em segundo plano sem interface gráfica
- **Pasta Automática**: Cria pasta específica para cada álbum baseada no ID
- **Interface Flexível**: Suporte a argumentos de linha de comando e modo interativo
- **Logs Detalhados**: Acompanhamento em tempo real do progresso

## 📋 Requisitos

- Python 3.7+
- Chrome/Chromium instalado
- ChromeDriver (gerenciado automaticamente pelo webdriver-manager)

## 🛠️ Instalação

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
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1"
```

## 🎯 Uso

### Modo Interativo (Recomendado para Iniciantes)
```bash
python yupoo_parallel_downloader.py --interactive
```
O programa irá solicitar:
- URL do álbum, categoria ou collection
- Número de threads paralelas (1-8)
- Modo headless (com ou sem interface gráfica)

### Linha de Comando (Para Usuários Avançados)

#### Download de Álbum Individual
```bash
# Álbum básico
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1"

# Com configurações personalizadas
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1" --threads 6 --no-headless
```

#### Download de Categoria Completa
```bash
# Baixa TODOS os álbuns de uma categoria
python yupoo_parallel_downloader.py --url "https://minkang.x.yupoo.com/categories/2890904"

# Com mais threads para acelerar
python yupoo_parallel_downloader.py --url "https://minkang.x.yupoo.com/categories/2890904" --threads 8
```

#### Download de Collection Completa
```bash
# Baixa TODOS os álbuns de uma collection
python yupoo_parallel_downloader.py --url "https://exemplo.x.yupoo.com/collections/123456"

# Com interface gráfica para acompanhar
python yupoo_parallel_downloader.py --url "https://exemplo.x.yupoo.com/collections/123456" --no-headless
```

#### Exemplos com Diferentes Subdomínios
```bash
# Qualquer álbum do Yupoo
python yupoo_parallel_downloader.py --url "https://fashion-store.x.yupoo.com/albums/123456?uid=1"
python yupoo_parallel_downloader.py --url "https://sports-shop.x.yupoo.com/albums/789012?uid=2"

# Qualquer categoria do Yupoo
python yupoo_parallel_downloader.py --url "https://fashion-store.x.yupoo.com/categories/123456"
python yupoo_parallel_downloader.py --url "https://sports-shop.x.yupoo.com/categories/789012"

# Qualquer collection do Yupoo
python yupoo_parallel_downloader.py --url "https://fashion-store.x.yupoo.com/collections/123456"
python yupoo_parallel_downloader.py --url "https://sports-shop.x.yupoo.com/collections/789012"
```

### Opções Disponíveis

- `--url, -u`: URL do álbum, categoria ou collection Yupoo (obrigatório)
- `--threads, -t`: Número de threads paralelas (1-8, padrão: 4)
- `--no-headless`: Executar com interface gráfica
- `--interactive, -i`: Modo interativo
- `--help, -h`: Mostrar ajuda

## 📁 Estrutura de Saída

O programa cria automaticamente uma pasta para cada álbum, categoria ou collection com nome descritivo:

### Para Álbuns:
```
yupoo_[SUBDOMAIN]_album_[ID_DO_ALBUM]_uid_[UID]/
├── image_0001_id_[DATA_ID].png
├── image_0002_id_[DATA_ID].png
├── image_0003_id_[DATA_ID].png
└── ...

# Exemplos:
yupoo_nfl-world_album_100300873_uid_1/
yupoo_fashion-store_album_123456_uid_2/
```

### Para Categorias:
```
yupoo_[SUBDOMAIN]_category_[ID_DA_CATEGORIA]/
├── image_0001_id_[DATA_ID].png
├── image_0002_id_[DATA_ID].png
├── image_0003_id_[DATA_ID].png
└── ...

# Exemplo:
yupoo_minkang_category_2890904/
```

### Para Collections:
```
yupoo_[SUBDOMAIN]_collection_[ID_DA_COLLECTION]/
├── image_0001_id_[DATA_ID].png
├── image_0002_id_[DATA_ID].png
├── image_0003_id_[DATA_ID].png
└── ...

# Exemplo:
yupoo_exemplo_collection_123456/
```

## ⚡ Performance

- **Taxa de Download**: ~5-10 imagens/minuto (dependendo da conexão)
- **Threads Recomendadas**: 4-6 threads para melhor performance
- **Resolução**: 4K (3840x2160) para máxima qualidade

## 🔧 Configurações Avançadas

### Ajustando Threads
- **CPU Limitada**: Use 2-3 threads
- **CPU Potente**: Use 6-8 threads
- **Conexão Lenta**: Use 2-4 threads
- **Categorias/Collections Grandes**: Use 6-8 threads para acelerar

### Modo Headless vs Interface
- **Headless (padrão)**: Mais rápido, sem interface gráfica
- **Com Interface**: Útil para debug, mais lento

## 💡 Dicas e Truques

### Para Downloads Grandes
```bash
# Use mais threads para categorias/collections grandes
python yupoo_parallel_downloader.py --url "https://minkang.x.yupoo.com/categories/2890904" --threads 8

# Use modo headless para máxima velocidade
python yupoo_parallel_downloader.py --url "https://minkang.x.yupoo.com/categories/2890904" --threads 8
```

### Para Debug e Testes
```bash
# Use interface gráfica para acompanhar o processo
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1" --no-headless

# Use menos threads para debug
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1" --threads 2 --no-headless
```

### URLs Válidas
- ✅ **Álbuns**: `https://subdomain.x.yupoo.com/albums/123456?uid=1`
- ✅ **Categorias**: `https://subdomain.x.yupoo.com/categories/123456`
- ✅ **Collections**: `https://subdomain.x.yupoo.com/collections/123456`
- ❌ **URLs inválidas**: Páginas individuais, perfis, etc.

## 🐛 Solução de Problemas

### Erro de Timeout
- Reduza o número de threads
- Verifique sua conexão com a internet

### ChromeDriver não encontrado
- O webdriver-manager baixa automaticamente
- Certifique-se de ter Chrome/Chromium instalado

### Erro 567 Server Error
- Algumas imagens podem estar indisponíveis
- O programa continua com as demais imagens

## 📊 Exemplos de Saída

### Download de Álbum Individual
```
================================================================================
YUPOO PARALLEL DOWNLOADER - Captura Paralela em 4K
Threads paralelas: 4
================================================================================
Detectado: URL de álbum
Pasta criada: C:\Users\usuario\Downloads\yupoo_downloader\yupoo_nfl-world_album_100300873_uid_1
Abrindo álbum: https://nfl-world.x.yupoo.com/albums/100300873?uid=1
Total de 120 data-ids únicos encontrados

Iniciando captura paralela de 120 imagens...
================================================================================
[001/120] Capturando ID 85992691...
[002/120] Capturando ID 85992690...
  [OK] ID 85992691 salvo: image_0001_id_85992691.png
  [OK] ID 85992690 salvo: image_0002_id_85992690.png
  Progresso: 5/120 | Taxa: 12.5 img/min | ETA: 9.2 min
...
================================================================================
Captura paralela concluida em 8.5 minutos!
[OK] Sucesso: 117 imagens
[ERRO] Falhas: 3 imagens
Taxa media: 13.8 imagens/minuto
Imagens salvas em: C:\Users\usuario\Downloads\yupoo_downloader\yupoo_nfl-world_album_100300873_uid_1
================================================================================
```

### Download de Categoria Completa
```
================================================================================
YUPOO PARALLEL DOWNLOADER - Download de Categoria
Threads paralelas: 4
================================================================================
Detectado: URL de categoria
Pasta criada: C:\Users\usuario\Downloads\yupoo_downloader\yupoo_minkang_category_2890904
Abrindo categoria: https://minkang.x.yupoo.com/categories/2890904
Encontrados 114 links de álbuns
Total de 114 álbuns únicos encontrados na categoria

Processando 114 álbuns da categoria...
================================================================================
[Álbum 1/114] Processando: https://minkang.x.yupoo.com/albums/212707253?uid=1&isSubCate=false&referrercate=2890904
  Encontrados 7 imagens no álbum
  [OK] ID 74156148 salvo: image_0001_id_74156148.png
  [OK] ID 74156147 salvo: image_0002_id_74156147.png
  Álbum 1 concluído: 7 sucessos, 0 falhas

[Álbum 2/114] Processando: https://minkang.x.yupoo.com/albums/212707254?uid=1&isSubCate=false&referrercate=2890904
  Encontrados 6 imagens no álbum
  [OK] ID 74156146 salvo: image_0008_id_74156146.png
  [OK] ID 74156145 salvo: image_0009_id_74156145.png
  Álbum 2 concluído: 6 sucessos, 0 falhas
...
================================================================================
Download da categoria concluído em 45.2 minutos!
[OK] Total de sucessos: 684 imagens
[ERRO] Total de falhas: 12 imagens
Taxa media: 15.4 imagens/minuto
Imagens salvas em: C:\Users\usuario\Downloads\yupoo_downloader\yupoo_minkang_category_2890904
================================================================================
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## ⚠️ Aviso Legal

Este software é apenas para fins educacionais. Respeite os termos de uso do Yupoo e os direitos autorais das imagens. Use por sua própria conta e risco.

## 🔗 Links Úteis

- [Selenium WebDriver](https://selenium-python.readthedocs.io/)
- [ChromeDriver](https://chromedriver.chromium.org/)
- [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html)
