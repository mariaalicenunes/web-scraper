import time
import json
import uuid
import re
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from operator import itemgetter # Importar para facilitar a ordenação

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------
# CONFIGURAÇÃO & CONSTANTES
# ----------------------
MAX_ARTISTS = 10
MAX_ALBUMS = 10 
URL_BASE = "https://www.discogs.com"
URL_HOME = urljoin(URL_BASE, "pt_BR/")
URL_SEARCH = urljoin(URL_BASE, "pt_BR/search")
GENRE_FILTER = "Rock"
OUTPUT_FILE = "dados_discogs.jsonl"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ----------------------
# FUNÇÕES AUXILIARES
# ----------------------

def setup_driver():
    """Configura e inicializa o WebDriver do Chrome."""
    options = Options()
    #options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(300)
        return driver
    except Exception as e:
        logging.error(f"Falha ao configurar o driver: {e}")
        return None

def handle_initial_popups(driver, wait):
    """Lida com o aceite de cookies e outros popups iniciais."""
    driver.get(URL_HOME)
    time.sleep(2)

    # 1) Aceitar cookies
    try:
        accept_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_btn.click()
        logging.info("Cookies aceitos.")
    except Exception:
        logging.warning("Não foi possível clicar no botão de cookies ou ele não apareceu.")

    time.sleep(1)

    # 2) Fechar alerta
    try:
        close_alert = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.alert-message-close-icon"))
        )
        close_alert.click()
        logging.info("Alerta inicial fechado.")
    except Exception:
        logging.info("Nenhum alerta para fechar ou não foi possível fechar.")

    time.sleep(1)

def select_genre_and_get_artist_list(driver, wait):
    """Navega para a busca, seleciona o gênero e extrai a lista inicial de artistas."""
    driver.get(URL_SEARCH)
    time.sleep(2)
    logging.info(f"Navegando para: {driver.current_url}")

    # 3) Clicar no botão do gênero 
    try:
        genre_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{GENRE_FILTER}')]"))
        )
        genre_button.click()
        logging.info(f"Gênero **{GENRE_FILTER}** selecionado.")
    except TimeoutException:
        logging.error(f"Timeout ao tentar clicar no botão do gênero '{GENRE_FILTER}'.")
        return []
    except ElementClickInterceptedException:
        logging.error(f"Elemento de gênero interceptado. Tentando novamente...")
        time.sleep(3)
        genre_button.click()
    
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    artist_list_raw = []
    seen_artists = set()

    # Coleta inicial de artistas da página de busca
    cards = soup.select('div[role="listitem"].w-full.text-black')

    for card in cards:
        text_links = card.select("a.block.w-full.truncate.text-sm")

        # o link do artista é geralmente o segundo em 'text_links'
        artist_tag = text_links[1] if len(text_links) >= 2 else None
        artist_name = artist_tag.get_text(strip=True) if artist_tag else None
        
        if artist_name == "Various" or not artist_name or artist_name in seen_artists:
            continue
        
        artist_url = urljoin(URL_BASE, artist_tag["href"]) if artist_tag and artist_tag.has_attr("href") else None

        if artist_url:
            seen_artists.add(artist_name)
            artist_list_raw.append({
                "Nome_Artista": artist_name,
                "url_artista": artist_url,
            })
            if len(artist_list_raw) >= 5 * MAX_ARTISTS: # Coleta mais do que o necessário para ter margem
                break

    logging.info(f"Total de artistas encontrados na página de busca: {len(artist_list_raw)}")
    return artist_list_raw

# ----------------------
# FUNÇÕES DE WEB SCRAPING
# ----------------------

def extract_artist_info(soup):
    """Extrai informações do artista (membros, sites) da página do perfil."""
    artist_data = {"membros": "Individual", "sites": []}
    info_section = soup.select_one("div.info_LD8Ql")

    if info_section:
        for row in info_section.select("tr"):
            header = row.find("h2")
            td = row.find("td")
            if not header or not td:
                continue

            title = header.get_text(strip=True).rstrip(":")

            # Sites
            if title == "Sites":
                artist_data["sites"] = [a["href"] for a in td.find_all("a", href=True)]

            # Members
            elif title == "Members":
                members = [a.get_text(strip=True) for a in td.find_all("a")]
                artist_data["membros"] = members if members else "Individual"


    return artist_data

