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

### Modo Interativo
```bash
python yupoo_parallel_downloader.py --interactive
```

### Linha de Comando
```bash
# Download de álbum individual
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1"

# Download de categoria completa (todos os álbuns)
python yupoo_parallel_downloader.py --url "https://minkang.x.yupoo.com/categories/2890904"

# Download de collection completa (todos os álbuns)
python yupoo_parallel_downloader.py --url "https://exemplo.x.yupoo.com/collections/123456"

# Com configurações personalizadas
python yupoo_parallel_downloader.py --url "https://nfl-world.x.yupoo.com/albums/100300873?uid=1" --threads 6 --no-headless

# Qualquer álbum, categoria ou collection do Yupoo
python yupoo_parallel_downloader.py --url "https://qualquer-subdomain.x.yupoo.com/albums/123456?uid=1"
python yupoo_parallel_downloader.py --url "https://qualquer-subdomain.x.yupoo.com/categories/123456"
python yupoo_parallel_downloader.py --url "https://qualquer-subdomain.x.yupoo.com/collections/123456"
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

### Modo Headless vs Interface
- **Headless (padrão)**: Mais rápido, sem interface gráfica
- **Com Interface**: Útil para debug, mais lento

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

## 📊 Exemplo de Saída

```
================================================================================
YUPOO PARALLEL DOWNLOADER - Captura Paralela em 4K
Threads paralelas: 4
================================================================================
Pasta criada: C:\Users\usuario\Downloads\yupoo_downloader\yupoo_album_100300873
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
Imagens salvas em: C:\Users\usuario\Downloads\yupoo_downloader\yupoo_album_100300873
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
