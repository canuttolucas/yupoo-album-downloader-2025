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

class YupooGUIDownloader:
    def __init__(self, headless=True, max_workers=4, log_callback=None):
        """
        Inicializa o downloader do Yupoo com callback para logs da GUI
        
        Args:
            headless: Se True, executa sem interface gráfica
            max_workers: Número máximo de threads paralelas
            log_callback: Função para enviar logs para a GUI
        """
        self.headless = headless
        self.max_workers = max_workers
        self.output_dir = None
        self.data_ids = []
        self.lock = threading.Lock()
        self.log_callback = log_callback
        self.is_cancelled = False
    
    def log(self, message, level="INFO"):
        """Envia log para a GUI"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
    
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
            self.log(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            self.log(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
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
            self.log(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            self.log(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
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
            self.log(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            self.log(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
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
        # chrome_options.add_argument('--disable-images')  # Desabilitar isso para garantir carregamento dinâmico
        # chrome_options.add_argument('--disable-javascript')  # Desabilitar isso quebra o scroll dinâmico do Yupoo
        
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
        self.log(f"Abrindo álbum: {album_url}")
        driver = self.create_driver()
        
        try:
            driver.get(album_url)
            time.sleep(3)
            
            # Scroll para carregar todas as imagens
            self.scroll_to_load_all(driver)
            
            self.log("Procurando data-ids das miniaturas...")
            
            # Encontra todos os elementos que contêm data-id
            elements_with_data_id = driver.find_elements(By.XPATH, "//div[@data-id]")
            self.log(f"Encontrados {len(elements_with_data_id)} elementos com data-id")
            
            data_ids = []
            for element in elements_with_data_id:
                if self.is_cancelled:
                    break
                data_id = element.get_attribute('data-id')
                if data_id and data_id.isdigit():
                    data_ids.append(data_id)
                    self.log(f"Data-ID encontrado: {data_id}")
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_data_ids = []
            for data_id in data_ids:
                if data_id not in seen:
                    seen.add(data_id)
                    unique_data_ids.append(data_id)
            
            self.log(f"Total de {len(unique_data_ids)} data-ids únicos encontrados")
            return unique_data_ids
            
        except Exception as e:
            self.log(f"Erro ao capturar data-ids: {e}", "ERROR")
            return []
        finally:
            driver.quit()
    
    def scroll_to_load_all(self, driver):
        """Faz scroll na página para carregar todas as imagens"""
        self.log("Fazendo scroll para carregar todas as imagens...")
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            if self.is_cancelled:
                break
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
        self.log(f"Abrindo categoria: {category_url}")
        driver = self.create_driver()
        
        try:
            driver.get(category_url)
            time.sleep(3)
            
            # Scroll para carregar todos os álbuns
            self.scroll_to_load_all(driver)
            
            self.log("Procurando álbuns na categoria...")
            
            # Encontra todos os links de álbuns
            album_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/albums/')]")
            self.log(f"Encontrados {len(album_links)} links de álbuns")
            
            album_urls = []
            for link in album_links:
                if self.is_cancelled:
                    break
                href = link.get_attribute('href')
                if href and '/albums/' in href:
                    album_urls.append(href)
                    self.log(f"Álbum encontrado: {href}")
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_album_urls = []
            for url in album_urls:
                if url not in seen:
                    seen.add(url)
                    unique_album_urls.append(url)
            
            self.log(f"Total de {len(unique_album_urls)} álbuns únicos encontrados na categoria")
            return unique_album_urls
            
        except Exception as e:
            self.log(f"Erro ao capturar álbuns da categoria: {e}", "ERROR")
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
        self.log(f"Abrindo collection: {collection_url}")
        driver = self.create_driver()
        
        try:
            driver.get(collection_url)
            time.sleep(3)
            
            # Scroll para carregar todos os álbuns
            self.scroll_to_load_all(driver)
            
            self.log("Procurando álbuns na collection...")
            
            # Encontra todos os links de álbuns
            album_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/albums/')]")
            self.log(f"Encontrados {len(album_links)} links de álbuns")
            
            album_urls = []
            for link in album_links:
                if self.is_cancelled:
                    break
                href = link.get_attribute('href')
                if href and '/albums/' in href:
                    album_urls.append(href)
                    self.log(f"Álbum encontrado: {href}")
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_album_urls = []
            for url in album_urls:
                if url not in seen:
                    seen.add(url)
                    unique_album_urls.append(url)
            
            self.log(f"Total de {len(unique_album_urls)} álbuns únicos encontrados na collection")
            return unique_album_urls
            
        except Exception as e:
            self.log(f"Erro ao capturar álbuns da collection: {e}", "ERROR")
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
        if self.is_cancelled:
            return (False, data_id, None, "Cancelado")
            
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
                self.log(f"[{index + 1:03d}/{len(self.data_ids)}] Capturando ID {data_id}...")
            
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
                self.log(f"ID {data_id} salvo: {filename}", "SUCCESS")
            
            return (True, data_id, filename, None)
            
        except Exception as e:
            error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            with self.lock:
                self.log(f"ID {data_id} falhou: {error_msg}", "ERROR")
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
        self.log("=" * 80)
        self.log("YUPOO PARALLEL DOWNLOADER - Captura Paralela em 4K")
        self.log(f"Threads paralelas: {self.max_workers}")
        self.log("=" * 80)
        
        # Passo 0: Criar pasta específica para o álbum
        self.create_album_folder(album_url)
        
        # Passo 1: Capturar todos os data-ids das miniaturas
        self.data_ids = self.get_data_ids(album_url)
        
        if not self.data_ids:
            self.log("Nenhum data-id encontrado no álbum!", "ERROR")
            return
        
        self.log(f"Iniciando captura paralela de {len(self.data_ids)} imagens...")
        self.log("=" * 80)
        
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
                if self.is_cancelled:
                    break
                    
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
                    self.log(f"Progresso: {successful + failed}/{len(self.data_ids)} | Taxa: {rate:.1f} img/min | ETA: {eta/60:.1f} min")
        
        elapsed_total = time.time() - start_time
        self.log("=" * 80)
        self.log(f"Captura paralela concluida em {elapsed_total/60:.1f} minutos!")
        self.log(f"Sucesso: {successful} imagens", "SUCCESS")
        self.log(f"Falhas: {failed} imagens", "ERROR" if failed > 0 else "INFO")
        self.log(f"Taxa media: {len(self.data_ids)/elapsed_total*60:.1f} imagens/minuto")
        self.log(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        self.log("=" * 80)
    
    def download_category(self, category_url):
        """
        Processo completo para categoria: obtém todos os álbuns e baixa todas as imagens
        
        Args:
            category_url: URL da categoria Yupoo
        """
        self.log("=" * 80)
        self.log("YUPOO PARALLEL DOWNLOADER - Download de Categoria")
        self.log(f"Threads paralelas: {self.max_workers}")
        self.log("=" * 80)
        
        # Passo 0: Criar pasta específica para a categoria
        self.create_category_folder(category_url)
        
        # Passo 1: Obter todos os álbuns da categoria
        album_urls = self.get_albums_from_category(category_url)
        
        if not album_urls:
            self.log("Nenhum álbum encontrado na categoria!", "ERROR")
            return
        
        self.log(f"Processando {len(album_urls)} álbuns da categoria...")
        self.log("=" * 80)
        
        # Passo 2: Para cada álbum, obter data-ids e baixar imagens
        total_successful = 0
        total_failed = 0
        start_time = time.time()
        
        for album_index, album_url in enumerate(album_urls):
            if self.is_cancelled:
                break
                
            self.log(f"[Álbum {album_index + 1}/{len(album_urls)}] Processando: {album_url}")
            
            # Obter data-ids do álbum
            data_ids = self.get_data_ids(album_url)
            
            if not data_ids:
                self.log(f"Nenhum data-id encontrado no álbum {album_index + 1}")
                continue
            
            self.log(f"Encontrados {len(data_ids)} imagens no álbum")
            
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
                    if self.is_cancelled:
                        break
                        
                    success, data_id, filename, error = future.result()
                    
                    if success:
                        successful += 1
                        total_successful += 1
                    else:
                        failed += 1
                        total_failed += 1
            
            self.log(f"Álbum {album_index + 1} concluído: {successful} sucessos, {failed} falhas")
        
        elapsed_total = time.time() - start_time
        self.log("=" * 80)
        self.log(f"Download da categoria concluído em {elapsed_total/60:.1f} minutos!")
        self.log(f"Total de sucessos: {total_successful} imagens", "SUCCESS")
        self.log(f"Total de falhas: {total_failed} imagens", "ERROR" if total_failed > 0 else "INFO")
        self.log(f"Taxa media: {(total_successful + total_failed)/elapsed_total*60:.1f} imagens/minuto")
        self.log(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        self.log("=" * 80)
    
    def download_collection(self, collection_url):
        """
        Processo completo para collection: obtém todos os álbuns e baixa todas as imagens
        
        Args:
            collection_url: URL da collection Yupoo
        """
        self.log("=" * 80)
        self.log("YUPOO PARALLEL DOWNLOADER - Download de Collection")
        self.log(f"Threads paralelas: {self.max_workers}")
        self.log("=" * 80)
        
        # Passo 0: Criar pasta específica para a collection
        self.create_collection_folder(collection_url)
        
        # Passo 1: Obter todos os álbuns da collection
        album_urls = self.get_albums_from_collection(collection_url)
        
        if not album_urls:
            self.log("Nenhum álbum encontrado na collection!", "ERROR")
            return
        
        self.log(f"Processando {len(album_urls)} álbuns da collection...")
        self.log("=" * 80)
        
        # Passo 2: Para cada álbum, obter data-ids e baixar imagens
        total_successful = 0
        total_failed = 0
        start_time = time.time()
        
        for album_index, album_url in enumerate(album_urls):
            if self.is_cancelled:
                break
                
            self.log(f"[Álbum {album_index + 1}/{len(album_urls)}] Processando: {album_url}")
            
            # Obter data-ids do álbum
            data_ids = self.get_data_ids(album_url)
            
            if not data_ids:
                self.log(f"Nenhum data-id encontrado no álbum {album_index + 1}")
                continue
            
            self.log(f"Encontrados {len(data_ids)} imagens no álbum")
            
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
                    if self.is_cancelled:
                        break
                        
                    success, data_id, filename, error = future.result()
                    
                    if success:
                        successful += 1
                        total_successful += 1
                    else:
                        failed += 1
                        total_failed += 1
            
            self.log(f"Álbum {album_index + 1} concluído: {successful} sucessos, {failed} falhas")
        
        elapsed_total = time.time() - start_time
        self.log("=" * 80)
        self.log(f"Download da collection concluído em {elapsed_total/60:.1f} minutos!")
        self.log(f"Total de sucessos: {total_successful} imagens", "SUCCESS")
        self.log(f"Total de falhas: {total_failed} imagens", "ERROR" if total_failed > 0 else "INFO")
        self.log(f"Taxa media: {(total_successful + total_failed)/elapsed_total*60:.1f} imagens/minuto")
        self.log(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        self.log("=" * 80)
    
    def cancel(self):
        """Cancela o download"""
        self.is_cancelled = True
        self.log("Download cancelado pelo usuário", "WARNING")