def clean_track_position(raw_position):
    """
    Remove todos os caracteres não numéricos de uma string de posição de faixa.
    Se a posição for apenas uma letra (ex: 'A', 'B'), converte para número ('1', '2').
    Ex: 'A1' -> '1', 'B2' -> '2', 'C10' -> '10', 'A' -> '1', 'B' -> '2'
    """
    if not raw_position:
        return None
    
    # Normaliza a string (remove espaços e torna maiúscula)
    raw_position = raw_position.strip().upper()
    
    # 1. Tenta encontrar dígitos
    numbers = re.findall(r'\d+', raw_position)
    
    if numbers:
        # Se encontrou números, usa o primeiro conjunto de dígitos (Ex: A10 -> 10)
        cleaned_position = "".join(numbers) 
        try:
            return str(int(cleaned_position))
        except ValueError:
            return cleaned_position # Se for um número muito grande, volta a string
    
    # 2. Se não encontrou números, verifica se é uma letra única
    if len(raw_position) == 1 and raw_position.isalpha():
        # Converte a letra para um valor numérico (A=1, B=2, Z=26)
        # Usa a tabela ASCII: ord('A') é 65.
        letter_value = ord(raw_position) - ord('A') + 1
        return str(letter_value)
    
    # 3. Retorna a posição original se nenhuma regra se aplicar
    return raw_position

def extract_album_tracklist(album_soup):
    """Extrai a lista de faixas, duração e posição do álbum."""
    tracks = []
    
    for tr in album_soup.select("tbody tr[data-track-position]"):
        raw_position = tr.get("data-track-position")
        
        # Chamada da função para limpar a posição
        position = clean_track_position(raw_position)

        # Título da faixa
        title_el = tr.select_one("td.trackTitle_loyWF span.trackTitle_loyWF")
        title_track = title_el.get_text(strip=True) if title_el else None

        # Duração
        dur_el = tr.select_one("td.duration_GhhxK span span")
        duration = dur_el.get_text(strip=True) if dur_el else None

        if position and title_track and duration:
            try:
                position_int = int(position) 
            except ValueError:
                position_int = position

            tracks.append({
                "numero_faixa": position_int, 
                "nome_faixa": title_track,
                "duracao_faixa": duration
            })
            
    # Garantir a ordenação por número da faixa
    tracks.sort(key=itemgetter("numero_faixa"))
    
    # Converte o 'numero_faixa' de volta para string para o output JSONL
    for track in tracks:
        track["numero_faixa"] = str(track["numero_faixa"])
        
    return tracks

def extract_album_details(album_soup):
    """Extrai gravadora, gênero e estilos da página do álbum."""
    album_info = {
        "gravadora_album": None,
        "genero_album": [],
        "estilos_album": [],
    }

    info_table = album_soup.select_one("div.info_LD8Ql table.table_c5ftk")
    if info_table:
        for tr in info_table.select("tr"):
            head_el = tr.select_one("th h2")
            value_td = tr.select_one("td")
            if not head_el or not value_td:
                continue

            field = head_el.get_text(strip=True).replace(":", "")

            # LABEL
            if field == "Label":
                label_links = [a.get_text(strip=True) for a in value_td.select("a")]
                if label_links:
                    album_info["gravadora_album"] = label_links[0]
                else:
                    album_info["gravadora_album"] = value_td.get_text(" ", strip=True)

            # GENRE
            elif field == "Genre":
                album_info["genero_album"] = [a.get_text(strip=True) for a in value_td.select("a")]

            # STYLE
            elif field == "Style":
                album_info["estilos_album"] = [a.get_text(strip=True) for a in value_td.select("a")]
                
    return album_info

def scrape_album_page(driver, album_url):
    """Navega e raspa detalhes e tracklist de um álbum."""
    try:
        driver.get(album_url)
    except TimeoutException:
        logging.warning(f"[TIMEOUT] Não consegui carregar o álbum: {album_url}")
        # Tentativa de interromper o carregamento lento
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
        return None

    time.sleep(1) 
    album_soup = BeautifulSoup(driver.page_source, "html.parser")
    
    tracks = extract_album_tracklist(album_soup)
    if not tracks:
        logging.info(f"Álbum ignorado (sem faixas válidas): {album_url}")
        return None
        
    album_details = extract_album_details(album_soup)
    
    return {
        "faixas_album": tracks,
        **album_details
    }

