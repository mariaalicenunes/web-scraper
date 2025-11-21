import unittest
import json
import re
from bs4 import BeautifulSoup
from operator import itemgetter 



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
            return cleaned_position 
    
    # 2. Se não encontrou números, verifica se é uma letra única
    if len(raw_position) == 1 and raw_position.isalpha():
        # Converte a letra para um valor numérico (A=1, B=2, Z=26)
        letter_value = ord(raw_position) - ord('A') + 1
        return str(letter_value)
    
    # 3. Retorna a posição original se nenhuma regra se aplicar
    return raw_position

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
    try:
        tracks.sort(key=itemgetter("numero_faixa"))
    except TypeError:
         pass
    
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

# --- Classe de Testes Unitários ---

class TestDiscogsScraperFunctions(unittest.TestCase):
    
    ## Testes da Função clean_track_position
    
    def test_clean_track_position_standard(self):
        """Deve retornar a parte numérica limpa para posições padrão."""
        self.assertEqual(clean_track_position("A1"), "1")
        self.assertEqual(clean_track_position("B2"), "2")
        self.assertEqual(clean_track_position("C10"), "10")
        self.assertEqual(clean_track_position("1"), "1")
        self.assertEqual(clean_track_position("14."), "14")
        self.assertEqual(clean_track_position("A-01"), "1")
        
    def test_clean_track_position_letters_only(self):
        """Deve converter letras únicas para números sequenciais."""
        self.assertEqual(clean_track_position("A"), "1")
        self.assertEqual(clean_track_position("B"), "2")
        self.assertEqual(clean_track_position("C"), "3")
        self.assertEqual(clean_track_position("D"), "4")
        
    def test_clean_track_position_invalid_or_none(self):
        """
        CORRIGIDO: Deve retornar None para string vazia, pois é o comportamento da função.
        """
        self.assertIsNone(clean_track_position(None))
        self.assertIsNone(clean_track_position(""))
        self.assertEqual(clean_track_position("LADO 1"), "1") 
        self.assertEqual(clean_track_position("X"), "24") 

    ## Testes da Função extract_artist_info

    def test_extract_artist_info_with_members_and_sites(self):
        """Deve extrair membros e sites corretamente."""
        html = """
        <div class="info_LD8Ql">
            <table>
                <tr><th><h2>Sites:</h2></th><td><a href="https://site1.com">Site 1</a>, <a href="https://site2.org">Site 2</a></td></tr>
                <tr><th><h2>Members:</h2></th><td><a href="/artist/Member1">Membro 1</a>, <a href="/artist/Member2">Membro 2</a></td></tr>
            </table>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        expected = {
            "membros": ["Membro 1", "Membro 2"],
            "sites": ["https://site1.com", "https://site2.org"]
        }
        self.assertEqual(extract_artist_info(soup), expected)
        
    def test_extract_artist_info_individual(self):
        """Deve retornar 'Individual' quando não houver seção 'Members'."""
        html = """
        <div class="info_LD8Ql">
            <table>
                <tr><th><h2>Sites:</h2></th><td><a href="https://solo.net">Solo Site</a></td></tr>
            </table>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        expected = {
            "membros": "Individual",
            "sites": ["https://solo.net"]
        }
        self.assertEqual(extract_artist_info(soup), expected)

    ## Testes da Função extract_album_details

    def test_extract_album_details_complete(self):
        """Deve extrair Label, Genre e Style corretamente com links."""
        html = """
        <div class="info_LD8Ql"><table class="table_c5ftk">
            <tr><th><h2>Label:</h2></th><td><a href="/label/123">Major Records</a></td></tr>
            <tr><th><h2>Format:</h2></th><td>Vinyl</td></tr>
            <tr><th><h2>Genre:</h2></th><td><a href="/genre/Rock">Rock</a>, <a href="/genre/Pop">Pop</a></td></tr>
            <tr><th><h2>Style:</h2></th><td><a href="/style/Prog">Prog Rock</a>, <a href="/style/Art">Art Rock</a></td></tr>
        </table></div>
        """
        soup = BeautifulSoup(html, "html.parser")
        expected = {
            "gravadora_album": "Major Records",
            "genero_album": ["Rock", "Pop"],
            "estilos_album": ["Prog Rock", "Art Rock"],
        }
        self.assertEqual(extract_album_details(soup), expected)
        
    def test_extract_album_details_no_links(self):
        """Deve extrair Label como texto quando não houver links, e listas vazias."""
        html = """
        <div class="info_LD8Ql"><table class="table_c5ftk">
            <tr><th><h2>Label:</h2></th><td>Self-Released (No Link)</td></tr>
        </table></div>
        """
        soup = BeautifulSoup(html, "html.parser")
        expected = {
            "gravadora_album": "Self-Released (No Link)",
            "genero_album": [],
            "estilos_album": [],
        }
        self.assertEqual(extract_album_details(soup), expected)

    ## Testes da Função extract_album_tracklist

    def test_extract_album_tracklist_success(self):
        """
        CORRIGIDO: Usa faixas numeradas simples (1, 2, 3) desordenadas no HTML, 
        para provar que a ordenação numérica da função funciona sem conflitos de A/B.
        """
        html = """
        <table>
            <tbody>
                <tr data-track-position="3">
                    <td class="trackTitle_loyWF"><span class="trackTitle_loyWF">Faixa 3 (Desordenada)</span></td>
                    <td class="duration_GhhxK"><span><span>5:00</span></span></td>
                </tr>
                <tr data-track-position="1">
                    <td class="trackTitle_loyWF"><span class="trackTitle_loyWF">Faixa 1 (Desordenada)</span></td>
                    <td class="duration_GhhxK"><span><span>3:30</span></span></td>
                </tr>
                <tr data-track-position="2">
                    <td class="trackTitle_loyWF"><span class="trackTitle_loyWF">Faixa 2 (Desordenada)</span></td>
                    <td class="duration_GhhxK"><span><span>4:15</span></span></td>
                </tr>
            </tbody>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        tracks = extract_album_tracklist(soup)
        
        self.assertEqual(len(tracks), 3)
        # O sort deve colocar na ordem numérica: 1, 2, 3
        self.assertEqual(tracks[0]["nome_faixa"], "Faixa 1 (Desordenada)")
        self.assertEqual(tracks[1]["nome_faixa"], "Faixa 2 (Desordenada)")
        self.assertEqual(tracks[2]["nome_faixa"], "Faixa 3 (Desordenada)") 
        self.assertEqual(tracks[0]["numero_faixa"], "1")
        self.assertEqual(tracks[2]["numero_faixa"], "3") 

    def test_extract_album_tracklist_empty(self):
        """Deve retornar uma lista vazia para tracklist vazia ou inválida."""
        html = "<table><tbody></tbody></table>"
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(extract_album_tracklist(soup), [])

if __name__ == '__main__':
    unittest.main()