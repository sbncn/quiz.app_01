import tools.main_defs as md
from tools.setup import setup, get_db_connection, db_config
import json
import psycopg2
import time
import os
from psycopg2.extras import execute_batch  # Performans için
from dotenv import load_dotenv

def start_menu():
    while True:
        print("\n--- Welcome to the Exam System ---")
        print("1. Setup Database")
        print("2. Login")
        print("3. Sign Up")
        print("4. Exit")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            setup()  # Veritabanını kurma işlemi
        elif choice == "2":
            md.login(db_config)
        elif choice == "3":
            md.signup(db_config)
        elif choice == "4":
            print("Exiting...")
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    start_menu()