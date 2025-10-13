import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import queue
import time
from yupoo_parallel_downloader import YupooParallelDownloader

class YupooDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yupoo Album Downloader 2025")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variáveis
        self.downloader = None
        self.is_downloading = False
        self.log_queue = queue.Queue()
        
        # Configurar estilo
        self.setup_styles()
        
        # Criar interface
        self.create_widgets()
        
        # Iniciar thread para logs
        self.start_log_thread()
        
        # Centralizar janela
        self.center_window()
    
    def setup_styles(self):
        """Configura estilos da interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar cores
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
    
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Yupoo Album Downloader 2025", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL
        ttk.Label(main_frame, text="URL:", style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Exemplos de URL
        examples_frame = ttk.LabelFrame(main_frame, text="Exemplos de URLs", padding="5")
        examples_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        examples_frame.columnconfigure(0, weight=1)
        
        examples_text = """Álbum: https://nfl-world.x.yupoo.com/albums/100300873?uid=1
Categoria: https://minkang.x.yupoo.com/categories/2890904
Collection: https://exemplo.x.yupoo.com/collections/123456"""
        
        ttk.Label(examples_frame, text=examples_text, font=('Consolas', 9)).grid(row=0, column=0, sticky=tk.W)
        
        # Configurações
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding="10")
        config_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        config_frame.columnconfigure(1, weight=1)
        
        # Threads
        ttk.Label(config_frame, text="Threads:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.threads_var = tk.IntVar(value=4)
        threads_spinbox = ttk.Spinbox(config_frame, from_=1, to=8, textvariable=self.threads_var, width=10)
        threads_spinbox.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Modo Headless
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(config_frame, text="Modo Headless (sem interface gráfica)", variable=self.headless_var)
        headless_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Pasta de destino
        ttk.Label(config_frame, text="Pasta de destino:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        output_frame = ttk.Frame(config_frame)
        output_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(output_frame, text="Procurar", command=self.browse_folder)
        browse_btn.grid(row=0, column=1)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.download_btn = ttk.Button(button_frame, text="Iniciar Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Parar", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="Limpar Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log de Execução", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def browse_folder(self):
        """Abre diálogo para selecionar pasta de destino"""
        folder = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if folder:
            self.output_dir_var.set(folder)
    
    def log_message(self, message, level="INFO"):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_queue.put(log_entry)
    
    def start_log_thread(self):
        """Inicia thread para processar logs"""
        def process_logs():
            while True:
                try:
                    message = self.log_queue.get(timeout=0.1)
                    self.log_text.insert(tk.END, message)
                    self.log_text.see(tk.END)
                    self.root.update_idletasks()
                except queue.Empty:
                    continue
                except:
                    break
        
        log_thread = threading.Thread(target=process_logs, daemon=True)
        log_thread.start()
    
    def validate_inputs(self):
        """Valida as entradas do usuário"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
            return False
        
        if not ("yupoo.com" in url and ("albums" in url or "categories" in url or "collections" in url)):
            messagebox.showerror("Erro", "URL inválida! Certifique-se de que é um link de álbum, categoria ou collection do Yupoo.")
            return False
        
        output_dir = self.output_dir_var.get().strip()
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino válida.")
            return False
        
        return True
    
    def start_download(self):
        """Inicia o download em uma thread separada"""
        if not self.validate_inputs():
            return
        
        if self.is_downloading:
            messagebox.showwarning("Aviso", "Download já em andamento!")
            return
        
        # Configurar interface
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Iniciando download...")
        
        # Limpar log
        self.clear_log()
        
        # Iniciar download em thread separada
        download_thread = threading.Thread(target=self.download_worker, daemon=True)
        download_thread.start()
    
    def download_worker(self):
        """Worker thread para o download"""
        try:
            # Criar downloader
            self.downloader = YupooParallelDownloader(
                headless=self.headless_var.get(),
                max_workers=self.threads_var.get()
            )
            
            # Mudar para pasta de destino
            original_dir = os.getcwd()
            os.chdir(self.output_dir_var.get())
            
            url = self.url_var.get().strip()
            
            # Detectar tipo de URL e executar
            if "categories" in url:
                self.log_message("Detectado: URL de categoria")
                self.status_var.set("Processando categoria...")
                self.downloader.download_category(url)
            elif "collections" in url:
                self.log_message("Detectado: URL de collection")
                self.status_var.set("Processando collection...")
                self.downloader.download_collection(url)
            else:
                self.log_message("Detectado: URL de álbum")
                self.status_var.set("Processando álbum...")
                self.downloader.download_album(url)
            
            # Voltar para diretório original
            os.chdir(original_dir)
            
            if self.is_downloading:  # Se não foi cancelado
                self.log_message("Download concluído com sucesso!", "SUCCESS")
                self.status_var.set("Download concluído!")
                messagebox.showinfo("Sucesso", "Download concluído com sucesso!")
            
        except Exception as e:
            self.log_message(f"Erro durante o download: {str(e)}", "ERROR")
            self.status_var.set("Erro durante o download")
            messagebox.showerror("Erro", f"Erro durante o download:\n{str(e)}")
        
        finally:
            # Restaurar interface
            self.is_downloading = False
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            if self.status_var.get() == "Iniciando download...":
                self.status_var.set("Pronto")
    
    def stop_download(self):
        """Para o download"""
        if self.is_downloading:
            self.is_downloading = False
            self.log_message("Parando download...", "WARNING")
            self.status_var.set("Parando download...")
            # Note: O download não pode ser interrompido facilmente devido ao Selenium
            # Mas a interface será restaurada quando a thread terminar
    
    def clear_log(self):
        """Limpa o log"""
        self.log_text.delete(1.0, tk.END)
    
    def on_closing(self):
        """Chamado quando a janela é fechada"""
        if self.is_downloading:
            if messagebox.askokcancel("Sair", "Download em andamento. Deseja realmente sair?"):
                self.is_downloading = False
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """Função principal"""
    root = tk.Tk()
    app = YupooDownloaderGUI(root)
    
    # Configurar fechamento da janela
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Iniciar aplicação
    root.mainloop()

if __name__ == "__main__":
    main()
