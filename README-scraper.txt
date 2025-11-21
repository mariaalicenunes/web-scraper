--> Discogs Data Scraper (Python/Selenium)

Um script de web scraping em Python projetado para extrair dados estruturados de artistas, discografias, faixas e metadados de álbuns do site Discogs.

Este projeto utiliza Selenium para navegação e interação com elementos dinâmicos (como aceitar cookies e aplicar filtros) e BeautifulSoup para a análise eficiente (parsing) do conteúdo HTML após o carregamento da página.

--> Funcionalidades

Extração Focada por Gênero: Filtra a busca inicial pelo gênero definido na configuração (GENRE_FILTER).

Raspagem Multi-Nível: Coleta dados em três níveis:

Lista de Artistas (da página de busca).

Detalhes do Artista (Membros, Sites).

Detalhes do Álbum (Gravadora, Gênero, Estilos e Tracklist).

Normalização de Dados: Aplica funções de limpeza para padronizar posições de faixas (e.g., A1 para 1).

Gerenciamento do WebDriver: Utiliza webdriver-manager para automatizar o download e a configuração do ChromeDriver.

Saída JSONL: Exporta os dados coletados em formato JSON Lines (.jsonl), ideal para processamento em Big Data, Machine Learning ou armazenamento em bancos de dados NoSQL.

--> Tecnologias Utilizadas

Python 3.x

Selenium: Automação de navegador.

BeautifulSoup 4: Parsing de HTML.

webdriver-manager: Gerenciamento de drivers de navegador.

logging: Sistema de log para acompanhamento da execução.

--> Pré-requisitos

Para rodar o script, você precisa ter o Google Chrome instalado no seu sistema.

1. Instalação de Dependências Python

Instale todas as bibliotecas necessárias usando pip:

pip install selenium beautifulsoup4 webdriver-manager


--> Configuração e Constantes

As seguintes constantes no início do script (discogs_scraper.py) controlam o comportamento e o volume de dados coletados. Edite-as conforme suas necessidades:

Constante

Descrição

Valor Padrão

MAX_ARTISTS

Número máximo de artistas a serem processados.

10

MAX_ALBUMS

Número máximo de álbuns processados por artista.

10

GENRE_FILTER

O gênero a ser filtrado na busca do Discogs (ex: "Rock", "Electronic").

"Rock"

OUTPUT_FILE

Nome do arquivo de saída no formato JSONL.

"dados_discogs.jsonl"

Nota: O script está atualmente configurado com options.add_argument("--headless=new") comentado. Para rodar o script sem abrir a janela do Chrome (modo headless), descomente esta linha.

--> Como Executar

Salve o código principal em um arquivo chamado discogs_scraper.py.

Ajuste as constantes no código conforme necessário.

Execute o script a partir do terminal:

python discogs_scraper.py


O script irá inicializar o Chrome, navegar, lidar com pop-ups de cookies e começar a processar os artistas e seus respectivos álbuns. O progresso será exibido no console via logging.

--> Fluxo de Raspagem

O processo de coleta segue um fluxo sequencial e hierárquico, garantindo que os dados do álbum estejam aninhados corretamente sob seus respectivos artistas:

Configuração: Inicializa o WebDriver e lida com pop-ups de cookies.

Busca: Navega para a página de busca do Discogs e aplica o filtro de GENRE_FILTER.

Lista de Artistas: Coleta os links de perfis dos artistas encontrados.

Loop do Artista: Para cada artista:

Raspa detalhes do artista (membros, sites).

Coleta a lista inicial de álbuns.

Loop do Álbum: Navega para a página de cada álbum e raspa (gravadora_album, genero_album, estilos_album, faixas_album).

Saída: Exporta o objeto final com artistas e suas discografias para o arquivo dados_discogs.jsonl.

--> Estrutura do Arquivo de Saída (JSONL)

O arquivo de saída (dados_discogs.jsonl) é um arquivo JSON Lines, onde cada linha é um objeto JSON completo representando um artista e toda a sua discografia coletada.

Exemplo de Linha (Artist Object):

{
    "id_artista": "b068c857-89c0-4824-a212-c21e05a5a9c3",
    "genero": "Rock",
    "nome_artista": "The Beatles",
    "membros_artista": ["John Lennon", "Paul McCartney", "George Harrison", "Ringo Starr"],
    "sites_artista": ["[https://www.thebeatles.com](https://www.thebeatles.com)", "[https://wikipedia.org/wiki/The_Beatles](https://wikipedia.org/wiki/The_Beatles)"],
    "albuns": [
        {
            "nome_album": "Abbey Road",
            "ano_lancamento": "1969",
            "gravadora_album": "Apple Records",
            "genero_album": ["Rock"],
            "estilos_album": ["Pop Rock", "Psychedelic Rock"],
            "faixas_album": [
                {
                    "numero_faixa": "1",
                    "nome_faixa": "Come Together",
                    "duracao_faixa": "4:20"
                },
                {
                    "numero_faixa": "2",
                    "nome_faixa": "Something",
                    "duracao_faixa": "3:03"
                }
            ]
        },
        // ... outros álbuns
    ]
}
