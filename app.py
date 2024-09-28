from flask import Flask, render_template, request, send_file
import pandas as pd
import os
from docx import Document
from readBackup import clauses_dict

app = Flask(__name__)

# Load the Excel workbook
file_path = 'Clause Matrix.xlsx'  # Replace this with the correct path to your file
xls = pd.ExcelFile(file_path, engine='openpyxl')

# Load the 'sort1' sheet into a DataFrame and force 'ALL PROCUREMENT TYPES' to be read as strings
df_sort1 = pd.read_excel(xls, sheet_name='sort1', dtype={'ALL PROCUREMENT TYPES': str})

# Convert 'ALL PROCUREMENT TYPES' column to avoid NaN issues
df_sort1['ALL PROCUREMENT TYPES'] = df_sort1['ALL PROCUREMENT TYPES'].fillna('').astype(str)

# Print the DataFrame to inspect the data for ALL PROCUREMENT TYPES
#print(df_sort1[['Cost', 'ALL PROCUREMENT TYPES']])  # <<--- Inserted here for debugging

# Initialize an empty dictionary to store clause IDs based on rows and columns
procurement_data = {}

# Iterate through each row in the DataFrame and populate the dictionary
for index, row in df_sort1.iterrows():
    cost_category = row['Cost']  # Assuming this column contains cost categories like "$10,000", "$25,000", etc.
    for column in df_sort1.columns[1:]:  # Skipping the first column (Cost), iterate over procurement types
        procurement_type = column
        clause_ids = row[procurement_type]  # Get clause IDs for this procurement type
        if cost_category not in procurement_data:
            procurement_data[cost_category] = {}
        procurement_data[cost_category][procurement_type] = clause_ids

# Function to get all cost thresholds that match the user input
def get_matching_thresholds(project_cost):
    """ Returns a list of cost thresholds that are less than or equal to the input project_cost """
    thresholds = []

    # Add ANY COST first since it's always included
    thresholds.append("ANY COST")
    
    # Add other thresholds based on project cost
    if project_cost > 10000:
        thresholds.append(">$10,000")
    if project_cost > 25000:
        thresholds.append(">$25,000")
    if project_cost > 100000:
        thresholds.append(">$100,000")
    if project_cost > 150000:
        thresholds.append(">$150,000")
    if project_cost > 250000:
        thresholds.append(">$250,000")
    
    return thresholds

@app.route('/')
def index():
    # Display the available procurement types (columns)
    procurement_types = df_sort1.columns[1:].tolist()  # Get all columns except 'Cost'
    return render_template('index.html', procurement_types=procurement_types)

@app.route('/get_clauses', methods=['GET', 'POST'])
def get_clauses():
    if request.method == 'POST':
        # Handle form submission
        if 'cost' not in request.form or request.form['cost'] == '':
            return "Project cost is missing", 400  # Handle missing cost input
        
        selected_column = request.form['column']
        project_cost = float(request.form['cost'])  # Convert cost to float

        # Mapping text-based thresholds to numeric values
        cost_mapping = {
            ">$10,000": 10000,
            ">$25,000": 25000,
            ">$100,000": 100000,
            ">$150,000": 150000,
            ">$250,000": 250000,
            "ANY COST": 0  # Assume "ANY COST" applies to any value
        }

        # Initialize an empty list to store all relevant clause IDs
        clause_ids = []

        # Debugging: print project cost
        #print(f"User project cost: {project_cost}")
        
        # Iterate over each row in the DataFrame
        for index, row in df_sort1.iterrows():
            row_cost_label = row['Cost']

            # Get the numeric value corresponding to the cost threshold
            if row_cost_label in cost_mapping:
                row_cost = cost_mapping[row_cost_label]
            else:
                print(f"Skipping row index {index}: Invalid or unmapped cost value '{row_cost_label}'")
                continue

            # Debugging: print the current row cost and type
            #print(f"Row index: {index}, Row cost: {row_cost}, Type: {type(row_cost)}")
            
            # Check if the current row cost is less than or equal to the user's input
            if project_cost >= row_cost:
                #print(f"Row cost {row_cost} is <= user input cost {project_cost}")
                
                # Get clause IDs from the selected column
                selected_column_ids = row[selected_column]

                # Debugging: print clause IDs from the selected column
                #print(f"Selected column ({selected_column}) IDs: {selected_column_ids}")

                # Check if the value is not NaN and append to clause_ids
                if pd.notna(selected_column_ids):
                    clause_ids.extend([clause.strip() for clause in str(selected_column_ids).split(',')])

                # Get clause IDs from the "ALL PROCUREMENT TYPES" column
                all_procurement_ids = row['ALL PROCUREMENT TYPES']
                
                # Debugging: print clause IDs from the "ALL PROCUREMENT TYPES" column
                #print(f"ALL PROCUREMENT TYPES IDs: {all_procurement_ids}")

                # Check if the value is not NaN and append to clause_ids
                if pd.notna(all_procurement_ids):
                    clause_ids.extend([clause.strip() for clause in str(all_procurement_ids).split(',')])

        # Ensure the clause IDs list is unique and sorted
        clause_ids = list(set(clause_ids))  # Remove duplicates

        #print("Clause IDs fetched from Excel:", clause_ids)
        
        try:
            clause_ids = [float(clause_id) for clause_id in clause_ids if clause_id]
        except ValueError as e:
            return f"Error processing clause IDs: {str(e)}", 400
        
        # Debugging: Print the clause IDs after converting to float
        #print("Clause IDs after conversion to float:", clause_ids)

        document = Document()
        document.add_heading('Clauses Report', 0)

        for clause_id in clause_ids:
            # Debugging: Print clause ID being looked up
            #print(f"Looking up clause ID: {clause_id}")
            
            clause_data = clauses_dict.get(clause_id, {})
            
            if not clause_data:
                clause_data = clauses_dict.get(int(clause_id), {})  # Try as integer
            if not clause_data:
                clause_data = clauses_dict.get(str(int(clause_id)), {})  # Try as string (integer)
             
             # Debugging: Print the fetched clause data
            #print(f"Fetched clause data for ID {clause_id}: {clause_data}")
            title = clause_data.get('Title', f'Clause {clause_id} (No Title Found)')
            text = clause_data.get('Text', 'No Text Found')

            document.add_heading(title, level=1)
            document.add_paragraph(text)

        # Save the document to a file
        output_file_path = 'Clauses_Report.docx'
        document.save(output_file_path)

        # Provide the file for download
        return send_file(output_file_path, as_attachment=True, download_name='Clauses_Report.docx')

    # If GET request, just render the form
    return render_template('index.html', procurement_types=df_sort1.columns[1:].tolist())

if __name__ == '__main__':
    app.run(debug=True)