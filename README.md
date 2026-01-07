# Yupoo Album Downloader 2025

Sistema completo para download e organização de álbuns do Yupoo com interface gráfica moderna.

## Funcionalidades

- Download de álbuns individuais ou coleções completas
- Download paralelo com até 10 threads simultâneas
- Organização automática por time, liga, temporada e tipo de produto
- Integração com OpenAI para classificação inteligente
- Interface gráfica moderna com tema escuro
- Suporte a múltiplas URLs em batch
- Extração automática de temporadas (formatos: 25/26, 24-25, 2024-2025)

## Requisitos

- Python 3.8 ou superior
- Google Chrome instalado
- Conexão com internet

## Instalação

### 1. Clone ou baixe o repositório

```bash
git clone https://github.com/seu-usuario/yupoo-album-downloader.git
cd yupoo-album-downloader
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

As bibliotecas instaladas serão:
- `selenium` - Automação do navegador
- `Pillow` - Processamento de imagens
- `webdriver-manager` - Gerenciamento automático do ChromeDriver
- `customtkinter` - Interface gráfica moderna
- `packaging` - Gerenciamento de versões

### 3. Execute o programa

```bash
python yupoo_gui.py
```

## Como Usar

### Download Básico

1. Cole a URL do álbum ou coleção Yupoo no campo de texto
2. Selecione a pasta de destino
3. Clique em "INICIAR DOWNLOAD"

### Download de Coleções

Para URLs de coleções (`/collections/` ou `/categories/`):

1. Escolha o modo:
   - **Só Capas (HQ)**: Baixa apenas a capa de cada álbum em alta qualidade
   - **Álbuns Completos**: Baixa todas as fotos de todos os álbuns

2. Selecione a paginação:
   - **Primeira**: Apenas a primeira página
   - **Todas**: Todas as páginas da coleção
   - **Intervalo**: Páginas específicas (ex: 1 a 5)

### Organização Automática

1. Clique em "Organizar Fotos" na barra lateral
2. Selecione a pasta de origem (onde estão as fotos baixadas)
3. Selecione a pasta de destino (onde será criada a estrutura organizada)
4. (Opcional) Insira sua chave da API OpenAI para melhor precisão
5. Clique em "Organizar"

As fotos serão organizadas automaticamente em pastas por:
- Time/Clube
- Liga/Competição
- Temporada (25-26, 24-25, etc.)
- Tipo de produto (PLAYER, MANGA LONGA, CORTA-VENTO, RETRO, etc.)

### Opções Avançadas

- **Threads**: Controle o número de downloads paralelos (1-10)
- **Modo Headless**: Esconde o navegador durante o download
- **Batch**: Cole múltiplas URLs (uma por linha, máximo 20)

## Estrutura de Pastas Organizadas

Exemplo de estrutura criada pelo organizador:

```
Destino/
├── RETRO/
│   ├── Barcelona RETRO Home 98-99.png
│   └── Real Madrid RETRO Away 02-03.png
├── PLAYER/
│   ├── Manchester United PLAYER Home 25-26.png
│   └── Liverpool PLAYER Away 24-25.png
├── MANGA LONGA/
│   └── Arsenal MANGA LONGA Home 25-26.png
├── CORTA-VENTO/
│   └── PSG CORTA-VENTO 25-26.png
└── SHORTS/
    └── Barcelona SHORTS Home 25-26.png
```

## Tipos de Produto Suportados

- PLAYER - Versão de jogador
- MANGA LONGA - Camisas de manga longa
- CORTA-VENTO - Jaquetas corta-vento
- RETRO - Camisas retrô/vintage
- WOMEN - Versão feminina
- KIDS - Versão infantil
- BABY - Versão bebê
- SHORTS - Calções
- POLOS - Camisas polo
- SUITS - Ternos/apresentação
- TRACKSUIT - Agasalhos
- GOALKEEPER - Goleiro

## Formatos de Temporada Reconhecidos

O sistema reconhece automaticamente os seguintes formatos:
- `25/26` → convertido para `25-26`
- `24-25` → mantido como `24-25`
- `2024-2025` → convertido para `24-25`
- `2026` → convertido para `26-27`

## Integração com OpenAI (Opcional)

Para melhorar a precisão da classificação automática:

1. Obtenha uma chave API em: https://platform.openai.com/api-keys
2. Cole a chave no campo "OpenAI API Key"
3. O sistema usará GPT-4o-mini para identificar times e categorias desconhecidas

## Solução de Problemas

### Erro: "ChromeDriver não encontrado"
- O `webdriver-manager` baixa automaticamente o ChromeDriver na primeira execução
- Certifique-se de ter conexão com internet

### Erro: "Timeout receiving message from renderer"
- Reduza o número de threads
- Verifique sua conexão com internet
- Tente novamente (pode ser instabilidade temporária)

### Temporada não aparece no nome do arquivo
- Verifique se o título original do álbum contém a temporada
- O sistema extrai a temporada do título original antes de qualquer processamento

### Fotos não são organizadas corretamente
- Use a chave da API OpenAI para melhor precisão
- Verifique se os nomes dos arquivos contêm informações do time/liga
- Confira os logs para ver como cada arquivo foi classificado

## Arquivos do Projeto

### Arquivos Principais
- `yupoo_gui.py` - Interface gráfica principal
- `yupoo_advanced_downloader.py` - Motor de download avançado
- `photo_organizer.py` - Sistema de organização e classificação
- `requirements.txt` - Dependências do projeto

### Arquivos de Dados
- `data/clubs.json` - Base de dados de clubes e ligas
- `data/nations.json` - Base de dados de seleções
- `data/keywords.json` - Palavras-chave para classificação

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Adicionar novos times/ligas aos arquivos JSON
- Melhorar a documentação

## Licença

Este projeto é fornecido "como está", sem garantias de qualquer tipo.

## Suporte

Para problemas ou dúvidas, abra uma issue no GitHub.
