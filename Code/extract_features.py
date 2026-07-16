import os
import pandas as pd
import glob
import numpy as np

# Path configuration (Paths relative to the directory where the script is executed)
base_dir = '.'
waves_dir = os.path.join(base_dir, 'Waves')
data_processed_dir = os.path.join(base_dir, 'Data_Processed')
results_dir = os.path.join(base_dir, 'Results')

os.makedirs(data_processed_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

# Variables of interest grouped by module (based on SHARE)
variables_of_interest = {
    'gv_health': ['mergeid', 'bmi', 'casp', 'sphus', 'adl', 'iadl', 'mobility', 'chronic'],
    'ph': ['mergeid', 'ph006d1', 'ph006d2', 'ph006d5', 'ph048_', 'ph049_', 'ph042_'],
    'br': ['mergeid', 'br001_', 'br010_', 'br015_', 'br016_'],
    'mh': ['mergeid', 'mh002_', 'mh003_', 'eurod'],
    'cf': ['mergeid', 'cf008tot', 'cf016_', 'cf018_', 'cf001_', 'cf002_'],
    'gv_isced': ['mergeid', 'isced1997_r', 'isced2011_r'],
    'cv_r': ['mergeid', 'age_int', 'gender']
}

def process_wave(wave_name, rel_version='rel8-0-0'):
    wave_folder = os.path.join(waves_dir, wave_name)
    if not os.path.exists(wave_folder):
        print(f"Folder {wave_name} does not exist. Skipping.")
        return
    
    print(f"Processing {wave_name}...")
    wave_df = None
    
    # Process each module
    for module, cols in variables_of_interest.items():
        # Look for the file corresponding to the module
        pattern = os.path.join(wave_folder, f"sharew*_{rel_version}_{module}.dta")
        files = glob.glob(pattern)
        
        if not files:
            print(f"  Warning: No file found for module '{module}' in {wave_name}.")
            continue
            
        file_path = files[0]
        try:
            # Read the Stata file
            df_mod = pd.read_stata(file_path, convert_categoricals=False)
            
            # Select only the columns that exist in this file
            existing_cols = [c for c in cols if c in df_mod.columns]
            df_mod = df_mod[existing_cols]
            
            # SHARE BUSINESS RULE: 
            # "define missing values as all values smaller than 0 for all variables except financial amounts."
            # Since we have no financial amounts, any value < 0 is null (-1 don't know, -2 refusal, -99 missing by design, etc.)
            for col in existing_cols:
                if col != 'mergeid':
                    # Apply mask for negative values and convert them to NaN
                    df_mod.loc[df_mod[col] < 0, col] = np.nan
            
            # Merge with the main dataframe
            if wave_df is None:
                wave_df = df_mod
            else:
                wave_df = pd.merge(wave_df, df_mod, on='mergeid', how='outer')
                
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            
    if wave_df is not None:
        # Save processed data
        output_file = os.path.join(data_processed_dir, f"{wave_name.replace(' ', '')}_processed.csv")
        wave_df.to_csv(output_file, index=False)
        print(f"  Successfully saved: {output_file}")
        
        # Generate basic statistical analysis for Results/
        stats_file = os.path.join(results_dir, f"{wave_name.replace(' ', '')}_summary.csv")
        describe_df = wave_df.describe()
        
        # Add row for percentage of nulls per column
        null_percent = (wave_df.isnull().sum() / len(wave_df)) * 100
        describe_df.loc['null_%'] = null_percent
        
        # Add column with global dataset metrics (to know how much is left after dropna)
        describe_df['GLOBAL_DATASET'] = np.nan
        describe_df.loc['count', 'GLOBAL_DATASET'] = len(wave_df)
        
        # Note: dropna() on the entire dataframe may leave very few records for variables with high missing rates (e.g. br001)
        describe_df.loc['after_dropna_count'] = np.nan
        describe_df.loc['after_dropna_count', 'GLOBAL_DATASET'] = len(wave_df.dropna())
        
        describe_df.to_csv(stats_file)
        print(f"  Statistical summary saved: {stats_file}")
    else:
        print(f"  No data extracted for {wave_name}.")

# Process waves 4, 5, 6 and 7
for w in ['Wave 4', 'Wave 5', 'Wave 6', 'Wave 7']:
    process_wave(w)

print("Processing completed.")
