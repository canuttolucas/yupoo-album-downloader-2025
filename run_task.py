from yupoo_advanced_downloader import YupooAdvancedDownloader
import os

def main():
    # URL provided by the user
    collection_url = "https://minkang.x.yupoo.com/collections/5062328"
    
    # Settings requested by the user:
    # - only the first page
    # - only the album cover
    page_option = 'first'
    
    print(f"Iniciando download da coleção: {collection_url}")
    print(f"Configurações: Pagina={page_option}, Apenas Capas")
    
    # Initialize the advanced downloader
    # headless=True is likely better for this environment
    downloader = YupooAdvancedDownloader(headless=True, max_workers=4)
    
    # Execute the download
    try:
        downloader.download_covers_from_collection(collection_url, page_option=page_option)
        print("\nTarefa finalizada com sucesso!")
    except Exception as e:
        print(f"\nOcorreu um erro durante a execução: {e}")

if __name__ == "__main__":
    main()
