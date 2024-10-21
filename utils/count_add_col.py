import os
import re
from bs4 import BeautifulSoup

def find_files_with_function(directory, step, function):
    files_with_function = []
    function_pattern = re.compile(r'\b' + re.escape(function) + r'\b')

    # Retrieve all filenames and sort by numeric ID
    filenames = os.listdir(directory)
    sorted_files = sorted(filenames, key=lambda x: int(re.search(r'\d+', x).group()))

    for filename in sorted_files:
        if filename.endswith(".html"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                # Find the step
                steps = soup.find_all("div", class_="step")
                for s in steps:
                    if f"Step {step}" in s.h3.get_text():
                        responses = s.find_all("pre")
                        for response in responses:
                            text = response.get_text().strip()
                            # Check if the function is the first operation in the response
                            if function_pattern.search(text):
                                # Further check if it starts with the function
                                if text.startswith(function):
                                    files_with_function.append(filename)
                                    break
    return files_with_function

# Example usage
directory_path = 'post-Analysis/'
step_to_check = 1
function_to_search = 'f_add_column'
result_files = find_files_with_function(directory_path, step_to_check, function_to_search)

print(f"Number of HTML files where the first function in Step {step_to_check} is '{function_to_search}': {len(result_files)}")
for file in result_files:
    print(file)
