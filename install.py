import subprocess

def install_packages(file_path):
    with open(file_path, 'r') as file:
        packages = file.readlines()
    
    for package in packages:
        package = package.strip()
        if package:
            try:
                subprocess.run(['pip', 'install', package], check=True)
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}, skipping...")

if __name__ == "__main__":
    install_packages('requirements.txtf')