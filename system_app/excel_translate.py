import pandas as pd
from deep_translator import GoogleTranslator
import time

# Read the Excel file
excel_file_path = 'C:/Users/New&Used/Desktop/tran.xlsx'
data = pd.read_excel(excel_file_path, engine='openpyxl')

# Print column names to verify
print("Excel file read successfully.")
print(data.columns)

# Function to translate text
def translate_text(text):
    if pd.notna(text):  # Check if the text is not NaN
        try:
            print(f"Translating: {text}")  # Log the text being translated
            translated = GoogleTranslator(source='ar', target='en', timeout=5).translate(text)
            time.sleep(1)  # Add a delay of 1 second between requests
            return translated
        except Exception as e:
            print(f"Translation error for '{text}': {e}")
            return text  # Return original if there's an error
    return text  # Return original if NaN

# Check if 'name' column exists
if 'name' in data.columns:
    # Translate the names in the 'name' column
    data['name'] = data['name'].apply(translate_text)
else:
    print("Error: 'name' column not found in the Excel file.")

# Save the updated DataFrame back to a new Excel file
output_file_path = 'C:/Users/New&Used/Desktop/translated_tran.xlsx'
data.to_excel(output_file_path, index=False)

print(f"Translation complete and saved to '{output_file_path}'.")
