import csv

CUSTOM_CSS = """
    <style>
    /* Customize stChatMessage */
    .st-emotion-cache-1c7y2kd.ea2tk8x0 {
        background-color: #ffe0ec !important; /* Lighter pastel pink */
        color: #1f1f1f !important;           /* Dark text */
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Optional: Style chat text inside the message */
    .st-emotion-cache-1c7y2kd.ea2tk8x0 p {
        color: #1f1f1f !important;
    }
    </style>
"""

def create_pokemon_name_dict(key_col: int, val_col: int ) -> dict:
    with open('data/pokemon_data.csv', mode='r') as infile:
        reader = csv.reader(infile,delimiter='\t')
        next(reader, None)
        pokemon_name_dict = {rows[key_col]:rows[val_col] for rows in reader}
        # for row in reader:
        #     first_four_cols = row[:4]
        #     try:
        #         pokemon_name_dict[first_four_cols[key_col]] = first_four_cols[val_col]
        #     except IndexError as e:
        #         print(f"Error accessing index in first_four_cols: {e}, row: {row}, first_four_cols: {first_four_cols}, key_col: {key_col}, val_col: {val_col}")
        return pokemon_name_dict
    
def translate_pokemon_name(pokemon_name_dict: dict, pokemon_name: str) -> str:
    if pokemon_name in pokemon_name_dict:
        translated_name = pokemon_name_dict[pokemon_name]
    else:
        # If not found, the original name does not need to be translated.
        print("Not found")
        translated_name = pokemon_name
    
    return translated_name
"""
import csv

def create_pokemon_name_dict(key_col: int, val_col: int) -> dict:
    pokemon_name_dict = {}
    with open('data/pokemon_data.csv', mode='r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # skip header

        for i, row in enumerate(reader, start=2):  # start=2 for real line number
            limited_row = row[:4]  # read only the first 4 columns
            if len(limited_row) > max(key_col, val_col):
                key = limited_row[key_col].strip()
                val = limited_row[val_col].strip()
                pokemon_name_dict[key] = val
            else:
                print(f"⚠️ Skipping line {i}: Not enough columns → {row}")

    return pokemon_name_dict

"""