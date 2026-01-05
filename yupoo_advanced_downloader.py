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
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import urllib.parse as urlparse
from urllib.parse import urlencode
from photo_organizer import PhotoOrganizer

class YupooAdvancedDownloader:
    def __init__(self, headless=True, max_workers=4, log_callback=None, openai_api_key=None):
        """
        Inicializa o downloader avançado do Yupoo com funcionalidades de paginação e capa
        
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
        self.openai_api_key = openai_api_key
        self.is_cancelled = False
        self.album_title = ""
        self.album_cover_id = None
        self.active_drivers = [] # Para fechar tudo no cancel
        
        # Inicializar Organizador se possível
        try:
            self.organizer = PhotoOrganizer(log_callback=log_callback, openai_api_key=openai_api_key)
            self.log("Organizador de Fotos carregado e pronto para uso ao vivo.")
        except Exception as e:
            self.organizer = None
            self.log(f"Aviso: Não foi possível carregar o Organizador de Fotos: {e}", "WARNING")
    
    def log(self, message, level="INFO"):
        """Envia log para a GUI"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
            
    def _add_page_to_url(self, url, page_num):
        """Helper para adicionar parâmetro de página na URL mantendo outros parâmetros"""
        url_parts = list(urlparse.urlparse(url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update({'page': page_num})
        url_parts[4] = urlencode(query)
        return urlparse.urlunparse(url_parts)
    
    def create_album_folder(self, album_url):
        """
        Cria uma pasta específica para o álbum baseada na URL
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            Caminho da pasta criada
        """
        # Extrai informações da URL para criar nome da pasta
        url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/(\d+)(?:\?uid=(\d+))?', album_url)
        
        if url_parts:
            subdomain = url_parts.group(1)
            album_id = url_parts.group(2)
            uid = url_parts.group(3) if url_parts.group(3) else "unknown"
            folder_name = f"yupoo_{subdomain}_album_{album_id}_uid_{uid}"
        else:
            album_id_match = re.search(r'/albums/(\d+)', album_url)
            if album_id_match:
                album_id = album_id_match.group(1)
                folder_name = f"yupoo_album_{album_id}"
            else:
                album_id = str(int(time.time()))
                folder_name = f"yupoo_album_{album_id}"
        
        self.output_dir = folder_name
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.log(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            self.log(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
        return self.output_dir
    
    def create_driver(self):
        """Cria uma nova instância do ChromeDriver com anti-bloqueio"""
        chrome_options = Options()
        chrome_options.add_argument('--window-size=3840,2160')
        chrome_options.add_argument('--start-maximized')
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Anti-bloqueio
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.exclude_switches = ["enable-automation"]
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Adicionar à lista de drivers ativos
        self.active_drivers.append(driver)
        return driver
    
    def create_driver_for_cover(self):
        """Cria um driver com JavaScript habilitado para download de capa"""
        chrome_options = Options()
        
        # Configurações para renderização em 4K
        chrome_options.add_argument('--window-size=3840,2160')
        chrome_options.add_argument('--start-maximized')
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Configurações adicionais (MAS COM JAVASCRIPT HABILITADO)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--force-device-scale-factor=1')
        # NÃO desabilitar imagens nem JavaScript para poder carregar dinamicamente
        
        # User agent para evitar bloqueios
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(3840, 2160)
        return driver
    
    def get_album_info(self, album_url):
        """
        Obtém informações do álbum: título e ID da capa
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            Tupla (album_title, cover_id)
        """
        self.log(f"Obtendo informações do álbum: {album_url}")
        driver = self.create_driver()
        
        try:
            driver.get(album_url)
            time.sleep(3)
            
            # Obter título do álbum
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, ".showalbumheader__gallerytitle span[data-name]")
                self.album_title = title_element.get_attribute("data-name")
                self.log(f"Título do álbum: {self.album_title}")
            except NoSuchElementException:
                self.album_title = "Album_Sem_Titulo"
                self.log("Título do álbum não encontrado, usando nome padrão")
            
            # Obter ID da capa do álbum
            try:
                cover_element = driver.find_element(By.CSS_SELECTOR, ".showalbumheader__gallerycover .autocover[data-type='photo']")
                cover_src = cover_element.get_attribute("src")
                # Extrair ID da capa do src: //photo.yupoo.com/minkang/79dfdc01/medium.jpg
                cover_id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', cover_src)
                if cover_id_match:
                    self.album_cover_id = cover_id_match.group(1)
                    self.log(f"ID da capa encontrado: {self.album_cover_id}")
                else:
                    self.album_cover_id = None
                    self.log("ID da capa não encontrado")
            except NoSuchElementException:
                self.album_cover_id = None
                self.log("Capa do álbum não encontrada")
            
            return self.album_title, self.album_cover_id
            
        except Exception as e:
            self.log(f"Erro ao obter informações do álbum: {e}", "ERROR")
            return "Album_Sem_Titulo", None
        finally:
            driver.quit()
    
    def get_pagination_info(self, album_url):
        """
        Obtém informações de paginação do álbum
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            Tupla (total_pages, current_page)
        """
        self.log("Analisando paginação do álbum...")
        driver = self.create_driver()
        
        try:
            driver.get(album_url)
            time.sleep(3)
            
            # Scroll para carregar todas as imagens e paginação
            self.scroll_to_load_all(driver)
            
            # Tentar obter do input de paginação (mais confiável)
            try:
                page_input = driver.find_element(By.CSS_SELECTOR, ".pagination__jumpwrap input[name='page']")
                total_pages = int(page_input.get_attribute("max"))
                self.log(f"Total de páginas encontradas via input: {total_pages}")
                return total_pages, 1
            except:
                pass

            # Procurar por elementos de paginação (fallback)
            try:
                pagination = driver.find_element(By.CSS_SELECTOR, "nav.pagination__main")
                page_links = pagination.find_elements(By.CSS_SELECTOR, "a.pagination__number")
                
                page_numbers = []
                for link in page_links:
                    try:
                        page_num = int(link.text.strip())
                        page_numbers.append(page_num)
                    except ValueError:
                        continue
                
                if page_numbers:
                    total_pages = max(page_numbers)
                    self.log(f"Total de páginas encontradas via links: {total_pages}")
                    return total_pages, 1
                else:
                    self.log("Nenhuma paginação encontrada, assumindo 1 página")
                    return 1, 1
                    
            except NoSuchElementException:
                self.log("Elemento de paginação não encontrado, assumindo 1 página")
                return 1, 1
                
        except Exception as e:
            self.log(f"Erro ao analisar paginação: {e}", "ERROR")
            return 1, 1
        finally:
            driver.quit()
    
    def get_data_ids_from_page(self, page_url):
        """
        Captura todos os data-id das miniaturas de uma página específica
        
        Args:
            page_url: URL da página do álbum
            
        Returns:
            Lista de data-ids das imagens
        """
        self.log(f"Processando página: {page_url}")
        driver = self.create_driver()
        
        try:
            driver.get(page_url)
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
            
            self.log(f"Total de {len(unique_data_ids)} data-ids únicos encontrados na página")
            return unique_data_ids
            
        except Exception as e:
            self.log(f"Erro ao capturar data-ids da página: {e}", "ERROR")
            return []
        finally:
            driver.quit()
    
    def scroll_to_load_all(self, driver):
        """Scrolla a página usando JavaScript para carregar álbuns dinâmicos (Lazy Loading)"""
        self.log("Aguardando carregamento inicial (2s)...")
        time.sleep(2)
        try:
            self.log("Iniciando Scroll Progressivo via JavaScript...")
            # Script JS para scrollar suavemente até o final, disparando lazy loading
            driver.execute_script("""
                const scrollStep = 400;
                const scrollDelay = 300;
                const totalHeight = document.body.scrollHeight;
                let currentScroll = 0;
                
                const scrollInterval = setInterval(() => {
                    window.scrollBy(0, scrollStep);
                    currentScroll += scrollStep;
                    if (currentScroll >= document.body.scrollHeight) {
                        clearInterval(scrollInterval);
                    }
                }, scrollDelay);
            """)
            
            # Aguardar o tempo do scroll (aprox 8 a 10 segundos para páginas grandes)
            time.sleep(10)
            
            # Garantir que chegou no fim absoluto
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
        except Exception as e:
            self.log(f"Aviso no scroll: {e}", "WARNING")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    def get_cover_image_id_from_album_page(self, album_url):
        """
        Obtém o ID da capa diretamente da página do álbum
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            ID da imagem real da capa ou None
        """
        driver = None
        try:
            driver = self.create_driver()
            driver.get(album_url)
            time.sleep(3)
            
            # Procura pela capa do álbum na página principal
            try:
                # Primeiro tenta encontrar a capa pelo seletor específico
                cover_element = driver.find_element(By.CSS_SELECTOR, ".showalbumheader__gallerycover .autocover[data-type='photo']")
                cover_src = cover_element.get_attribute("src")
                
                # Extrair ID da capa do src: //photo.yupoo.com/minkang/79dfdc01/medium.jpg
                cover_id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', cover_src)
                if cover_id_match:
                    return cover_id_match.group(1)
                    
            except NoSuchElementException:
                # Se não encontrar pelo seletor específico, procura por qualquer imagem com autocover
                try:
                    cover_elements = driver.find_elements(By.CSS_SELECTOR, ".autocover[data-type='photo']")
                    for element in cover_elements:
                        src = element.get_attribute("src")
                        if src and "medium.jpg" in src:  # Capa geralmente tem medium.jpg
                            id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', src)
                            if id_match:
                                return id_match.group(1)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"Erro ao obter ID da capa: {e}", "ERROR")
        finally:
            if driver:
                driver.quit()
        
        return None
    def get_image_real_id_quick(self, data_id, base_url, driver):
        """
        Versão rápida de get_image_real_id que usa um driver já aberto
        
        Args:
            data_id: Data-ID da miniatura
            base_url: URL base do álbum
            driver: Driver já aberto
            
        Returns:
            ID da imagem real ou None
        """
        try:
            # Extrai subdomain e uid da URL base
            url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/\d+(?:\?uid=(\d+))?', base_url)
            if url_parts:
                subdomain = url_parts.group(1)
                uid = url_parts.group(2) if url_parts.group(2) else "1"
            else:
                subdomain = "nfl-world"
                uid = "1"
            
            # Constrói a URL da imagem individual
            image_url = f"https://{subdomain}.x.yupoo.com/{data_id}?uid={uid}"
            
            # Salvar URL atual
            current_url = driver.current_url
            
            try:
                driver.get(image_url)
                time.sleep(0.5)
                
                # Procura pelo elemento img com data-src ou data-origin-src
                try:
                    img_element = driver.find_element(By.CSS_SELECTOR, "img[data-src], img[data-origin-src], .viewer_img")
                    
                    # Tenta data-src primeiro
                    data_src = img_element.get_attribute('data-src')
                    if data_src:
                        id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', data_src)
                        if id_match:
                            return id_match.group(1)
                    
                    # Tenta src normal
                    src = img_element.get_attribute('src')
                    if src:
                        id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', src)
                        if id_match:
                            return id_match.group(1)
                    
                    # Se não encontrou, tenta data-origin-src
                    data_origin_src = img_element.get_attribute('data-origin-src')
                    if data_origin_src:
                        id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', data_origin_src)
                        if id_match:
                            return id_match.group(1)
                            
                except NoSuchElementException:
                    pass
            finally:
                # Voltar para a URL anterior
                try:
                    driver.get(current_url)
                    time.sleep(0.3)
                except:
                    pass
                
        except Exception as e:
            self.log(f"Erro ao obter ID rápido da imagem {data_id}: {e}", "ERROR")
        
        return None
    
    def download_cover_direct(self, driver, data_id, album_url):
        """
        Baixa a capa diretamente usando o driver já aberto
        
        Args:
            driver: Driver já aberto na página do álbum
            data_id: Data-ID da capa
            album_url: URL base do álbum
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Extrai subdomain e uid da URL base
            url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/\d+(?:\?uid=(\d+))?', album_url)
            if url_parts:
                subdomain = url_parts.group(1)
                uid = url_parts.group(2) if url_parts.group(2) else "1"
            else:
                subdomain = "nfl-world"
                uid = "1"
            
            # Constrói a URL da imagem individual
            image_url = f"https://{subdomain}.x.yupoo.com/{data_id}?uid={uid}"
            
            self.log(f"Navegando para: {image_url}")
            driver.get(image_url)
            time.sleep(2)
            
            # Aguarda o elemento img estar presente
            wait = WebDriverWait(driver, 10)
            
            # Procura pelo componente img específico
            img_element = None
            selectors = [
                "//img[contains(@class, 'viewer_img')]",
                "//div[@class='viewer_imgwrap']//img",
                "//div[contains(@class, 'viewer')]//img[not(contains(@class, 'avatar'))]",
                "img[data-src]",
                "img[data-origin-src]",
                "//img[contains(@src, 'photo.yupoo.com')]"
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        img_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    else:
                        img_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    
                    if img_element:
                        break
                except:
                    continue
            
            if not img_element:
                self.log("Elemento img não encontrado!", "ERROR")
                return False
            
            # Aguarda a imagem carregar completamente
            time.sleep(1)
            
            # Scroll até o elemento
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            time.sleep(0.5)
            
            # Captura screenshot do elemento específico
            screenshot = img_element.screenshot_as_png
            
            # Gera nome do arquivo
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', self.album_title)
            filename = f"{safe_title}_CAPA.png"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot)
            
            self.log(f"Capa salva: {filename}", "SUCCESS")
            self.log(f"Arquivo salvo em: {os.path.abspath(filepath)}")
            return True
            
        except Exception as e:
            self.log(f"Erro ao baixar capa diretamente: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
    
    def get_image_real_id(self, data_id, base_url):
        """
        Obtém o ID real da imagem (não data-id) para verificar se é a capa
        
        Args:
            data_id: Data-ID da miniatura
            base_url: URL base do álbum
            
        Returns:
            ID da imagem real ou None
        """
        driver = None
        try:
            # Cria driver para esta verificação
            driver = self.create_driver()
            
            # Extrai subdomain e uid da URL base
            url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/\d+(?:\?uid=(\d+))?', base_url)
            if url_parts:
                subdomain = url_parts.group(1)
                uid = url_parts.group(2) if url_parts.group(2) else "1"
            else:
                subdomain = "nfl-world"
                uid = "1"
            
            # Constrói a URL da imagem individual
            image_url = f"https://{subdomain}.x.yupoo.com/{data_id}?uid={uid}"
            
            driver.get(image_url)
            time.sleep(1)
            
            # Procura pelo elemento img com data-src ou data-origin-src
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, "img[data-src], img[data-origin-src]")
                
                # Tenta data-src primeiro
                data_src = img_element.get_attribute('data-src')
                if data_src:
                    # Extrair ID do data-src: //photo.yupoo.com/minkang/1d2f73da/big.jpg
                    id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', data_src)
                    if id_match:
                        return id_match.group(1)
                
                # Se não encontrou, tenta data-origin-src
                data_origin_src = img_element.get_attribute('data-origin-src')
                if data_origin_src:
                    id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', data_origin_src)
                    if id_match:
                        return id_match.group(1)
                        
            except NoSuchElementException:
                pass
                
        except Exception as e:
            self.log(f"Erro ao obter ID da imagem {data_id}: {e}", "ERROR")
        finally:
            if driver:
                driver.quit()
        
        return None
    
    def capture_single_image(self, data_id, index, base_url, is_cover=False):
        """
        Captura uma única imagem (função para thread)
        
        Args:
            data_id: ID da imagem
            index: Índice da imagem
            base_url: URL base do álbum para extrair subdomain e uid
            is_cover: Se True, é a capa do álbum
            
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
                subdomain = "nfl-world"
                uid = "1"
            
            # Constrói a URL da imagem individual dinamicamente
            image_url = f"https://{subdomain}.x.yupoo.com/{data_id}?uid={uid}"
            
            with self.lock:
                if is_cover:
                    self.log(f"[CAPA] Capturando ID {data_id}...")
                else:
                    self.log(f"[{index + 1:03d}] Capturando ID {data_id}...")
            
            driver.get(image_url)
            time.sleep(1)
            
            # Aguarda o elemento img estar presente
            wait = WebDriverWait(driver, 5)
            
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
            time.sleep(0.5)
            
            # Scroll até o elemento
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            
            # Captura screenshot do elemento específico
            screenshot = img_element.screenshot_as_png
            
            # Gera nome do arquivo baseado no título do álbum
            if is_cover:
                filename = f"{self.album_title}_CAPA.png"
            else:
                # Remove caracteres inválidos do título
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', self.album_title)
                filename = f"{safe_title}_{index + 1:04d}_id_{data_id}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot)
            
            with self.lock:
                if is_cover:
                    self.log(f"CAPA salva: {filename}", "SUCCESS")
                else:
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
    
    def download_album_advanced(self, album_url, download_mode="all", page_range=None):
        """
        Processo avançado de download com opções de paginação e capa
        
        Args:
            album_url: URL do álbum Yupoo
            download_mode: "all" para todas as fotos, "cover" para só a capa
            page_range: Tupla (start_page, end_page) ou None para todas as páginas
        """
        self.log("=" * 80)
        self.log("YUPOO ADVANCED DOWNLOADER - Download Avançado")
        self.log(f"Modo: {download_mode.upper()}")
        self.log(f"Threads paralelas: {self.max_workers}")
        self.log("=" * 80)
        
        # Passo 0: Criar pasta específica para o álbum
        self.create_album_folder(album_url)
        
        # Passo 1: Obter informações do álbum
        self.album_title, self.album_cover_id = self.get_album_info(album_url)
        
        # Passo 2: Se modo capa, baixar só a capa
        if download_mode == "cover":
            self.log("MODO CAPA ATIVADO - Baixando apenas a capa do álbum")
            
            # Método simplificado: pegar a primeira imagem do álbum (que geralmente é a capa)
            driver = None
            try:
                # Criar driver com JavaScript habilitado para carregar imagens dinamicamente
                driver = self.create_driver_for_cover()
                driver.get(album_url)
                time.sleep(4)  # Aguardar carregamento completo
                
                # Scroll para garantir que todas as imagens estejam carregadas
                self.scroll_to_load_all(driver)
                
                # Procurar pela imagem de capa real (do header)
                cover_data_id = None
                cover_unique_id = None
                
                # Passo A: Extrair o ID único da capa do header
                try:
                    cover_element = driver.find_element(By.CSS_SELECTOR, ".showalbumheader__gallerycover .autocover")
                    cover_src = cover_element.get_attribute("src")
                    # Extrair o ID como 'c6c14310' de '//photo.yupoo.com/joyjerseys/c6c14310/medium.jpg'
                    id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', cover_src)
                    if id_match:
                        cover_unique_id = id_match.group(1)
                        self.log(f"ID único da capa identificado: {cover_unique_id}")
                except Exception as e:
                    self.log(f"Erro ao identificar ID da capa no header: {e}", "WARNING")
                
                # Passo B: Procurar na grade de fotos a miniatura que contém esse ID
                if cover_unique_id:
                    try:
                        all_thumb_divs = driver.find_elements(By.CSS_SELECTOR, "div.autocover[data-id]")
                        for div in all_thumb_divs:
                            data_id = div.get_attribute('data-id')
                            # Verificar imagens dentro dessa div ou a própria div se for img
                            try:
                                img_in_div = div.find_element(By.TAG_NAME, "img")
                                img_src = img_in_div.get_attribute("src")
                                if cover_unique_id in img_src:
                                    cover_data_id = data_id
                                    self.log(f"Capa correspondente encontrada na grade! Data-ID: {cover_data_id}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        self.log(f"Erro ao buscar correspondência na grade: {e}", "WARNING")

                # Método Fallout: Se não encontrou por ID, pegar o primeiro elemento com data-id
                if not cover_data_id:
                    try:
                        # Primeiro, procurar por todos os elementos com data-id
                        all_images = driver.find_elements(By.XPATH, "//div[@data-id]")
                    
                        if all_images:
                            # Pegar o primeiro elemento com data-id válido
                            for img in all_images:
                                data_id = img.get_attribute('data-id')
                                if data_id and data_id.isdigit():
                                    cover_data_id = data_id
                                    self.log(f"Primeira imagem encontrada - Data-ID: {cover_data_id}")
                                    break
                    except Exception as e:
                        self.log(f"Erro ao encontrar imagens: {e}", "ERROR")
                
                # Método 2 (Fallback): Procurar pela capa do header do álbum e usar primeira imagem
                if not cover_data_id:
                    try:
                        # Tentar encontrar elemento de capa no header (opcional, apenas para log)
                        try:
                            cover_element = driver.find_element(By.CSS_SELECTOR, ".showalbumheader__gallerycover img, .autocover[data-type='photo'], img.autocover")
                            cover_src = cover_element.get_attribute("src")
                            if cover_src:
                                self.log(f"Encontrada capa no header: {cover_src}")
                        except:
                            pass
                        
                        # Se ainda não temos data-id, pegar qualquer primeiro data-id disponível
                        all_divs = driver.find_elements(By.XPATH, "//div[@data-id]")
                        for div in all_divs:
                            data_id = div.get_attribute('data-id')
                            if data_id and data_id.isdigit():
                                cover_data_id = data_id
                                self.log(f"Capa encontrada via fallback! Data-ID: {data_id}")
                                break
                    except Exception as e:
                        self.log(f"Erro no método fallback: {e}", "ERROR")
                        pass
                
                # Método 3 (Ultimo Fallback): Qualquer imagem disponível
                if not cover_data_id:
                    try:
                        first_image = driver.find_element(By.XPATH, "//div[@data-id]")
                        cover_data_id = first_image.get_attribute('data-id')
                        self.log(f"Usando primeira imagem disponível como capa: {cover_data_id}")
                    except NoSuchElementException:
                        self.log("Nenhuma imagem encontrada no álbum!", "ERROR")
                        return
                
                # Baixar a capa usando o método direto
                if cover_data_id:
                    self.log(f"Baixando capa do álbum (Data-ID: {cover_data_id})...")
                    success = self.download_cover_direct(driver, cover_data_id, album_url)
                    
                    if success:
                        self.log("Capa baixada com sucesso!", "SUCCESS")
                    else:
                        self.log("Erro ao baixar capa", "ERROR")
                
            except Exception as e:
                self.log(f"Erro durante download da capa: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "ERROR")
            finally:
                if driver:
                    driver.quit()
            
            return
        
        # Passo 3: Modo todas as fotos - analisar paginação
        total_pages, current_page = self.get_pagination_info(album_url)
        
        if page_range:
            start_page, end_page = page_range
            if start_page < 1 or end_page > total_pages or start_page > end_page:
                self.log(f"Intervalo de páginas inválido! Total disponível: {total_pages}", "ERROR")
                return
            pages_to_process = list(range(start_page, end_page + 1))
        else:
            pages_to_process = list(range(1, total_pages + 1))
        
        self.log(f"Processando páginas: {pages_to_process}")
        
        # Passo 4: Coletar todos os data-ids de todas as páginas
        all_data_ids = []
        for page_num in pages_to_process:
            if self.is_cancelled:
                break
                
            if page_num == 1:
                page_url = album_url
            else:
                page_url = self._add_page_to_url(album_url, page_num)
            
            self.log(f"Processando página {page_num}/{total_pages}")
            page_data_ids = self.get_data_ids_from_page(page_url)
            all_data_ids.extend(page_data_ids)
        
        if not all_data_ids:
            self.log("Nenhum data-id encontrado!", "ERROR")
            return
        
        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_data_ids = []
        for data_id in all_data_ids:
            if data_id not in seen:
                seen.add(data_id)
                unique_data_ids.append(data_id)
        
        self.data_ids = unique_data_ids
        self.log(f"Total de {len(self.data_ids)} imagens únicas para baixar")
        
        # Passo 5: Baixar todas as imagens
        self.log("Iniciando download de todas as imagens...")
        self.log("=" * 80)
        
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
        self.log(f"Download concluído em {elapsed_total/60:.1f} minutos!")
        self.log(f"Sucesso: {successful} imagens", "SUCCESS")
        self.log(f"Falhas: {failed} imagens", "ERROR" if failed > 0 else "INFO")
        self.log(f"Taxa média: {len(self.data_ids)/elapsed_total*60:.1f} imagens/minuto")
        self.log(f"Imagens salvas em: {os.path.abspath(self.output_dir)}")
        self.log("=" * 80)
    
    def get_total_pages(self, collection_url):
        """
        Obtém o número total de páginas de uma coleção
        
        Args:
            collection_url: URL da coleção Yupoo
            
        Returns:
            Número total de páginas como inteiro
        """
        self.log(f"Analisando paginação da coleção: {collection_url}")
        driver = self.create_driver()
        
        try:
            driver.get(collection_url)
            time.sleep(3)
            
            # Scroll para carregar a paginação
            self.scroll_to_load_all(driver)
            
            # Método robusto para detectar total de páginas na coleção
            try:
                # 1. Tentar pelo input de paginação (MAIS CONFIÁVEL)
                # Seletor: form.pagination__jumpwrap input[name='page']
                page_input = driver.find_element(By.CSS_SELECTOR, "form.pagination__jumpwrap input")
                max_page = page_input.get_attribute("max")
                if max_page and max_page.isdigit():
                    total_pages = int(max_page)
                    self.log(f"Total de páginas encontrado via input: {total_pages}")
                    return total_pages
            except:
                pass

            try:
                # 2. Tentar pelo texto "no total X páginas"
                # Exemplo de seletor: html body.yupoo-with-head-foot div.container.categories__wrapper div.categories__box div.categories__box-right form.pagination__jumpwrap span
                pagination_span = driver.find_element(By.XPATH, "//form[contains(@class, 'pagination__jumpwrap')]/span")
                text = pagination_span.text # "no total 2 páginas" ou "in total 2 pages"
                
                # Extrair número
                num_match = re.search(r'total (\d+)', text, re.IGNORECASE)
                if num_match:
                    total_pages = int(num_match.group(1))
                    self.log(f"Total de páginas encontrado via texto: {total_pages}")
                    return total_pages
            except:
                pass
                
            # Fallbacks anteriores
            try:
                # Procura pelo texto "in total X pages" ou "no total X páginas" genérico
                pagination_text = driver.find_element(By.XPATH, "//*[(contains(text(), 'in total') or contains(text(), 'no total')) and contains(text(), 'pag')]")
                text = pagination_text.text
                num_match = re.search(r'(?:total|total\sde)\s+(\d+)', text, re.IGNORECASE)
                if num_match:
                    total_pages = int(num_match.group(1))
                    self.log(f"Total de páginas encontrado (fallback): {total_pages}")
                    return total_pages
            except:
                pass
            
            # Se não encontrar nada, tenta identificar se há botão "Next" ou paginação numérica
            try:
                pagination_nav = driver.find_element(By.CSS_SELECTOR, "nav.pagination__main")
                self.log("Elemento de navegação encontrado, mas número exato não. Assumindo que há mais páginas.")
                return 999 # Retorna um número alto para indicar que há muitas páginas, ou pode retornar 1
            except:
                pass
            
            self.log("Nenhuma paginação detectada, assumindo 1 página")
            return 1
                
        except Exception as e:
            self.log(f"Erro ao analisar paginação: {e}", "ERROR")
            return 1
        finally:
            driver.quit()
    
    def download_covers_from_collection(self, collection_url, page_option='all'):
        """
        Baixa apenas as capas dos álbuns de uma coleção/categoria em alta qualidade
        
        Args:
            collection_url: URL da coleção ou categoria Yupoo
            page_option: 'all', 'first', ou tupla (start, end) para intervalo
        """
        self.log(f"Iniciando download de CAPAS da coleção/categoria: {collection_url}")
        
        # 1. Criar pasta da coleção
        self.create_collection_folder(collection_url)
        self.log("=" * 80)
        self.log("YUPOO COLLECTION COVER DOWNLOADER - Capas em Alta Qualidade")
        self.log(f"Opção de páginas: {page_option}")
        self.log("=" * 80)
        
        # Determinar páginas para processar
        if page_option == 'first':
            pages_to_process = [1]
        elif page_option == 'all':
            total_pages = self.get_total_pages(collection_url)
            pages_to_process = list(range(1, total_pages + 1))
        elif isinstance(page_option, tuple):
            start_page, end_page = page_option
            total_pages = self.get_total_pages(collection_url)
            if start_page < 1 or end_page > total_pages or start_page > end_page:
                self.log(f"Intervalo de páginas inválido! Total disponível: {total_pages}", "ERROR")
                return
            pages_to_process = list(range(start_page, end_page + 1))
        else:
            self.log("Opção de páginas inválida!", "ERROR")
            return
        
        self.log(f"Processando páginas: {pages_to_process}")
        
        # Criar pasta para a coleção
        collection_folder = self.create_collection_folder(collection_url)
        
        all_albums = []
        
        # Processar cada página
        for page_num in pages_to_process:
            if self.is_cancelled:
                break
                
            if page_num == 1:
                page_url = collection_url
            else:
                page_url = f"{collection_url}?page={page_num}"
            
            self.log(f"Processando página {page_num}/{max(pages_to_process)}")
            page_albums = self.get_albums_from_collection_page(page_url)
            all_albums.extend(page_albums)
        
        if not all_albums:
            self.log("Nenhum álbum encontrado na coleção!", "ERROR")
            return
        
        self.log(f"Total de {len(all_albums)} álbuns encontrados")
        
        # Baixar capas de todos os álbuns em paralelo
        successful = 0
        failed = 0
        
        self.log(f"Iniciando download paralelo de {len(all_albums)} capas...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_album = {
                # info[0]=url, info[1]=thumb, info[2]=title
                executor.submit(self.download_cover_high_quality, info[0], self.extract_cover_id_from_thumbnail(info[1]), collection_folder, i+1, info[2]): i 
                for i, info in enumerate(all_albums)
                if not self.is_cancelled
            }
            
            for future in as_completed(future_to_album):
                if self.is_cancelled:
                    break
                try:
                    success = future.result()
                    if success:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    self.log(f"Erro em thread de download: {e}", "ERROR")
                    failed += 1
        
        self.log("=" * 80)
        self.log(f"Download de capas concluído!")
        self.log(f"Sucesso: {successful} capas", "SUCCESS")
        self.log(f"Falhas: {failed} capas", "ERROR" if failed > 0 else "INFO")
        self.log("=" * 80)

    
    def download_albums_from_collection(self, collection_url, page_option='all'):
        """
        Baixa todos os álbuns de uma coleção/categoria (todas as fotos)
        
        Args:
            collection_url: URL da coleção ou categoria Yupoo
            page_option: 'all', 'first', ou tupla (start, end) para intervalo
        """
        self.log(f"Iniciando download COMPLETO da coleção/categoria: {collection_url}")
        
        # 1. Criar pasta da coleção
        self.create_collection_folder(collection_url)
        self.log("=" * 80)
        self.log("YUPOO COLLECTION ALBUMS DOWNLOADER - Todos os Álbuns")
        self.log(f"Opção de páginas: {page_option}")
        self.log("=" * 80)
        
        # Determinar páginas para processar
        if page_option == 'first':
            pages_to_process = [1]
        elif page_option == 'all':
            total_pages = self.get_total_pages(collection_url)
            pages_to_process = list(range(1, total_pages + 1))
        elif isinstance(page_option, tuple):
            start_page, end_page = page_option
            total_pages = self.get_total_pages(collection_url)
            if start_page < 1 or end_page > total_pages or start_page > end_page:
                self.log(f"Intervalo de páginas inválido! Total disponível: {total_pages}", "ERROR")
                return
            pages_to_process = list(range(start_page, end_page + 1))
        else:
            self.log("Opção de páginas inválida!", "ERROR")
            return
        
        self.log(f"Processando páginas: {pages_to_process}")
        
        all_albums = []
        
        # Processar cada página
        for page_num in pages_to_process:
            if self.is_cancelled:
                break
                
            if page_num == 1:
                page_url = collection_url
            else:
                page_url = self._add_page_to_url(collection_url, page_num)
            
            self.log(f"Processando página {page_num}/{max(pages_to_process)}")
            page_albums = self.get_albums_from_collection_page(page_url)
            all_albums.extend(page_albums)
        
        if not all_albums:
            self.log("Nenhum álbum encontrado na coleção!", "ERROR")
            return
        
        self.log(f"Total de {len(all_albums)} álbuns encontrados")
        
        # Baixar cada álbum completo
        successful = 0
        failed = 0
        
        for i, album_info in enumerate(all_albums):
            if self.is_cancelled:
                break
                
            album_url, _, _ = album_info
            self.log(f"Baixando álbum {i+1}/{len(all_albums)}: {album_url}")
            
            try:
                # Usar a função existente para baixar o álbum completo
                self.download_album_advanced(album_url, "all", None)
                successful += 1
                
            except Exception as e:
                self.log(f"Erro ao baixar álbum {i+1}: {e}", "ERROR")
                failed += 1
        
        self.log("=" * 80)
        self.log(f"Download de álbuns concluído!")
        self.log(f"Sucesso: {successful} álbuns", "SUCCESS")
        self.log(f"Falhas: {failed} álbuns", "ERROR" if failed > 0 else "INFO")
        self.log("=" * 80)
    
    def create_collection_folder(self, collection_url):
        """
        Cria uma pasta específica para a coleção usando a categoria da trilha de navegação (crumbs)
        
        Args:
            collection_url: URL da coleção Yupoo
            
        Returns:
            Caminho da pasta criada
        """
        self.log("Identificando nome da categoria para a pasta...")
        driver = self.create_driver()
        folder_name = None
        
        try:
            driver.get(collection_url)
            time.sleep(2)
            
            # Tenta encontrar a categoria no crumbs: a.yupoo-crumbs-span[title]
            try:
                # O último link no crumbs geralmente é a categoria/coleção atual
                crumbs = driver.find_elements(By.CSS_SELECTOR, "a.yupoo-crumbs-span")
                if crumbs:
                    category_name = crumbs[-1].get_attribute("title") or crumbs[-1].text
                    if category_name:
                        folder_name = re.sub(r'[<>:"/\\|?*]', '_', category_name).strip()
                        self.log(f"Categoria identificada: {folder_name}")
            except:
                pass
                
        except Exception as e:
            self.log(f"Erro ao obter nome da coleção/categoria: {e}", "WARNING")
        finally:
            driver.quit()

        # Fallback se não conseguiu extrair do site
        if not folder_name:
            # Tenta collections
            url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/collections/(\d+)', collection_url)
            if url_parts:
                folder_name = f"yupoo_{url_parts.group(1)}_collection_{url_parts.group(2)}"
            else:
                # Tenta categories
                url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/categories/(\d+)', collection_url)
                if url_parts:
                    folder_name = f"yupoo_{url_parts.group(1)}_category_{url_parts.group(2)}"
                else:
                    folder_name = f"yupoo_collection_{int(time.time())}"
        
        self.output_dir = folder_name
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.log(f"Pasta criada: {os.path.abspath(self.output_dir)}")
        else:
            self.log(f"Usando pasta existente: {os.path.abspath(self.output_dir)}")
        
        return self.output_dir
    
    def get_albums_from_collection_page(self, page_url):
        """
        Extrai informações dos álbuns de uma página de coleção
        
        Args:
            page_url: URL da página da coleção
            
        Returns:
            Lista de tuplas (album_url, cover_thumbnail_url)
        """
        self.log(f"Extraindo álbuns da página: {page_url}")
        driver = self.create_driver()
        
        try:
            driver.get(page_url)
            time.sleep(4)
            
            # Scroll para carregar todos os álbuns
            self.scroll_to_load_all(driver)
            
            # Encontrar todos os links de álbuns (com scroll no fim ou meio, tentamos tudo)
            # Scroll para cima devagar para garantir que o find_elements pegue tudo se necessário,
            # mas na verdade o find_elements deveria pegar mesmo fora da view.
            
            selectors = ["a.album__main", "a[href*='/albums/']", ".album__title a"]
            album_links = []
            for sel in selectors:
                links = driver.find_elements(By.CSS_SELECTOR, sel)
                if len(links) > len(album_links):
                    album_links = links
            
            self.log(f"Iniciando extração de {len(album_links)} links detectados...")
            
            albums = []
            seen_urls = set()
            
            for link in album_links:
                try:
                    album_url = link.get_attribute('href')
                    if not album_url or album_url in seen_urls:
                        continue
                    
                    # Capturar título do álbum diretamente daqui (mais confiável)
                    album_title = link.get_attribute('title') or link.text
                    if not album_title:
                        try:
                            album_title = link.find_element(By.CSS_SELECTOR, ".album__title").text
                        except: pass
                    
                    # Limpar nome para arquivo
                    if album_title:
                        album_title = re.sub(r'[<>:"/\\|?*]', '_', album_title).strip()
                    else:
                        album_title = "Album_Sem_Nome"
                    
                    # Tentar encontrar miniatura de capa
                    try:
                        img_element = link.find_element(By.CSS_SELECTOR, "img")
                        cover_thumbnail_url = img_element.get_attribute('src') or img_element.get_attribute('data-src')
                    except:
                        try:
                            # Tentar via background-image no style
                            style = link.get_attribute('style') or ""
                            match = re.search(r'url\("?\'?([^"\']+)"?\'?\)', style)
                            if match:
                                cover_thumbnail_url = match.group(1)
                                if cover_thumbnail_url.startswith('//'):
                                    cover_thumbnail_url = 'https:' + cover_thumbnail_url
                            else:
                                # Tentar xpath como último recurso
                                img_element = link.find_element(By.XPATH, ".//img")
                                cover_thumbnail_url = img_element.get_attribute('src') or img_element.get_attribute('data-src')
                        except:
                            self.log(f"Aviso: Não foi possível encontrar imagem para o álbum {album_url}", "DEBUG")
                            continue
                    
                    if album_url and cover_thumbnail_url:
                        # Retornar (url, thumbnail, title)
                        albums.append((album_url, cover_thumbnail_url, album_title))
                        seen_urls.add(album_url)
                        
                except Exception:
                    continue
            
            self.log(f"Total de {len(albums)} álbuns extraídos!")
            return albums
        except Exception as e:
            self.log(f"Erro na extração: {e}", "ERROR")
            return []
        finally:
            driver.quit()
    
    def extract_cover_id_from_thumbnail(self, thumbnail_url):
        """
        Extrai o ID da capa da URL da miniatura
        
        Args:
            thumbnail_url: URL da miniatura (ex: //photo.yupoo.com/minkang/79dfdc01/medium.jpg)
            
        Returns:
            ID da capa ou None
        """
        try:
            # Extrair ID da miniatura: //photo.yupoo.com/minkang/79dfdc01/medium.jpg
            id_match = re.search(r'//photo\.yupoo\.com/[^/]+/([^/]+)/', thumbnail_url)
            if id_match:
                return id_match.group(1)
        except Exception as e:
            self.log(f"Erro ao extrair ID da miniatura: {e}", "ERROR")
        
        return None
    
    def download_cover_high_quality(self, album_url, cover_id, output_folder, album_index, album_name_preset=None):
        """
        Baixa a capa do álbum em alta qualidade com retentativas
        """
        for attempt in range(2): 
            if self.is_cancelled: return False
            driver = None
            try:
                driver = self.create_driver()
                driver.get(album_url)
                
                # Espera 5s e scroll 5s conforme sugerido
                self.scroll_to_load_all(driver)
                
                elements_with_data_id = driver.find_elements(By.XPATH, "//div[@data-id]")
                target_data_id = None
                
                def find_target(elems, cid):
                    for element in elems:
                        try:
                            img = element.find_element(By.TAG_NAME, "img")
                            src = img.get_attribute("src")
                            if src and cid in src:
                                return element.get_attribute('data-id')
                        except: continue
                    return None

                target_data_id = find_target(elements_with_data_id, cover_id)
                
                if not target_data_id:
                    if elements_with_data_id:
                        target_data_id = elements_with_data_id[0].get_attribute('data-id')
                    else: continue

                # Navegar para a página da imagem
                url_parsed = urlparse.urlparse(album_url)
                subdomain = url_parsed.netloc.split('.')[0]
                uid_match = re.search(r'uid=(\d+)', album_url)
                uid = uid_match.group(1) if uid_match else "1"
                
                image_url = f"https://{subdomain}.x.yupoo.com/{target_data_id}?uid={uid}"
                driver.get(image_url)
                time.sleep(2)
                
                img_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img[data-src], img[data-origin-src], .viewer_img"))
                )
                screenshot = img_element.screenshot_as_png
                
                # Usar nome pré-definido se disponível
                album_name = album_name_preset or f"Album_{album_index:03d}"

                filename = f"{album_name}_CAPA_HQ.png"
                filepath = os.path.join(output_folder, filename)
                with open(filepath, 'wb') as f: f.write(screenshot)
                self.log(f"Capa HQ salva: {filename}", "SUCCESS")
                
                # --- ORGANIZAÇÃO AO VIVO ---
                if self.organizer:
                    try:
                        classification = self.organizer.classify_file(filename)
                        if classification['team_name']:
                            # O diretório base para organização deve ser fora da pasta da coleção atual para seguir o padrão FUTEBOL/
                            # Mas se o usuário quiser manual, respeitamos. Aqui usamos o pai do output_folder
                            root_output = os.path.dirname(output_folder)
                            target_dir = os.path.join(root_output, classification['target_folder'])
                            target_path = os.path.join(target_dir, classification['target_filename'])
                            
                            target_path = self.organizer._get_unique_path(target_path)
                            os.makedirs(target_dir, exist_ok=True)
                            
                            import shutil
                            shutil.move(filepath, target_path)
                            self.log(f"Organizado ao vivo: {filename} -> {classification['target_folder']}")
                    except Exception as org_err:
                        self.log(f"Aviso na organização ao vivo: {org_err}", "DEBUG")
                # ---------------------------
                
                return True
            except Exception as e:
                self.log(f"Erro no download da capa (tentativa {attempt+1}): {e}", "WARNING")
            finally:
                if driver: driver.quit()
        return False
    
    def cancel(self):
        """Cancela o download de forma agressiva e fecha todos os drivers ativos"""
        self.is_cancelled = True
        self.log("CANCELAMENTO SOLICITADO PELO USUÁRIO. Interrompendo todos os navegadores...", "WARNING")
        
        # Criar uma cópia da lista para evitar problemas de modificação durante o loop
        drivers_to_quit = list(self.active_drivers)
        self.active_drivers = []
        
        for driver in drivers_to_quit:
            try:
                driver.quit()
            except:
                pass
