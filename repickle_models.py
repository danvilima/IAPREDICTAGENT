import pickle
import os

files = [
    'models/modelo_poisson_casa.pkl',
    'models/modelo_poisson_visitante.pkl',
    'models/colunas_atributos.pkl'
]

for file in files:
    if os.path.exists(file):
        try:
            with open(file, 'rb') as f:
                obj = pickle.load(f)
            with open(file, 'wb') as f:
                pickle.dump(obj, f, protocol=4)
            print(f"Successfully re-pickled {file} with protocol 4.")
        except Exception as e:
            print(f"Error processing {file}: {e}")
    else:
        print(f"File not found: {file}")
