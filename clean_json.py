# clean_json.py

import json

def clean_duplicate_movies(source_filename):
    """
    Lê um arquivo JSON de filmes, remove entradas com 'display_title' duplicado
    e salva o resultado em um novo arquivo.
    """
    try:
        print(f"Lendo o arquivo de origem: {source_filename}...")
        with open(source_filename, 'r', encoding='utf-8') as f:
            all_movies = json.load(f)
        
        original_count = len(all_movies)
        print(f"Total de filmes no arquivo original: {original_count}")

        # --- A Lógica da Limpeza ---
        # Usamos um dicionário para garantir a unicidade. As chaves de um dicionário
        # não podem se repetir. Usaremos o título do filme como chave.
        unique_movies = {}

        for movie in all_movies:
            # Pega o título de cada objeto de filme
            title = movie.get('display_title')
            
            if title:
                # Ao adicionar ao dicionário, se um título já existir como chave,
                # a entrada antiga é simplesmente sobrescrita. No final, teremos
                # apenas a última ocorrência de cada título.
                unique_movies[title] = movie
        
        # A nossa lista limpa são os valores do dicionário
        deduplicated_list = list(unique_movies.values())
        final_count = len(deduplicated_list)
        
        # --- Salvando o Resultado ---
        # Cria um novo nome de arquivo para a lista limpa
        clean_filename = source_filename.replace('.json', '_clean.json')
        
        print(f"Salvando {final_count} filmes únicos em '{clean_filename}'...")
        with open(clean_filename, 'w', encoding='utf-8') as f:
            json.dump(deduplicated_list, f, ensure_ascii=False, indent=2)

        print("\n-------------------------------------------------")
        print("Limpeza concluída com sucesso!")
        print(f"Filmes originais: {original_count}")
        print(f"Filmes únicos: {final_count}")
        print(f"Duplicatas removidas: {original_count - final_count}")
        print(f"Arquivo limpo salvo como: {clean_filename}")
        print("-------------------------------------------------")


    except FileNotFoundError:
        print(f"ERRO: O arquivo '{source_filename}' não foi encontrado. Verifique o nome e o local do arquivo.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


# --- Como Usar ---
# Coloque o nome do arquivo que você quer limpar aqui
# (o arquivo que foi gerado pelo script de scraping)
if __name__ == '__main__':
    # Altere o nome do arquivo aqui se for diferente
    file_to_clean = "popular_movies_2500.json" 
    clean_duplicate_movies(file_to_clean)