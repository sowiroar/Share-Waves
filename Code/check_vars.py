import pandas as pd
import os

waves = ['Wave 4', 'Wave 5', 'Wave 6', 'Wave 7']
base_dir = r'C:\Users\eguen\Documents\Githubs-Redlat\Share\Waves'
modules = ['ph', 'br', 'mh', 'cf', 'gv_health', 'gv_isced', 'dn', 'cv_r']

for w in waves:
    w_dir = os.path.join(base_dir, w)
    if not os.path.exists(w_dir): continue
    print(f'--- {w} ---')
    files = os.listdir(w_dir)
    for mod in modules:
        mod_files = [f for f in files if f.endswith(f'_{mod}.dta')]
        if not mod_files:
            print(f'  Module {mod} not found.')
        else:
            try:
                df = pd.read_stata(os.path.join(w_dir, mod_files[0]), convert_categoricals=False, iterator=True)
                cols = df.variable_labels()
                print(f'  {mod}: {mod_files[0]} ({len(cols)} vars)')
            except Exception as e:
                print(f'  {mod}: Error {e}')
