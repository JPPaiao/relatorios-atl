import pandas as pd

# Load the Excel file
df = pd.read_excel('teste-12.xlsx', engine='openpyxl')

# Separate rows with and without 'DATA. PAG'
df_with_date = df[df['DATA. PAG'].notna()]
df_without_date = df[df['DATA. PAG'].isna()]

# Remove duplicates in rows with 'DATA. PAG', keeping the first occurrence
df_with_date = df_with_date.drop_duplicates(subset='UNIDADE', keep='first')

# Remove duplicates in rows without 'DATA. PAG', keeping the first occurrence
df_without_date = df_without_date.drop_duplicates(subset='UNIDADE', keep='first')

# Combine both DataFrames
df_filtered = pd.concat([df_with_date, df_without_date])

# Save the filtered DataFrame to a new Excel file
df_filtered.to_excel('filtered_teste-12.xlsx', index=False)

print("Filtered rows have been saved to 'filtered_teste-12.xlsx'.")

import pandas as pd

# Load the Excel file
df = pd.read_excel('filtered_teste-12.xlsx', engine='openpyxl')

# Function to format CNPJ
def format_cnpj(cnpj):
    return str(cnpj).zfill(14)

# Apply the formatting function to all CNPJ columns
cnpj_columns = ['CNPJ AGENDADO', 'CNPJ HBL', 'CNPJ TRANSPORTADORA']
for col in cnpj_columns:
    df[col] = df[col].apply(format_cnpj)

# Save the formatted DataFrame to a new Excel file
df.to_excel('formatted_filtered_teste-12.xlsx', index=False)

print("Formatted CNPJ fields have been saved to 'formatted_filtered_teste-12.xlsx'.")



