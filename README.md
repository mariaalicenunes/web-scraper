--> Discogs Data Scraper & Testes Unitários

Esta solução unificada compreende um script de web scraping em Python projetado para extrair dados estruturados do Discogs e um conjunto de testes unitários para garantir a integridade do processamento de dados.

O projeto principal utiliza Selenium para navegação e interação com elementos dinâmicos (como aceitar cookies) e BeautifulSoup para a análise eficiente (parsing) do conteúdo HTML. O módulo de testes valida as funções críticas de limpeza e normalização.

--> Funcionalidades do Scraper

Extração Focada por Gênero: Filtra a busca inicial pelo gênero definido na configuração (GENRE_FILTER).

Raspagem Multi-Nível: Coleta dados em três níveis:
- Lista de Artistas (da página de busca).
- Detalhes do Artista (Membros, Sites).
- Detalhes do Álbum (Gravadora, Gênero, Estilos e Tracklist).

Normalização de Dados: Aplica funções de limpeza para padronizar posições de faixas (e.g., A1 para 1).

Gerenciamento do WebDriver: Utiliza webdriver-manager para automatizar o download e a configuração do ChromeDriver.

Saída JSONL: Exporta os dados coletados em formato JSON Lines (.jsonl), ideal para processamento em Big Data e Machine Learning.

--> Tecnologias Utilizadas

Python 3.x
Selenium: Automação de navegador.
BeautifulSoup 4: Parsing de HTML.
webdriver-manager: Gerenciamento de drivers de navegador.
logging: Sistema de log para acompanhamento da execução.
unittest: Framework nativo para execução dos testes.

--> Pré-requisitos e Instalação

Para rodar a solução completa, você precisa ter o Google Chrome instalado no seu sistema.

1. Instalação de Dependências Python

Instale todas as bibliotecas necessárias (para o scraper e testes) usando pip:

pip install selenium beautifulsoup4 webdriver-manager

--> Configuração do Scraper

As seguintes constantes no início do script (discogs_scraper.py) controlam o comportamento e o volume de dados coletados. Edite-as conforme suas necessidades:

| Constante | Descrição | Valor Padrão |
| :--- | :--- | :--- |
| MAX_ARTISTS | Número máximo de artistas a serem processados. | 10 |
| MAX_ALBUMS | Número máximo de álbuns processados por artista. | 10 |
| GENRE_FILTER | O gênero a ser filtrado na busca do Discogs. | "Rock" |
| OUTPUT_FILE | Nome do arquivo de saída no formato JSONL. | "dados_discogs.jsonl" |

Nota: O script está atualmente configurado com options.add_argument("--headless=new") comentado. Para rodar sem abrir a janela do Chrome, descomente esta linha.

--> Como Executar

1. Executando o Scraper

Salve o código principal em um arquivo chamado discogs_scraper.py e execute:

python discogs_scraper.py

O script irá inicializar o Chrome, navegar, lidar com pop-ups e processar os dados. O progresso será exibido no console.

2. Executando os Testes Unitários

Salve o código de testes em um arquivo chamado test_discogs_scraper.py no mesmo diretório e execute:

python test_discogs_scraper.py

Isso validará as funções de limpeza de faixas, extração de artistas e processamento de álbuns.

--> Fluxo de Raspagem (Scraper)

O processo segue um fluxo sequencial e hierárquico:

Configuração: Inicializa o WebDriver e lida com pop-ups de cookies.
Busca: Navega para a página de busca do Discogs e aplica o filtro de GENRE_FILTER.
Lista de Artistas: Coleta os links de perfis dos artistas encontrados.
Loop do Artista: Raspa detalhes (membros, sites) e coleta a lista de álbuns.
Loop do Álbum: Navega para a página de cada álbum e raspa metadados e faixas.
Saída: Exporta o objeto final para dados_discogs.jsonl.

--> Estrutura do Arquivo de Saída (JSONL)

O arquivo gerado contém objetos JSON completos representando um artista e sua discografia.

Exemplo de Linha:

{
    "id_artista": "b068c857-89c0-4824-a212-c21e05a5a9c3",
    "genero": "Rock",
    "nome_artista": "The Beatles",
    "membros_artista": ["John Lennon", "Paul McCartney", "George Harrison", "Ringo Starr"],
    "sites_artista": ["https://www.thebeatles.com", "https://wikipedia.org/wiki/The_Beatles"],
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
                }
            ]
        }
    ]
}

--> Cobertura dos Testes Unitários

A classe TestDiscogsScraperFunctions engloba a validação das seguintes lógicas críticas:

| Função | Descrição | Casos de Teste Principais |
| :--- | :--- | :--- |
| clean_track_position | Normaliza posições de faixas para inteiros. | Posicionamento alfanumérico (A1 -> 1), letras (B -> 2), valores nulos. |
| extract_artist_info | Coleta membros e URLs de sites. | Extração de múltiplos membros e verificação de "Individual" para solo. |
| extract_album_details | Extrai metadados do álbum. | Extração com e sem links, listas vazias. |
| extract_album_tracklist | Processa a lista de faixas e ordenação. | Validação da ordenação numérica (1, 2, 3) independente do HTML. |

--> Interpretação dos Resultados dos Testes

Sucesso Total:
.......
----------------------------------------------------------------------
Ran 7 tests in 0.0XXs
OK

Falha (F) ou Erro (E):
A saída indicará qual asserção falhou (AssertionError) ou qual erro inesperado ocorreu, facilitando a depuração das funções de parsing.