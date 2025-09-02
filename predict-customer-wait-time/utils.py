import pandas as pd
import re

def clean_byte_string_columns(df):
    """
    Clean pandas DataFrame columns with object dtype by removing b'...' formatting
    and stripping whitespaces.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame to process
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with cleaned string columns
    """
    # Create a copy to avoid modifying the original DataFrame
    df_cleaned = df.copy()
    
    # Get columns with object dtype
    object_cols = df_cleaned.select_dtypes(include=['object']).columns
    
    for col in object_cols:
        # Apply cleaning to each column
        df_cleaned[col] = df_cleaned[col].apply(clean_byte_string_value)
    
    return df_cleaned

def clean_byte_string_value(value):
    """
    Helper function to clean individual values.
    
    Parameters:
    -----------
    value : any
        Value to clean
        
    Returns:
    --------
    any
        Cleaned value
    """
    # Handle null values
    if pd.isna(value):
        return value
    
    # Convert to string if not already
    str_value = str(value)
    
    # Check if it matches the b'...' pattern
    if str_value.startswith("b'") and str_value.endswith("'"):
        # Remove b' from start and ' from end, then strip whitespace
        cleaned = str_value[2:-1].strip()
        return cleaned
    
    # If it doesn't match the pattern, just strip whitespace
    return str_value.strip()