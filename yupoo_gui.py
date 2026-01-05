import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import sys
import queue
import time
from yupoo_gui_downloader import YupooGUIDownloader
from yupoo_advanced_downloader import YupooAdvancedDownloader
from yupoo_simple_cover_downloader import YupooSimpleCoverDownloader
from photo_organizer import PhotoOrganizer
from packaging import version

# Set appearance mode and default color theme
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class YupooDownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Yupoo Album Downloader 2025 - Modern Edition")
        self.geometry("900x700")
        self.resizable(True, True)
        
        # Variáveis de Estado
        self.downloader = None
        self.is_downloading = False
        self.log_queue = queue.Queue()
        self.status_var = tk.StringVar(value="Pronto")
        
        # Configurar Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Criar Sidebar
        self.create_sidebar()
        
        # Criar Frame Principal
        self.create_main_frame()
        
        # Iniciar thread para logs
        self.start_log_thread()
        
        # Center Window
        self.center_window()
        
        # Protocolo para fechar tudo ao fechar a janela (X)
        self.protocol("WM_DELETE_WINDOW", self.stop_download)
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Yupoo\nDownloader", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Botão Organizar Fotos
        self.organize_button = ctk.CTkButton(self.sidebar_frame, text="Organizar Fotos", command=self.open_organize_dialog, fg_color="#2E7D32", hover_color="#1B5E20")
        self.organize_button.grid(row=1, column=0, padx=20, pady=(10, 5))
        
        self.label_mode = ctk.CTkLabel(self.sidebar_frame, text="Tema:", anchor="w")
        self.label_mode.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))

    def create_main_frame(self):
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # --- URL Input (Multi-line for batch) ---
        self.url_frame = ctk.CTkFrame(self.main_frame)
        self.url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.url_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.url_frame, text="URLs do Yupoo (uma por linha, máx. 20):").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.url_textbox = ctk.CTkTextbox(self.url_frame, height=100)
        self.url_textbox.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # --- OpenAI API Key ---
        self.api_frame = ctk.CTkFrame(self.main_frame)
        self.api_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.api_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.api_frame, text="OpenAI API Key (opcional):").grid(row=0, column=0, padx=10, pady=10)
        self.api_key_entry = ctk.CTkEntry(self.api_frame, placeholder_text="sk-...", show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        
        # --- Pasta de Destino ---
        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.output_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.output_frame, text="Salvar em:").grid(row=0, column=0, padx=10, pady=10)
        self.output_dir_entry = ctk.CTkEntry(self.output_frame)
        self.output_dir_entry.insert(0, os.getcwd())
        self.output_dir_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        self.browse_btn = ctk.CTkButton(self.output_frame, text="Selecionar Pasta", command=self.browse_folder, width=100)
        self.browse_btn.grid(row=0, column=2, padx=(0, 10), pady=10)
        
        # --- Opções Avançadas ---
        self.advanced_frame = ctk.CTkFrame(self.main_frame)
        self.advanced_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.advanced_frame.grid_columnconfigure(0, weight=1)
        
        self.use_advanced_chk = ctk.CTkCheckBox(self.advanced_frame, text="Usar Funcionalidades Avançadas (Recomendado)", onvalue=True, offvalue=False)
        self.use_advanced_chk.select() # Default ON
        self.use_advanced_chk.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Opções de Threads
        self.thread_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        self.thread_frame.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(self.thread_frame, text="Threads (Paralelismo):").pack(side="left", padx=(0, 10))
        self.threads_slider = ctk.CTkSlider(self.thread_frame, from_=1, to=10, number_of_steps=9)
        self.threads_slider.set(10)
        self.threads_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # Headless
        self.headless_chk = ctk.CTkCheckBox(self.advanced_frame, text="Modo Headless (Esconder Navegador)", onvalue=True, offvalue=False)
        self.headless_chk.select()
        self.headless_chk.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # --- Opções de Coleção/Álbum ---
        self.collection_options_frame = ctk.CTkFrame(self.main_frame, border_width=1, border_color="gray50")
        self.collection_options_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.collection_options_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.collection_options_frame, text="Opções de Coleção / Álbum", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Modo de Coleção
        self.coll_mode_label = ctk.CTkLabel(self.collection_options_frame, text="Modo Coleção:")
        self.coll_mode_label.grid(row=1, column=0, sticky="w", padx=10)
        self.collection_mode_var = ctk.StringVar(value="covers")
        self.radio_coll_covers = ctk.CTkRadioButton(self.collection_options_frame, text="Só Capas (HQ)", variable=self.collection_mode_var, value="covers")
        self.radio_coll_covers.grid(row=2, column=0, sticky="w", padx=20, pady=2)
        self.radio_coll_full = ctk.CTkRadioButton(self.collection_options_frame, text="Álbuns Completos", variable=self.collection_mode_var, value="albums")
        self.radio_coll_full.grid(row=3, column=0, sticky="w", padx=20, pady=2)

        # Opções de Página
        ctk.CTkLabel(self.collection_options_frame, text="Paginação:").grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))
        self.page_option_var = ctk.StringVar(value="all")
        
        self.page_opts_frame = ctk.CTkFrame(self.collection_options_frame, fg_color="transparent")
        self.page_opts_frame.grid(row=5, column=0, sticky="w", padx=10)
        
        ctk.CTkRadioButton(self.page_opts_frame, text="Primeira", variable=self.page_option_var, value="first").pack(side="left", padx=10)
        ctk.CTkRadioButton(self.page_opts_frame, text="Todas", variable=self.page_option_var, value="all").pack(side="left", padx=10)
        ctk.CTkRadioButton(self.page_opts_frame, text="Intervalo", variable=self.page_option_var, value="range").pack(side="left", padx=10)
        
        self.range_frame = ctk.CTkFrame(self.collection_options_frame, fg_color="transparent")
        self.range_frame.grid(row=6, column=0, sticky="w", padx=30, pady=2)
        ctk.CTkLabel(self.range_frame, text="De:").pack(side="left")
        self.page_start = ctk.CTkEntry(self.range_frame, width=50)
        self.page_start.insert(0, "1")
        self.page_start.pack(side="left", padx=5)
        ctk.CTkLabel(self.range_frame, text="Até:").pack(side="left")
        self.page_end = ctk.CTkEntry(self.range_frame, width=50)
        self.page_end.insert(0, "1")
        self.page_end.pack(side="left", padx=5)

        # --- Botões de Ação ---
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, pady=20)
        
        self.start_btn = ctk.CTkButton(self.action_frame, text="INICIAR DOWNLOAD", command=self.start_download, width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(self.action_frame, text="PARAR", command=self.stop_download, width=100, height=40, fg_color="darkred", hover_color="maroon", state="disabled")
        self.stop_btn.pack(side="left", padx=10)
        
        self.restart_btn = ctk.CTkButton(self.action_frame, text="REINICIAR", command=self.hard_restart, width=100, height=40, fg_color="gray30", hover_color="gray20")
        self.restart_btn.pack(side="left", padx=10)

        # --- Log e Status ---
        self.status_label = ctk.CTkLabel(self.main_frame, textvariable=self.status_var, font=ctk.CTkFont(size=13, weight="bold"))
        self.status_label.grid(row=5, column=0, sticky="w", padx=10, pady=(10, 0))
        
        # Barra de Progresso do Link Atual (Álbuns/Imagens)
        self.progress_label_link = ctk.CTkLabel(self.main_frame, text="Progresso do Link Atual: 0%")
        self.progress_label_link.grid(row=6, column=0, sticky="w", padx=10)
        self.progressbar_link = ctk.CTkProgressBar(self.main_frame)
        self.progressbar_link.grid(row=7, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.progressbar_link.set(0)
        
        # Barra de Progresso Geral (Batch)
        self.progress_label_batch = ctk.CTkLabel(self.main_frame, text="Progresso Geral (Links): 0%")
        self.progress_label_batch.grid(row=8, column=0, sticky="w", padx=10)
        self.progressbar_batch = ctk.CTkProgressBar(self.main_frame, progress_color="#2E7D32")
        self.progressbar_batch.grid(row=9, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.progressbar_batch.set(0)

        self.log_box = ctk.CTkTextbox(self.main_frame, height=200)
        self.log_box.grid(row=10, column=0, sticky="ew", padx=10, pady=10)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir_entry.get())
        if folder:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, folder)
            
    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {level}: {message}\n")

    def start_log_thread(self):
        def process_logs():
            while True:
                try:
                    message = self.log_queue.get(timeout=0.1)
                    self.log_box.insert("end", message)
                    self.log_box.see("end")
                except queue.Empty:
                    continue
                except:
                    break
        threading.Thread(target=process_logs, daemon=True).start()

    def validate_inputs(self):
        urls_text = self.url_textbox.get("1.0", "end").strip()
        if not urls_text:
            self.log_message("Erro: Nenhuma URL informada.", "ERROR")
            return False
        
        # Validar quantidade máxima
        urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
        if len(urls) > 20:
            self.log_message("Erro: Máximo de 20 URLs permitidas.", "ERROR")
            return False
            
        # Range validation
        if self.page_option_var.get() == "range":
            try:
                start = int(self.page_start.get())
                end = int(self.page_end.get())
                if start < 1 or end < start:
                    raise ValueError
            except ValueError:
                self.log_message("Erro: Intervalo de páginas inválido.", "ERROR")
                return False

        return True

    def start_download(self):
        if not self.validate_inputs():
            return
            
        self.is_downloading = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Resetar barras
        self.progressbar_link.set(0)
        self.progress_label_link.configure(text="Progresso do Link Atual: 0%")
        self.progressbar_batch.set(0)
        self.progress_label_batch.configure(text="Progresso Geral (Links): 0%")
        
        self.log_box.delete("1.0", "end")
        self.status_var.set("Iniciando...")
        
        threading.Thread(target=self.download_worker, daemon=True).start()

    def update_link_progress(self, current, total):
        """Atualiza a barra de progresso do link atual"""
        if total > 0:
            percentage = min(1.0, current / total)
            self.progressbar_link.set(percentage)
            self.progress_label_link.configure(text=f"Progresso do Link Atual: {int(percentage * 100)}%")
        else:
            self.progressbar_link.set(0)
            self.progress_label_link.configure(text="Progresso do Link Atual: 0%")
        self.update_idletasks()

    def update_batch_progress(self, current, total):
        """Atualiza a barra de progresso geral (batch)"""
        if total > 0:
            percentage = min(1.0, current / total)
            self.progressbar_batch.set(percentage)
            self.progress_label_batch.configure(text=f"Progresso Geral (Links): {int(percentage * 100)}% ({current}/{total})")
        else:
            self.progressbar_batch.set(0)
            self.progress_label_batch.configure(text="Progresso Geral (Links): 0%")
        self.update_idletasks()

    def stop_download(self):
        self.log_message("CANCELAMENTO TOTAL. FECHANDO TUDO...", "WARNING")
        if self.downloader:
            self.downloader.cancel()
        self.is_downloading = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progressbar_link.set(0)
        self.progressbar_batch.set(0)
        os._exit(0)

    def hard_restart(self):
        """Reinicia o processo completamente"""
        self.log_message("Reiniciando aplicação...", "WARNING")
        try:
            if self.downloader:
                self.downloader.cancel()
        except: pass
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def download_worker(self):
        original_cwd = os.getcwd()
        try:
            # Ler URLs do textbox (batch)
            urls_text = self.url_textbox.get("1.0", "end").strip()
            urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
            
            use_advanced = self.use_advanced_chk.get() == 1
            max_workers = int(self.threads_slider.get())
            headless = self.headless_chk.get() == 1
            output_dir = self.output_dir_entry.get()
            api_key = self.api_key_entry.get().strip() if hasattr(self, 'api_key_entry') else None

            collection_mode = self.collection_mode_var.get()
            page_opt = self.page_option_var.get()
            
            page_conf = "all"
            if page_opt == "first":
                page_conf = "first"
            elif page_opt == "range":
                try:
                    s = int(self.page_start.get())
                    e = int(self.page_end.get())
                    page_conf = (s, e)
                except: 
                    page_conf = "all"

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            os.chdir(output_dir)

            total_urls = len(urls)
            self.log_message(f"=== PROCESSANDO {total_urls} URL(s) ===")

            for idx, url in enumerate(urls, 1):
                if not self.is_downloading:
                    self.log_message("Download cancelado pelo usuário.", "WARNING")
                    break
                    
                self.update_batch_progress(idx - 1, total_urls)
                self.update_link_progress(0, 100) # Reset link bar for new link
                
                self.log_message(f"\n[{idx}/{total_urls}] Processando: {url}")
                self.status_var.set(f"Baixando {idx}/{total_urls}")

                # Limpar downloader anterior se existir para liberar recursos
                if self.downloader:
                    self.log_message("Limpando recursos do link anterior...", "DEBUG")
                    if hasattr(self.downloader, 'close'):
                        self.downloader.close()
                    self.downloader = None
                    import gc
                    gc.collect()

                if use_advanced or "collections" in url or "categories" in url:
                    self.downloader = YupooAdvancedDownloader(
                        headless=headless,
                        max_workers=max_workers,
                        log_callback=self.log_message,
                        openai_api_key=api_key
                    )
                    
                    if "collections" in url or "categories" in url:
                        if collection_mode == "covers":
                            self.downloader.download_covers_from_collection(url, page_conf, progress_callback=self.update_link_progress)
                        else:
                            self.downloader.download_albums_from_collection(url, page_conf, progress_callback=self.update_link_progress)
                            
                    elif "albums" in url:
                        self.downloader.download_album_advanced(url, "all", None, progress_callback=self.update_link_progress)
                        
                else:
                    self.downloader = YupooGUIDownloader(
                        headless=headless,
                        max_workers=max_workers,
                        log_callback=self.log_message
                    )
                    # Adicionar progresso ao downloader antigo se necessário, 
                    # mas o foco é no Advanced que o user usa mais
                    if "collections" in url:
                        self.downloader.download_collection(url)
                    elif "categories" in url:
                        self.downloader.download_category(url)
                    else:
                        self.downloader.download_album(url)
                
                self.update_link_progress(100, 100) # Finaliza a barra do link

            self.update_batch_progress(total_urls, total_urls)
            self.log_message(f"\n=== TODAS AS {total_urls} URL(s) PROCESSADAS! ===", "SUCCESS")
            self.status_var.set("Finalizado")

        except Exception as e:
            self.log_message(f"Erro Crítico: {e}", "ERROR")
        finally:
            os.chdir(original_cwd)
            self.is_downloading = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.progressbar_link.set(0)
            self.progressbar_batch.set(0)

    def open_organize_dialog(self):
        """Abre o diálogo para organizar fotos de futebol"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Organizar Fotos de Futebol")
        dialog.geometry("600x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # Variáveis
        source_var = tk.StringVar()
        dest_var = tk.StringVar()
        
        # Título
        title_label = ctk.CTkLabel(dialog, text="Organizador de Camisas de Futebol", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        desc_label = ctk.CTkLabel(dialog, text="Classifica e organiza fotos por Clube/Liga/Temporada", font=ctk.CTkFont(size=12))
        desc_label.pack(pady=(0, 20))
        
        # Frame de seleção de pastas
        folders_frame = ctk.CTkFrame(dialog)
        folders_frame.pack(fill="x", padx=20, pady=10)
        
        # Pasta de origem
        ctk.CTkLabel(folders_frame, text="Pasta de Origem (fotos baixadas):").pack(anchor="w", padx=10, pady=(10, 0))
        source_frame = ctk.CTkFrame(folders_frame)
        source_frame.pack(fill="x", padx=10, pady=5)
        source_entry = ctk.CTkEntry(source_frame, textvariable=source_var, width=400)
        source_entry.pack(side="left", padx=(0, 10))
        ctk.CTkButton(source_frame, text="Selecionar", width=80, 
                      command=lambda: source_var.set(filedialog.askdirectory(title="Selecione a pasta de origem"))).pack(side="left")
        
        # Pasta de destino
        ctk.CTkLabel(folders_frame, text="Pasta de Destino (estrutura organizada):").pack(anchor="w", padx=10, pady=(10, 0))
        dest_frame = ctk.CTkFrame(folders_frame)
        dest_frame.pack(fill="x", padx=10, pady=5)
        dest_entry = ctk.CTkEntry(dest_frame, textvariable=dest_var, width=400)
        dest_entry.pack(side="left", padx=(0, 10))
        ctk.CTkButton(dest_frame, text="Selecionar", width=80,
                      command=lambda: dest_var.set(filedialog.askdirectory(title="Selecione a pasta de destino"))).pack(side="left")
        
        # Log de progresso
        log_frame = ctk.CTkFrame(dialog)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(log_frame, text="Progresso:").pack(anchor="w", padx=10, pady=(10, 0))
        log_text = ctk.CTkTextbox(log_frame, height=150)
        log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def log_to_dialog(message, level="INFO"):
            log_text.insert("end", f"[{level}] {message}\n")
            log_text.see("end")
            dialog.update_idletasks()
        
        def run_organizer():
            source = source_var.get()
            dest = dest_var.get()
            
            if not source or not dest:
                log_to_dialog("Por favor, selecione ambas as pastas!", "ERROR")
                return
            
            log_to_dialog(f"Iniciando organização...")
            log_to_dialog(f"Origem: {source}")
            log_to_dialog(f"Destino: {dest}")
            
            try:
                organizer = PhotoOrganizer(log_callback=log_to_dialog)
                stats = organizer.organize_folder(source, dest)
                log_to_dialog(f"\n=== CONCLUÍDO ===", "SUCCESS")
                log_to_dialog(f"Arquivos processados: {stats['processed']}", "SUCCESS")
                log_to_dialog(f"Arquivos movidos: {stats['moved']}", "SUCCESS")
            except Exception as e:
                log_to_dialog(f"Erro: {e}", "ERROR")
        
        # Botões de ação
        action_frame = ctk.CTkFrame(dialog)
        action_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(action_frame, text="Organizar", command=run_organizer, fg_color="#2E7D32", hover_color="#1B5E20").pack(side="left", padx=10)
        ctk.CTkButton(action_frame, text="Fechar", command=dialog.destroy, fg_color="gray").pack(side="right", padx=10)

if __name__ == "__main__":
    app = YupooDownloaderGUI()
    app.mainloop()
