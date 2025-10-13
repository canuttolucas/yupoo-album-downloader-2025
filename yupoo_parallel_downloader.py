import os
import time
import re
import sys
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class YupooParallelDownloader:
    def __init__(self, headless=True, max_workers=4):
        """
        Inicializa o downloader do Yupoo com paralelismo
        
        Args:
            headless: Se True, executa sem interface gráfica
            max_workers: Número máximo de threads paralelas
        """
        self.headless = headless
        self.max_workers = max_workers
        self.output_dir = None
        self.data_ids = []
        self.lock = threading.Lock()
    
    def create_album_folder(self, album_url):
        """
        Cria uma pasta específica para o álbum baseada na URL
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            Caminho da pasta criada
        """
        # Extrai informações da URL para criar nome da pasta
        # Formato: https://[subdomain].x.yupoo.com/albums/[album_id]?uid=[uid]
        url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/(\d+)(?:\?uid=(\d+))?', album_url)
        
        if url_parts:
            subdomain = url_parts.group(1)
            album_id = url_parts.group(2)
            uid = url_parts.group(3) if url_parts.group(3) else "unknown"
            
            # Cria nome da pasta mais descritivo
            folder_name = f"yupoo_{subdomain}_album_{album_id}_uid_{uid}"
        else:
            # Fallback para URLs que não seguem o padrão esperado
            album_id_match = re.search(r'/albums/(\d+)', album_url)
            if album_id_match:
                album_id = album_id_match.group(1)
                folder_name = f"yupoo_album_{album_id}"
            else:
                # Se não encontrar o ID, usa timestamp
                album_id = str(int(time.time()))
                folder_name = f"yupoo_album_{album_id}"
        
        self.output_dir = folder_name
        
        # Cria o diretório se não existir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            print(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
        return self.output_dir
    
    def create_category_folder(self, category_url):
        """
        Cria uma pasta específica para a categoria baseada na URL
        
        Args:
            category_url: URL da categoria Yupoo
            
        Returns:
            Caminho da pasta criada
        """
        # Extrai informações da URL para criar nome da pasta
        # Formato: https://[subdomain].x.yupoo.com/categories/[category_id]
        url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/categories/(\d+)', category_url)
        
        if url_parts:
            subdomain = url_parts.group(1)
            category_id = url_parts.group(2)
            
            # Cria nome da pasta mais descritivo
            folder_name = f"yupoo_{subdomain}_category_{category_id}"
        else:
            # Fallback para URLs que não seguem o padrão esperado
            category_id_match = re.search(r'/categories/(\d+)', category_url)
            if category_id_match:
                category_id = category_id_match.group(1)
                folder_name = f"yupoo_category_{category_id}"
            else:
                # Se não encontrar o ID, usa timestamp
                category_id = str(int(time.time()))
                folder_name = f"yupoo_category_{category_id}"
        
        self.output_dir = folder_name
        
        # Cria o diretório se não existir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            print(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
        return self.output_dir
    
    def create_collection_folder(self, collection_url):
        """
        Cria uma pasta específica para a collection baseada na URL
        
        Args:
            collection_url: URL da collection Yupoo
            
        Returns:
            Caminho da pasta criada
        """
        # Extrai informações da URL para criar nome da pasta
        # Formato: https://[subdomain].x.yupoo.com/collections/[collection_id]
        url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/collections/(\d+)', collection_url)
        
        if url_parts:
            subdomain = url_parts.group(1)
            collection_id = url_parts.group(2)
            
            # Cria nome da pasta mais descritivo
            folder_name = f"yupoo_{subdomain}_collection_{collection_id}"
        else:
            # Fallback para URLs que não seguem o padrão esperado
            collection_id_match = re.search(r'/collections/(\d+)', collection_url)
            if collection_id_match:
                collection_id = collection_id_match.group(1)
                folder_name = f"yupoo_collection_{collection_id}"
            else:
                # Se não encontrar o ID, usa timestamp
                collection_id = str(int(time.time()))
                folder_name = f"yupoo_collection_{collection_id}"
        
        self.output_dir = folder_name
        
        # Cria o diretório se não existir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            print(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
        return self.output_dir
    
    def create_driver(self):
        """Cria uma nova instância do ChromeDriver"""
        chrome_options = Options()
        
        # Configurações para renderização em 4K
        chrome_options.add_argument('--window-size=3840,2160')
        chrome_options.add_argument('--start-maximized')
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Configurações adicionais para melhor performance
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument('--disable-images')  # Desabilita carregamento de imagens desnecessárias
        chrome_options.add_argument('--disable-javascript')  # Desabilita JS desnecessário
        
        # User agent para evitar bloqueios
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(3840, 2160)
        return driver
    
    def get_data_ids(self, album_url):
        """
        Captura todos os data-id das miniaturas do álbum
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            Lista de data-ids das imagens
        """
        print(f"Abrindo álbum: {album_url}")
        driver = self.create_driver()
        
        try:
            driver.get(album_url)
            time.sleep(3)
            
            # Scroll para carregar todas as imagens
            self.scroll_to_load_all(driver)
            
            print("Procurando data-ids das miniaturas...")
            
            # Encontra todos os elementos que contêm data-id
            elements_with_data_id = driver.find_elements(By.XPATH, "//div[@data-id]")
            print(f"Encontrados {len(elements_with_data_id)} elementos com data-id")
            
            data_ids = []
            for element in elements_with_data_id:
                data_id = element.get_attribute('data-id')
                if data_id and data_id.isdigit():
                    data_ids.append(data_id)
                    print(f"[OK] Data-ID encontrado: {data_id}")
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_data_ids = []
            for data_id in data_ids:
                if data_id not in seen:
                    seen.add(data_id)
                    unique_data_ids.append(data_id)
            
            print(f"\nTotal de {len(unique_data_ids)} data-ids únicos encontrados")
            return unique_data_ids
            
        except Exception as e:
            print(f"Erro ao capturar data-ids: {e}")
            return []
        finally:
            driver.quit()
    
    def scroll_to_load_all(self, driver):
        """Faz scroll na página para carregar todas as imagens"""
        print("Fazendo scroll para carregar todas as imagens...")
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
    
    def get_albums_from_category(self, category_url):
        """
        Obtém todos os álbuns de uma categoria
        
        Args:
            category_url: URL da categoria Yupoo
            
        Returns:
            Lista de URLs dos álbuns
        """
        print(f"Abrindo categoria: {category_url}")
        driver = self.create_driver()
        
        try:
            driver.get(category_url)
            time.sleep(3)
            
            # Scroll para carregar todos os álbuns
            self.scroll_to_load_all(driver)
            
            print("Procurando álbuns na categoria...")
            
            # Encontra todos os links de álbuns
            album_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/albums/')]")
            print(f"Encontrados {len(album_links)} links de álbuns")
            
            album_urls = []
            for link in album_links:
                href = link.get_attribute('href')
                if href and '/albums/' in href:
                    album_urls.append(href)
                    print(f"[OK] Álbum encontrado: {href}")
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_album_urls = []
            for url in album_urls:
                if url not in seen:
                    seen.add(url)
                    unique_album_urls.append(url)
            
            print(f"\nTotal de {len(unique_album_urls)} álbuns únicos encontrados na categoria")
            return unique_album_urls
            
        except Exception as e:
            print(f"Erro ao capturar álbuns da categoria: {e}")
            return []
        finally:
            driver.quit()
    
    def get_albums_from_collection(self, collection_url):
        """
        Obtém todos os álbuns de uma collection
        
        Args:
            collection_url: URL da collection Yupoo
            
        Returns:
            Lista de URLs dos álbuns
        """
        print(f"Abrindo collection: {collection_url}")
        driver = self.create_driver()
        
        try:
            driver.get(collection_url)
            time.sleep(3)
            
            # Scroll para carregar todos os álbuns
            self.scroll_to_load_all(driver)
            
            print("Procurando álbuns na collection...")
            
            # Encontra todos os links de álbuns
            album_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/albums/')]")
            print(f"Encontrados {len(album_links)} links de álbuns")
            
            album_urls = []
            for link in album_links:
                href = link.get_attribute('href')
                if href and '/albums/' in href:
                    album_urls.append(href)
                    print(f"[OK] Álbum encontrado: {href}")
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_album_urls = []
            for url in album_urls:
                if url not in seen:
                    seen.add(url)
                    unique_album_urls.append(url)
            
            print(f"\nTotal de {len(unique_album_urls)} álbuns únicos encontrados na collection")
            return unique_album_urls
            
        except Exception as e:
            print(f"Erro ao capturar álbuns da collection: {e}")
            return []
        finally:
            driver.quit()
    
    def capture_single_image(self, data_id, index, base_url):
        """
        Captura uma única imagem (função para thread)
        
        Args:
            data_id: ID da imagem
            index: Índice da imagem
            base_url: URL base do álbum para extrair subdomain e uid
            
        Returns:
            Tupla (success, data_id, filename, error_message)
        """
        driver = None
        try:
            # Cria driver para esta thread
            driver = self.create_driver()
            
            # Extrai subdomain e uid da URL base
            url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/\d+(?:\?uid=(\d+))?', base_url)
            if url_parts:
                subdomain = url_parts.group(1)
                uid = url_parts.group(2) if url_parts.group(2) else "1"
            else:
                # Fallback para URLs que não seguem o padrão
                subdomain = "nfl-world"  # fallback
                uid = "1"
            
            # Constrói a URL da imagem individual dinamicamente
            image_url = f"https://{subdomain}.x.yupoo.com/{data_id}?uid={uid}"
            
            with self.lock:
                print(f"[{index + 1:03d}/{len(self.data_ids)}] Capturando ID {data_id}...")
            
            driver.get(image_url)
            time.sleep(1)  # Reduzido para 1 segundo
            
            # Aguarda o elemento img estar presente
            wait = WebDriverWait(driver, 5)  # Reduzido para 5 segundos
            
            # Procura pelo componente img específico
            img_element = None
            selectors = [
                "//img[contains(@class, 'viewer_img')]",
                "//div[@class='viewer_imgwrap']//img",
                "//div[contains(@class, 'viewer')]//img[not(contains(@class, 'avatar'))]",
                "//img[contains(@src, 'photo.yupoo.com')]"
            ]
            
            for selector in selectors:
                try:
                    img_element = wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if img_element:
                        break
                except:
                    continue
            
            if not img_element:
                return (False, data_id, None, "Elemento img não encontrado")
            
            # Aguarda a imagem carregar
            time.sleep(0.5)  # Reduzido para 0.5 segundos
            
            # Scroll até o elemento
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            
            # Captura screenshot do elemento específico
            screenshot = img_element.screenshot_as_png
            
            # Salva a imagem
            filename = f"image_{index + 1:04d}_id_{data_id}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot)
            
            with self.lock:
                print(f"  [OK] ID {data_id} salvo: {filename}")
            
            return (True, data_id, filename, None)
            
        except Exception as e:
            error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            with self.lock:
                print(f"  [ERRO] ID {data_id} falhou: {error_msg}")
            return (False, data_id, None, error_msg)
        finally:
            if driver:
                driver.quit()
    
    def download_album(self, album_url):
        """
        Processo completo com paralelismo
        
        Args:
            album_url: URL do álbum Yupoo
        """
        print("=" * 80)
        print("YUPOO PARALLEL DOWNLOADER - Captura Paralela em 4K")
        print(f"Threads paralelas: {self.max_workers}")
        print("=" * 80)
        
        # Passo 0: Criar pasta específica para o álbum
        self.create_album_folder(album_url)
        
        # Passo 1: Capturar todos os data-ids das miniaturas
        self.data_ids = self.get_data_ids(album_url)
        
        if not self.data_ids:
            print("Nenhum data-id encontrado no álbum!")
            return
        
        print(f"\nIniciando captura paralela de {len(self.data_ids)} imagens...")
        print("=" * 80)
        
        # Passo 2: Processar imagens em paralelo
        successful = 0
        failed = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete todas as tarefas
            future_to_data_id = {
                executor.submit(self.capture_single_image, data_id, index, album_url): data_id 
                for index, data_id in enumerate(self.data_ids)
            }
            
            # Processa resultados conforme completam
            for future in as_completed(future_to_data_id):
                success, data_id, filename, error = future.result()
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                # Mostra progresso a cada 5 imagens
                if (successful + failed) % 5 == 0:
                    elapsed = time.time() - start_time
                    rate = (successful + failed) / elapsed
                    eta = (len(self.data_ids) - successful - failed) / rate if rate > 0 else 0
                    print(f"  Progresso: {successful + failed}/{len(self.data_ids)} | Taxa: {rate:.1f} img/min | ETA: {eta/60:.1f} min")
        
        elapsed_total = time.time() - start_time
        print("=" * 80)
        print(f"Captura paralela concluida em {elapsed_total/60:.1f} minutos!")
        print(f"[OK] Sucesso: {successful} imagens")
        print(f"[ERRO] Falhas: {failed} imagens")
        print(f"Taxa media: {len(self.data_ids)/elapsed_total*60:.1f} imagens/minuto")
        print(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        print("=" * 80)
    
    def download_category(self, category_url):
        """
        Processo completo para categoria: obtém todos os álbuns e baixa todas as imagens
        
        Args:
            category_url: URL da categoria Yupoo
        """
        print("=" * 80)
        print("YUPOO PARALLEL DOWNLOADER - Download de Categoria")
        print(f"Threads paralelas: {self.max_workers}")
        print("=" * 80)
        
        # Passo 0: Criar pasta específica para a categoria
        self.create_category_folder(category_url)
        
        # Passo 1: Obter todos os álbuns da categoria
        album_urls = self.get_albums_from_category(category_url)
        
        if not album_urls:
            print("Nenhum álbum encontrado na categoria!")
            return
        
        print(f"\nProcessando {len(album_urls)} álbuns da categoria...")
        print("=" * 80)
        
        # Passo 2: Para cada álbum, obter data-ids e baixar imagens
        total_successful = 0
        total_failed = 0
        start_time = time.time()
        
        for album_index, album_url in enumerate(album_urls):
            print(f"\n[Álbum {album_index + 1}/{len(album_urls)}] Processando: {album_url}")
            
            # Obter data-ids do álbum
            data_ids = self.get_data_ids(album_url)
            
            if not data_ids:
                print(f"  Nenhum data-id encontrado no álbum {album_index + 1}")
                continue
            
            print(f"  Encontrados {len(data_ids)} imagens no álbum")
            
            # Baixar imagens do álbum
            successful = 0
            failed = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submete todas as tarefas
                future_to_data_id = {
                    executor.submit(self.capture_single_image, data_id, index, album_url): data_id 
                    for index, data_id in enumerate(data_ids)
                }
                
                # Processa resultados conforme completam
                for future in as_completed(future_to_data_id):
                    success, data_id, filename, error = future.result()
                    
                    if success:
                        successful += 1
                        total_successful += 1
                    else:
                        failed += 1
                        total_failed += 1
            
            print(f"  Álbum {album_index + 1} concluído: {successful} sucessos, {failed} falhas")
        
        elapsed_total = time.time() - start_time
        print("=" * 80)
        print(f"Download da categoria concluído em {elapsed_total/60:.1f} minutos!")
        print(f"[OK] Total de sucessos: {total_successful} imagens")
        print(f"[ERRO] Total de falhas: {total_failed} imagens")
        print(f"Taxa media: {(total_successful + total_failed)/elapsed_total*60:.1f} imagens/minuto")
        print(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        print("=" * 80)
    
    def download_collection(self, collection_url):
        """
        Processo completo para collection: obtém todos os álbuns e baixa todas as imagens
        
        Args:
            collection_url: URL da collection Yupoo
        """
        print("=" * 80)
        print("YUPOO PARALLEL DOWNLOADER - Download de Collection")
        print(f"Threads paralelas: {self.max_workers}")
        print("=" * 80)
        
        # Passo 0: Criar pasta específica para a collection
        self.create_collection_folder(collection_url)
        
        # Passo 1: Obter todos os álbuns da collection
        album_urls = self.get_albums_from_collection(collection_url)
        
        if not album_urls:
            print("Nenhum álbum encontrado na collection!")
            return
        
        print(f"\nProcessando {len(album_urls)} álbuns da collection...")
        print("=" * 80)
        
        # Passo 2: Para cada álbum, obter data-ids e baixar imagens
        total_successful = 0
        total_failed = 0
        start_time = time.time()
        
        for album_index, album_url in enumerate(album_urls):
            print(f"\n[Álbum {album_index + 1}/{len(album_urls)}] Processando: {album_url}")
            
            # Obter data-ids do álbum
            data_ids = self.get_data_ids(album_url)
            
            if not data_ids:
                print(f"  Nenhum data-id encontrado no álbum {album_index + 1}")
                continue
            
            print(f"  Encontrados {len(data_ids)} imagens no álbum")
            
            # Baixar imagens do álbum
            successful = 0
            failed = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submete todas as tarefas
                future_to_data_id = {
                    executor.submit(self.capture_single_image, data_id, index, album_url): data_id 
                    for index, data_id in enumerate(data_ids)
                }
                
                # Processa resultados conforme completam
                for future in as_completed(future_to_data_id):
                    success, data_id, filename, error = future.result()
                    
                    if success:
                        successful += 1
                        total_successful += 1
                    else:
                        failed += 1
                        total_failed += 1
            
            print(f"  Álbum {album_index + 1} concluído: {successful} sucessos, {failed} falhas")
        
        elapsed_total = time.time() - start_time
        print("=" * 80)
        print(f"Download da collection concluído em {elapsed_total/60:.1f} minutos!")
        print(f"[OK] Total de sucessos: {total_successful} imagens")
        print(f"[ERRO] Total de falhas: {total_failed} imagens")
        print(f"Taxa media: {(total_successful + total_failed)/elapsed_total*60:.1f} imagens/minuto")
        print(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        print("=" * 80)


def get_user_input():
    """
    Solicita input do usuário para URL do álbum e configurações
    """
    print("=" * 80)
    print("YUPOO PARALLEL DOWNLOADER - Configuração")
    print("=" * 80)
    
    # Solicita URL do álbum, categoria ou collection
    while True:
        try:
            album_url = input("Digite a URL do álbum, categoria ou collection Yupoo: ").strip()
            if album_url and "yupoo.com" in album_url and ("albums" in album_url or "categories" in album_url or "collections" in album_url):
                break
            print("URL inválida! Certifique-se de que é um link de álbum, categoria ou collection do Yupoo.")
            print("Exemplos:")
            print("  Álbum: https://nfl-world.x.yupoo.com/albums/100300873?uid=1")
            print("  Categoria: https://minkang.x.yupoo.com/categories/2890904")
            print("  Collection: https://exemplo.x.yupoo.com/collections/123456")
        except (EOFError, KeyboardInterrupt):
            print("\nEntrada cancelada. Usando URL padrão...")
            album_url = "https://nfl-world.x.yupoo.com/albums/100300873?uid=1"
            break
    
    # Solicita número de threads
    while True:
        try:
            max_workers = input("Número de threads paralelas (padrão: 4): ").strip()
            if not max_workers:
                max_workers = 4
            else:
                max_workers = int(max_workers)
            if 1 <= max_workers <= 8:
                break
            print("Digite um número entre 1 e 8.")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Usando valor padrão: 4 threads")
            max_workers = 4
            break
    
    # Solicita modo headless
    try:
        headless_input = input("Executar em modo headless (sem interface)? (s/n, padrão: s): ").strip().lower()
        headless = headless_input in ['', 's', 'sim', 'y', 'yes']
    except (EOFError, KeyboardInterrupt):
        print("Usando modo headless padrão")
        headless = True
    
    return album_url, max_workers, headless


def parse_arguments():
    """
    Parse argumentos da linha de comando
    """
    parser = argparse.ArgumentParser(description='Yupoo Parallel Downloader - Baixa imagens de álbuns do Yupoo')
    parser.add_argument('--url', '-u', type=str, help='URL do álbum Yupoo')
    parser.add_argument('--threads', '-t', type=int, default=4, help='Número de threads paralelas (1-8)')
    parser.add_argument('--no-headless', action='store_true', help='Executar com interface gráfica')
    parser.add_argument('--interactive', '-i', action='store_true', help='Modo interativo (solicita input)')
    
    return parser.parse_args()


if __name__ == "__main__":
    try:
        # Parse argumentos da linha de comando
        args = parse_arguments()
        
        if args.interactive or not args.url:
            # Modo interativo
            album_url, max_workers, headless = get_user_input()
        else:
            # Modo linha de comando
            album_url = args.url
            max_workers = max(1, min(8, args.threads))
            headless = not args.no_headless
            
            # Valida URL
            if not ("yupoo.com" in album_url and ("albums" in album_url or "categories" in album_url or "collections" in album_url)):
                print("URL inválida! Certifique-se de que é um link de álbum, categoria ou collection do Yupoo.")
                print("Exemplos:")
                print("  Álbum: https://nfl-world.x.yupoo.com/albums/100300873?uid=1")
                print("  Categoria: https://minkang.x.yupoo.com/categories/2890904")
                print("  Collection: https://exemplo.x.yupoo.com/collections/123456")
                sys.exit(1)
        
        # Cria o downloader com as configurações
        downloader = YupooParallelDownloader(headless=headless, max_workers=max_workers)
        
        print(f"\nConfigurações:")
        print(f"  URL: {album_url}")
        print(f"  Threads: {max_workers}")
        print(f"  Headless: {'Sim' if headless else 'Não'}")
        print()
        
        # Detecta se é álbum, categoria ou collection e executa o método apropriado
        if "categories" in album_url:
            print("Detectado: URL de categoria")
            downloader.download_category(album_url)
        elif "collections" in album_url:
            print("Detectado: URL de collection")
            downloader.download_collection(album_url)
        else:
            print("Detectado: URL de álbum")
            downloader.download_album(album_url)
        
    except KeyboardInterrupt:
        print("\nProcesso interrompido pelo usuário.")
    except Exception as e:
        print(f"Erro geral: {e}")
