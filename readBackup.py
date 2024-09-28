import pandas as pd

# Load the Excel workbook
file_path = 'Clause Matrix.xlsx'  # Change this to the path of your workbook
xls = pd.ExcelFile(file_path, engine='openpyxl')

# Load the 'backup' sheet into a DataFrame
df_backup = pd.read_excel(xls, sheet_name='backup')

# Create a dictionary with ID#, Title, and Text
clauses_dict = {}

# Iterate through each row and build the dictionary
for index, row in df_backup.iterrows():
    clause_id = row['ID#']
    title = row['Title']
    text = row['Text']
    clauses_dict[clause_id] = {'Title': title, 'Text': text}

# Print the resulting dictionary
#print(clauses_dict)