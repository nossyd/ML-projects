import pandas as pd
import re
import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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


def add_travel_distance_miles(df, lat1_col, long1_col, lat2_col, long2_col, distance_col='travel_distance_miles'):
    """
    Vectorized version for better performance on large DataFrames.
    """
    result_df = df.copy()
    
    # Earth's radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1 = np.radians(result_df[lat1_col])
    long1 = np.radians(result_df[long1_col])
    lat2 = np.radians(result_df[lat2_col])
    long2 = np.radians(result_df[long2_col])
    
    # Calculate differences
    dlat = lat2 - lat1
    dlong = long2 - long1
    
    # Haversine formula
    a = (np.sin(dlat/2)**2 + 
         np.cos(lat1) * np.cos(lat2) * np.sin(dlong/2)**2)
    
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    result_df[distance_col] = R * c
    
    return result_df


def plot_histogram_kde(df, col, title=None, xlabel=None, ylabel="Frequency", 
                       bins=30, color="skyblue", figsize=(10, 6)):
    """
    Create a histogram with KDE (Kernel Density Estimation) for a DataFrame column.
    
    Parameters:
    df: pandas DataFrame
    col: Column name to plot
    title: Plot title (default: "Histogram with KDE for {col}")
    xlabel: X-axis label (default: col name)
    ylabel: Y-axis label (default: "Frequency")
    bins: Number of bins for histogram (default: 30)
    color: Color for the histogram (default: "skyblue")
    figsize: Figure size tuple (default: (10, 6))
    
    Returns:
    None (displays the plot)
    """
    # Set figure size
    plt.figure(figsize=figsize)
    
    # Create the plot
    sns.histplot(df[col], kde=True, bins=bins, color=color, 
                 edgecolor="black", alpha=0.7)
    
    # Set default labels if not provided
    if title is None:
        title = f"Histogram with KDE for {col}"
    if xlabel is None:
        xlabel = col
    
    # Add titles and labels
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    
    # Show the plot
    plt.show()


def separate(data):
    """This function will separate the data into numerical and categorical type (object)

    Args:
        data (pd.DataFrame): Dataframe containing all columns

    Returns:
        num: numerical type columns
        cat: categorical type columns
    """
    num = data.dtypes != 'object'
    cat = data.dtypes == 'object'

    num = data[data.columns[num]]
    cat = data[data.columns[cat]]
    
    return num, cat


def cat_feat(train, valid, test=None):
    """This function matches the categorical features in the training, validation, and testing sets simultaneously

    Args:
        train (pd.DataFrame): Dataframe containing categorical data for training dataset
        valid (pd.DataFrame): Dataframe containing categorical data for valid dataset
        test (pd.DataFrame): Dataframe containing categorical data for test dataset

    Returns:
        train: Dataframe containing categorical data for training dataset
        valid: Dataframe containing categorical data for valid dataset
        test: Dataframe containing categorical data for test dataset
    """
    # Make sure categorical features in all sets match
    # Make sure the training, validation, and test features has same number of levels
    keep = [train.nunique()[i] == valid.nunique()[i] == test.nunique()[i] for i in range(train.shape[1])]
    train = train[train.columns[keep]]
    valid = valid[valid.columns[keep]]
    if test is not None:
        test = test[test.columns[keep]]

    # Make sure the levels are the same
    keep = []
    for i in range(train.shape[1]):
        keep.append(all(np.sort(train.iloc[:,i].unique()) == np.sort(valid.iloc[:,i].unique())) and all(np.sort(valid.iloc[:,i].unique()) == np.sort(test.iloc[:,i].unique())))
    train = train[train.columns[keep]]
    valid = valid[valid.columns[keep]]
    if test is not None:
        test = test[test.columns[keep]]
        return train, valid, test
    else:
        return train, valid