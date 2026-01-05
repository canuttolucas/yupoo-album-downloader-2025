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
import threading

class YupooSimpleCoverDownloader:
    def __init__(self, headless=True, log_callback=None):
        """
        Downloader simples que baixa apenas a capa do álbum
        
        Args:
            headless: Se True, executa sem interface gráfica
            log_callback: Função para enviar logs para a GUI
        """
        self.headless = headless
        self.output_dir = None
        self.lock = threading.Lock()
        self.log_callback = log_callback
        self.is_cancelled = False
        self.album_title = ""
    
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
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        
        # User agent para evitar bloqueios
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(3840, 2160)
        return driver
    
    def get_album_title(self, album_url):
        """
        Obtém o título do álbum
        
        Args:
            album_url: URL do álbum Yupoo
            
        Returns:
            Título do álbum
        """
        self.log(f"Obtendo título do álbum: {album_url}")
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
            
            return self.album_title
            
        except Exception as e:
            self.log(f"Erro ao obter título do álbum: {e}", "ERROR")
            return "Album_Sem_Titulo"
        finally:
            driver.quit()
    
    def download_cover_only(self, album_url):
        """
        Baixa apenas a capa do álbum (primeira imagem)
        
        Args:
            album_url: URL do álbum Yupoo
        """
        self.log("=" * 80)
        self.log("YUPOO SIMPLE COVER DOWNLOADER - Apenas Capa")
        self.log(f"URL do álbum: {album_url}")
        self.log("=" * 80)
        
        # Passo 0: Criar pasta específica para o álbum
        self.create_album_folder(album_url)
        
        # Passo 1: Obter título do álbum
        self.album_title = self.get_album_title(album_url)
        
        # Passo 2: Baixar apenas a primeira imagem (capa)
        self.log("Baixando capa do álbum...")
        driver = self.create_driver()
        
        try:
            driver.get(album_url)
            time.sleep(3)
            
            # Scroll para carregar as imagens
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
                    # Procura pelo primeiro elemento com data-id
                    first_image_element = driver.find_element(By.XPATH, "//div[@data-id][1]")
                    cover_data_id = first_image_element.get_attribute('data-id')
                    self.log(f"Usando fallback para primeira imagem - Data-ID: {cover_data_id}")
                except NoSuchElementException:
                    self.log("Nenhuma imagem encontrada no álbum!", "ERROR")
                    return

            # Passo 3: Baixar a imagem identificada
            # Extrai subdomain e uid da URL base
            url_parts = re.search(r'https://([^.]+)\.x\.yupoo\.com/albums/\d+(?:\?uid=(\d+))?', album_url)
            if url_parts:
                subdomain = url_parts.group(1)
                uid = url_parts.group(2) if url_parts.group(2) else "1"
            else:
                subdomain = "nfl-world"
                uid = "1"
            
            # Constrói a URL da imagem individual
            image_url = f"https://{subdomain}.x.yupoo.com/{cover_data_id}?uid={uid}"
            
            self.log(f"Abrindo imagem de capa: {image_url}")
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
                self.log("Elemento img não encontrado!", "ERROR")
                return
                
            # Aguarda a imagem carregar
            time.sleep(1)
            
            # Scroll até o elemento
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            
            # Captura screenshot do elemento específico
            screenshot = img_element.screenshot_as_png
            
            # Gera nome do arquivo baseado no título do álbum
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', self.album_title)
            filename = f"{safe_title}_CAPA.png"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot)
            
            self.log(f"CAPA salva: {filename}", "SUCCESS")
            self.log(f"Arquivo salvo em: {os.path.abspath(filepath)}")
                
        except Exception as e:
            self.log(f"Erro ao baixar capa: {e}", "ERROR")
        finally:
            driver.quit()
        
        self.log("=" * 80)
        self.log("Download da capa concluído!")
        self.log("=" * 80)
    
    def scroll_to_load_all(self, driver):
        """Faz scroll na página para carregar todas as imagens"""
        self.log("Fazendo scroll para carregar imagens...")
        
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
    
    def cancel(self):
        """Cancela o download"""
        self.is_cancelled = True
        self.log("Download cancelado pelo usuário", "WARNING")
