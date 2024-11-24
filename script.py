import pandas as pd
import os
import logging
import requests
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define the path to your original CSV file
original_file_path = 'SampleData.csv'

# Check if the file exists
if not os.path.exists(original_file_path):
    logging.error(f"File {original_file_path} not found.")
else:
    # Read the original CSV file
    df = pd.read_csv(original_file_path)

    # Define header mapping (OldHeader to NewHeader)
    header_mapping = {
        'Department': 'DepartmentCode',
        'DivisionCode': 'DivisionCode',
        'BenefitClass': 'BenefitClass',
        'ContributionGroup': 'ContributionGroup',
        'MiddleName': 'MiddleName',
        'CompanyCode': 'CompanyCode',
        # Add other mappings as needed
    }

    # Rename columns according to the mapping
    df.rename(columns=header_mapping, inplace=True)

    # Data validation and correction for "Gender" column
    gender_mapping = {
        'f': 'Female', 'F': 'Female',
        'm': 'Male', 'M': 'Male'
    }
    
    df['Gender'] = df['Gender'].replace(gender_mapping)

    # Predict gender for unspecified entries using Genderize.io
    def predict_gender(name):
        try:
            response = requests.get(f"https://api.genderize.io?name={name}")
            if response.status_code == 200:
                data = response.json()
                gender = data.get('gender', None)
                return gender.capitalize() if gender else None
            else:
                return None
        except Exception as e:
            logging.error(f"Error predicting gender for {name}: {e}")
            return None

    # Apply prediction to entries with unspecified gender
    df['Gender'] = df.apply(
        lambda row: predict_gender(row['FirstName']) if row['Gender'] not in ['Male', 'Female'] else row['Gender'],
        axis=1
    )

    # Check for invalid or missing gender entries after prediction
    valid_genders = ['Male', 'Female']
    invalid_genders = df[~df['Gender'].isin(valid_genders)]

    if not invalid_genders.empty:
        logging.warning("Entries with unresolved gender:")
        print(invalid_genders[['FirstName', 'LastName', 'EmailAddress', 'Gender']])

    # Mapping for MarriageStatus
    valid_marriage_statuses = ['Single', 'Married']
    
    # Apply mapping and set other values to "Other"
    df['MarriageStatus'] = df['MarriageStatus'].apply(
        lambda x: x if x in valid_marriage_statuses else 'Other'
    )

    # Mapping for Smoker column
    def map_smoker_status(value):
        if pd.isnull(value) or value.lower() in ['no', 'n']:
            return False
        elif value.lower() in ['yes', 'y']:
            return True
        return False  # Default to False for any other values

    df['Smoker'] = df['Smoker'].apply(lambda x: map_smoker_status(x) if isinstance(x, str) else False)

    # Clean SSN column by removing special characters and preserving leading zeros
    def clean_ssn(ssn):
        if pd.isnull(ssn):
            return ssn  # Return as is if null
        cleaned_ssn = re.sub(r'\D', '', ssn)  # Remove non-digit characters
        return cleaned_ssn.zfill(9)  # Ensure leading zeros are preserved

    df['SSN'] = df['SSN'].apply(clean_ssn)

    # Write the modified DataFrame to a new CSV file
    new_file_path = 'MappedData.csv'
    df.to_csv(new_file_path, index=False)

    logging.info(f"New CSV file created at {new_file_path} with updated headers.")
