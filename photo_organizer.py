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
        """Extrai temporada válida do texto (10-11 até 25-26)"""
        pattern = r'\b(1[0-9]|2[0-5])[-/](1[0-9]|2[0-6])\b'
        match = re.search(pattern, text)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            if 10 <= start <= 25 and end == start + 1:
                return f"{start:02d}-{end:02d}"
        return None

    def _extract_product_type(self, text: str) -> Optional[str]:
        """Identifica o tipo de produto (retro, women, kids, etc.)"""
        normalized = self._normalize(text)
        for product_key, product_data in self.keywords_data.get('product_types', {}).items():
            for keyword in product_data.get('keywords', []):
                if keyword in normalized:
                    return product_data['folder']
        return None

    def _extract_version(self, text: str) -> str:
        """Extrai a versão (Home, Away, Third, etc.)"""
        normalized = self._normalize(text)
        for version_key, version_data in self.keywords_data.get('version_mapping', {}).items():
            for keyword in version_data.get('keywords', []):
                if keyword in normalized:
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
            'team_type': None,  # CLUB ou NATION
            'league_or_continent': None,
            'season': None,
            'version': None,
            'product_type': None,
            'target_folder': None,
            'target_filename': None,
            'confidence': 'LOW'
        }
        
        # 1. Encontrar o time
        team_info = self._find_team(filename)
        if team_info:
            result['team_name'] = team_info[0]
            result['league_or_continent'] = team_info[1]
            result['team_type'] = team_info[2]
            result['confidence'] = 'HIGH'
        
        # 2. Extrair temporada
        result['season'] = self._extract_season(filename)
        
        # 3. Extrair versão
        result['version'] = self._extract_version(filename)
        
        # 4. Extrair tipo de produto
        result['product_type'] = self._extract_product_type(filename)
        
        # 5. Determinar pasta de destino (REGRA DE PRIORIDADE)
        if result['team_name']:
            if result['team_type'] == 'CLUB':
                base_path = f"FUTEBOL/CLUBES/{self._sanitize_filename(result['league_or_continent'])}/{self._sanitize_filename(result['team_name'])}"
            else:
                base_path = f"FUTEBOL/SELECOES/{self._sanitize_filename(result['league_or_continent'])}/{self._sanitize_filename(result['team_name'])}"
            
            # Prioridade: Temporada > Tipo de Produto > INDISPONIVEL
            if result['season']:
                result['target_folder'] = f"{base_path}/{result['season']}"
            elif result['product_type']:
                result['target_folder'] = f"{base_path}/{result['product_type']}"
            else:
                result['target_folder'] = f"{base_path}/{self.keywords_data.get('folder_unavailable', 'INDISPONIVEL')}"
        else:
            result['target_folder'] = f"FUTEBOL/{self.keywords_data.get('folder_unavailable', 'INDISPONIVEL')}"
            result['confidence'] = 'NONE'
        
        # 6. Gerar nome de arquivo padronizado
        name_parts = []
        if result['team_name']:
            name_parts.append(self._sanitize_filename(result['team_name']))
        if result['version']:
            name_parts.append(result['version'])
        if result['season']:
            name_parts.append(result['season'])
        
        if name_parts:
            base_name = ' '.join(name_parts)
        else:
            base_name = os.path.splitext(filename)[0]
        
        ext = os.path.splitext(filename)[1]
        result['target_filename'] = f"{base_name}{ext}"
        
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
                target_dir = os.path.join(destination_folder, classification['target_folder'])
                target_path = os.path.join(target_dir, classification['target_filename'])
                
                # Evitar sobrescrição
                target_path = self._get_unique_path(target_path)
                
                self.log(f"[{classification['confidence']}] {filename} -> {os.path.relpath(target_path, destination_folder)}")
                
                if not dry_run:
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.copy2(source_path, target_path)
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
    
    # Testes de classificação
    test_files = [
        "Barcelona Home 25-26.jpg",
        "juve away kit 24-25.png",
        "brazil copa 2022.jpg",
        "manchester united retro 98-99.jpg",
        "Flamengo Women 24-25.png",
        "psg kids away.jpg",
        "real madrid goalkeeper.png",
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
