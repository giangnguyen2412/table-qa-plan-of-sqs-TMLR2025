# install.py

import subprocess
import os

def run_command(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("Installing required Python packages...")
    run_command("pip install -r requirements.txt")

    print("Checking if Azure CLI is logged in...")
    result = subprocess.run("az account show", shell=True)
    if result.returncode != 0:
        print("You are not logged into Azure CLI. Please run: az login")
    else:
        print("Azure CLI is already logged in.")

    # Optional: Download datasets, create folders, etc.
    # os.makedirs("data", exist_ok=True)

if __name__ == "__main__":
    main()
