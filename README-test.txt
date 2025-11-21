--> Testes Unitários | Discogs Scraper Functions

Este repositório contém os testes unitários para as funções principais de raspagem (scraping) e processamento de dados da aplicação Discogs. O objetivo é garantir a integridade e a correta normalização dos dados extraídos, como posições de faixas, detalhes de artistas e metadados de álbuns.

Estrutura do Projeto

O arquivo de teste (test_discogs_scraper.py) é autônomo. Ele inclui as implementações das funções sob teste e a classe unittest, permitindo uma execução direta e desacoplada do código principal da aplicação.

--> Pré-requisitos

Para executar os testes com sucesso, o ambiente deve possuir:

Python 3.6+

BeautifulSoup 4 (Principal dependência externa para parsing de HTML).

--> Instalação de Dependências

Instale a biblioteca beautifulsoup4 através do pip:

pip install beautifulsoup4


--> Execução dos Testes

Siga os passos abaixo para iniciar a suíte de testes unitários.

1. Preparação do Ambiente

Certifique-se de que o arquivo de teste (test_discogs_scraper.py) está salvo no seu diretório de trabalho.

2. Comando de Execução

Execute o script diretamente a partir do terminal:

python test_discogs_scraper.py


--> Funções e Casos de Teste Verificados

A classe TestDiscogsScraperFunctions engloba a validação das seguintes lógicas:

Função

Descrição

Casos de Teste Principais

clean_track_position

Normaliza posições de faixas (e.g., "A1", "B", "10.") para inteiros representados como strings.

Posicionamento alfanumérico (A1 -> 1), letras singulares (B -> 2), e tratamento de valores nulos.

extract_artist_info

Coleta membros e URLs de sites de um perfil de artista/grupo.

Extração de múltiplos membros e verificação do retorno "Individual" para artistas solo.

extract_album_details

Extrai metadados do álbum, incluindo Gravadora, Gênero e Estilos.

Extração de dados com e sem links e manuseio de listas vazias.

extract_album_tracklist

Processa a lista de faixas, garantindo a ordenação correta e a limpeza da posição de cada faixa.

Validação da ordenação numérica (1, 2, 3) independentemente da ordem no HTML de entrada.

--> Interpretação dos Resultados

O módulo unittest exibe os resultados no terminal da seguinte forma:

Sucesso Total

-->Se todos os testes passarem, a saída será:

.......
----------------------------------------------------------------------
Ran 7 tests in 0.0XXs

OK


Cada ponto (.) representa a conclusão bem-sucedida de um método de teste.

Falha ou Erro

Em caso de problemas, a saída indicará o tipo de ocorrência:

F (Failure): O teste falhou devido a uma asserção violada (o resultado retornado não era o esperado).

E (Error): O teste encontrou um erro inesperado (exceção não tratada).

Exemplo de Falha (F):

.F.....
======================================================================
FAIL: test_clean_track_position_standard (__main__.TestDiscogsScraperFunctions.test_clean_track_position_standard)
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: '1' != '2'
...


Esta seção detalhará a asserção que falhou, auxiliando no processo de depuração.