import tkinter as tk
from tkinter import messagebox
import os
import mysql.connector
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import Counter

# MySQL Connection Setup (Update with your MySQL credentials)
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",        # Your MySQL server (usually localhost)
        user="root",             # MySQL username
        password="kc-ac-am-TC24!",     # MySQL password
        database="hospital_db"   # Your MySQL database
    )

# Function to create the database if it doesn't exist
def create_database():
    connection = None
    cursor = None
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS hospital_db")
        cursor.execute("USE hospital_db")

        # Create the program_run_history table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_run_history (
            run_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100), 
            run_time DATETIME
        );
        """)

        # Create the program_run_log table to track each successful program launch
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_run_log (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            run_time DATETIME
        );
        """)

        connection.commit()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Function to create the table (or recreate it) for program run history
def create_program_run_table():
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Drop the table if it exists (to avoid the old version causing issues)
        cursor.execute("DROP TABLE IF EXISTS program_run_history;")

        # Create the table with the proper columns
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_run_history (
            run_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),  -- column for the username of the nurse
            run_time DATETIME       -- column for the datetime of the program run
        );
        """)

        connection.commit()
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error creating table: {err}")

# Function to log program run event (verification by nurse)
def log_program_run(username):
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Insert a new record for each program run with the nurse's username
        cursor.execute("""
        INSERT INTO program_run_history (username, run_time)
        VALUES (%s, %s)
        """, (username, datetime.now()))

        connection.commit()
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error logging program run: {err}")

# Function to log the program's successful startup in the program_run_log table
def log_program_start():
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Insert a new record for the successful program run (program startup)
        cursor.execute("""
        INSERT INTO program_run_log (run_time)
        VALUES (%s)
        """, (datetime.now(),))

        connection.commit()
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error logging program startup: {err}")

# Function to plot the program run graph
def plot_feed_graph():
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)

        # Query to get the username and run_time data (verifications by second nurse)
        query = "SELECT username, run_time FROM program_run_history ORDER BY run_time ASC"
        cursor.execute(query)
        program_runs = cursor.fetchall()

        if not program_runs:
            messagebox.showinfo("No Data", "No program run data available.")
            return

        # Filter out only the second nurse's username for plotting
        second_nurse_username = 'nurse2'  # Replace with the actual username for the second nurse
        second_nurse_runs = [run for run in program_runs if run['username'] == second_nurse_username]

        if not second_nurse_runs:
            messagebox.showinfo("No Data", f"No data available for {second_nurse_username}.")
            return

        # Prepare the data for plotting
        run_times = [run['run_time'] for run in second_nurse_runs]
        usernames = [run['username'] for run in second_nurse_runs]  # This will be all the second nurse's username

        cursor.close()
        connection.close()

        # Create a line plot with the second nurse's username on the y-axis and run time on the x-axis
        plt.plot(run_times, usernames, marker='o', linestyle='-', color='skyblue', markersize=5)

        # Set title and labels
        plt.title(f"Breast Milk Verification Log", fontsize=16)
        plt.xlabel("Verification Time", fontsize=12)
        plt.ylabel("Verifying Nurse", fontsize=12)

        # Format the x-axis to display the dates and times clearly
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.gcf().autofmt_xdate()  # Rotate the x-axis labels for better visibility

        # Show the graph
        plt.tight_layout()
        plt.show()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
    except Exception as ex:
        messagebox.showerror("Error", f"Unexpected error: {ex}")

# Function to verify nurse login using environment variables
def verify_nurse_login(username, password):
    correct_username = os.getenv('NURSE_USERNAME', 'nurse2')  # Default for testing
    correct_password = os.getenv('NURSE_PASSWORD', 'password123')  # Default for testing
    
    if username == correct_username and password == correct_password:
        return True
    return False

# Function to handle the verification process
def on_verify():
    # Get the MRN from the entry widget
    mrn = entry_mrn.get()
    
    # Get the nurse login details
    username = entry_username.get()
    password = entry_password.get()
    
    # Verify nurse login credentials
    if verify_nurse_login(username, password):
        messagebox.showinfo("Success", f"Patient MRN {mrn} verified successfully.")
        
        # Log the program run event with the verifying nurse's username
        log_program_run(username)
        
        # Ask the user if they want to see the feed table
        result = messagebox.askyesno("View Feed Table", "Do you want to see a graph of the breast milk feeds over the last 48 hours?")
        if result:
            plot_feed_graph()
    else:
        messagebox.showerror("Error", "Nurse verification failed. Access denied.")

# Set up the main window
root = tk.Tk()
root.title("Breast Milk Administration Verification")

# Set the window size
root.geometry("400x350")

# Create labels and input fields
label_mrn = tk.Label(root, text="Enter Patient MRN from Label:")
label_mrn.pack(pady=10)

entry_mrn = tk.Entry(root, width=30)
entry_mrn.pack(pady=5)

label_username = tk.Label(root, text="Enter Second Nurse's Username:")
label_username.pack(pady=10)

entry_username = tk.Entry(root, width=30)
entry_username.pack(pady=5)

label_password = tk.Label(root, text="Enter Second Nurse's Password:")
label_password.pack(pady=10)

entry_password = tk.Entry(root, show="*", width=30)
entry_password.pack(pady=5)

# Verify button
verify_button = tk.Button(root, text="Verify", command=on_verify)
verify_button.pack(pady=20)

create_database()  # Ensure database exists
create_program_run_table()  # Ensure the table is created correctly
log_program_start()  # Log the program's successful start

# Run the application
root.mainloop()