# ----------------------
# FLUXO PRINCIPAL
# ----------------------

def run_scraper():
    """Executa o fluxo completo de raspagem de dados."""
    driver = setup_driver()
    if not driver:
        return

    wait = WebDriverWait(driver, 10)
    
    try:
        handle_initial_popups(driver, wait)
        artist_list_raw = select_genre_and_get_artist_list(driver, wait)
        
        final_artists_data = []

        # 1. Iterar sobre a lista bruta de artistas
        for artist_item in artist_list_raw:
            if len(final_artists_data) >= MAX_ARTISTS:
                break

            artist_name = artist_item["Nome_Artista"]
            artist_url = artist_item["url_artista"]
            
            logging.info(f"\nProcessando artista: **{artist_name}**")

            if not artist_url:
                continue

            # 2. Coletar dados do artista e lista inicial de álbuns
            driver.get(artist_url)
            time.sleep(2)
            artist_soup = BeautifulSoup(driver.page_source, "html.parser")
            
            artist_info = extract_artist_info(artist_soup)
            
            # 3. Coleta inicial da lista de álbuns
            albums_raw = []
            seen_albums = set()
            
            # Tenta diferentes seletores para álbuns
            for row in artist_soup.select("tr.textWithCoversRow_Xv0h3")[:MAX_ALBUMS * 2]:
                
                if len(albums_raw) >= MAX_ALBUMS:
                    break

                # Link principal (capa)
                main_link = row.select_one("td:first-of-type a.link_wXY7O")
                if not main_link:
                    continue

                full_url = urljoin(URL_BASE, main_link.get("href", ""))

                # Título e Ano
                title_a = row.select_one("td.title_K9_iv a.link_wXY7O") or row.select_one("td.mobileStacked_Zbgf9 a.link_wXY7O")
                title = title_a.get_text(strip=True) if title_a else "UNKNOWN_TITLE"
                
                year_td = row.select_one("td.year_o3FNi")
                year = year_td.get_text(strip=True) if year_td else "UNKNOWN_YEAR"
                
                # Evitar duplicados no loop inicial
                key = (title, year)
                if key in seen_albums:
                    continue
                seen_albums.add(key)
                
                albums_raw.append({
                    "nome_album": title,
                    "url_album": full_url,
                    "ano_lancamento": year,
                })

            # 4. Navegar em cada álbum para coletar tracklist e detalhes
            discography = []
            for album_data_raw in albums_raw:
                if len(discography) >= MAX_ALBUMS:
                    break
                
                scraped_data = scrape_album_page(driver, album_data_raw["url_album"])
                
                if scraped_data:
                    final_album = {
                        # "id_album": str(uuid.uuid4()), <--- REMOVIDO CONFORME SOLICITADO
                        "nome_album": album_data_raw["nome_album"],
                        "ano_lancamento": album_data_raw["ano_lancamento"],
                        **scraped_data
                    }
                    discography.append(final_album)
            
            # 5. Adicionar artista final se tiver álbuns válidos
            if discography:
                artist_data = {
                    "id_artista": str(uuid.uuid4()), 
                    "genero": GENRE_FILTER, 
                    "nome_artista": artist_name,
                    "membros_artista": artist_info["membros"],
                    "sites_artista": artist_info["sites"],
                    "albuns": discography,
                }
                final_artists_data.append(artist_data)
                logging.info(f"Artista '{artist_name}' adicionado com **{len(discography)}** álbuns.")
            else:
                logging.warning(f"Artista '{artist_name}' ignorado (sem álbuns válidos).")

        # 6. Salvar em JSONL
        save_to_jsonl(final_artists_data)

    except Exception as e:
        logging.critical(f"Erro Crítico no fluxo principal: {e}", exc_info=True)
    finally:
        driver.quit()
        logging.info("Driver encerrado.")
        logging.info(f"Total de artistas coletados (com >=1 álbum): **{len(final_artists_data)}**")


def save_to_jsonl(data):
    """Salva a lista de dicionários no formato JSONL."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    logging.info(f"Dados salvos com sucesso no arquivo: **{OUTPUT_FILE}**")


if __name__ == "__main__":
    run_scraper()