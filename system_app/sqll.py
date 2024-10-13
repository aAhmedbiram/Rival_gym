import pyodbc
import pandas as pd

# Replace these variables with your actual values
server_name = 'master'
database_name = 'master'

# Create a connection string for Windows authentication
connection_string = f'DRIVER=SQL Server;SERVER={server_name};DATABASE={database_name};Trusted_Connection=yes;'

# Establish a connection
try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # Sample query to retrieve data from a table
    query = 'SELECT * FROM Members'
    
    # Execute the query and fetch the results into a Pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Display the DataFrame
    print(df)

except pyodbc.Error as ex:
    print(f"Error: {ex}")

finally:
    # Close the cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
