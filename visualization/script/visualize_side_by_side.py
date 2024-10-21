import os
from utils.helper import *

def get_ids_from_directory(directory, prefix, suffix):
    """Extract IDs from files in a directory with a given prefix and suffix."""
    ids = set()
    for filename in os.listdir(directory):
        if filename.startswith(prefix) and filename.endswith(suffix):
            id_part = filename[len(prefix):-len(suffix)]
            ids.add(id_part)
    return ids

def find_common_ids_in_subfolders(base_dir_x, base_dir_y, subfolders, prefix_x, suffix_x, prefix_y, suffix_y):
    """Find IDs that are common to files in corresponding subfolders in both directories."""
    common_ids = {}
    for subfolder in subfolders:
        dir_x = os.path.join(base_dir_x, subfolder)
        dir_y = os.path.join(base_dir_y, subfolder)
        
        ids_x = get_ids_from_directory(dir_x, prefix_x, suffix_x)
        ids_y = get_ids_from_directory(dir_y, prefix_y, suffix_y)
        
        common_ids[subfolder] = ids_x.intersection(ids_y)
    
    return common_ids

def split_content_by_hr(content):
    """Split the HTML content by <hr> tags and return the sections along with their lengths."""
    sections = content.split('<hr>')
    return sections

def merge_html_sections(sections_x, sections_y):
    """Merge sections from two lists of HTML content side by side with padding and <hr> separators."""
    max_length = max(len(sections_x), len(sections_y))
    merged_sections = []

    for i in range(max_length):
        section_x = sections_x[i] if i < len(sections_x) else ""
        section_y = sections_y[i] if i < len(sections_y) else ""

        # Determine the height of each section by counting lines
        height_x = section_x.count('\n')
        height_y = section_y.count('\n')

        # Pad the shorter section to match the length of the longer one
        if height_x > height_y and section_y:
            section_y = f'<div style="min-height: {height_x}em;">{section_y}</div>'
        elif height_y > height_x and section_x:
            section_x = f'<div style="min-height: {height_y}em;">{section_x}</div>'

        merged_sections.append(f"""
        <div class="container">
            <div class="left">
                {section_x}
            </div>
            <div class="right">
                {section_y}
            </div>
        </div>
        <hr>
        """)

    return ''.join(merged_sections)

def merge_html_files(file_x, file_y):
    """Merge the contents of two HTML files side by side."""
    with open(file_x, 'r') as f_x, open(file_y, 'r') as f_y:
        content_x = f_x.read()
        content_y = f_y.read()

    sections_x = split_content_by_hr(content_x)
    sections_y = split_content_by_hr(content_y)

    # Merge sections with alignment
    merged_content = merge_html_sections(sections_x[:len(sections_y)], sections_y[:len(sections_x)])

    # Append any remaining sections from the longer file without padding
    if len(sections_x) > len(sections_y):
        for section in sections_x[len(sections_y):]:
            merged_content += f"""
            <div class="container">
                <div class="left">
                    {section}
                </div>
                <div class="right"></div>
            </div>
            <hr>
            """
    elif len(sections_y) > len(sections_x):
        for section in sections_y[len(sections_x):]:
            merged_content += f"""
            <div class="container">
                <div class="left"></div>
                <div class="right">
                    {section}
                </div>
            </div>
            <hr>
            """

    final_html = f"""
    <html>
    <head>
    <style>
    .container {{
        display: flex;
    }}
    .left, .right {{
        width: 50%;
        padding: 10px;
    }}
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ text-align: center; }}
    .cot-title {{ color: blue; }}
    .pos-title {{ color: green; }}
    h2 {{ color: black; text-align: left; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    table, th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background-color: #f2f2f2; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .important {{ font-weight: bold; color: #ff5722; }}
    .highlight {{ background-color: #ffffcc; }}
    </style>
    </head>
    <body>
    {merged_content}
    </body>
    </html>
    """
    return final_html


def save_merged_html(output_dir, subfolder, id, content):
    """Save the merged HTML content into the specified output directory."""
    os.makedirs(os.path.join(output_dir, subfolder), exist_ok=True)
    output_file = os.path.join(output_dir, subfolder, f"test-{id}.html")
    with open(output_file, 'w') as f:
        f.write(content)

# Set the base directories and file naming conventions
base_dir_x = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/chain-of-Table/htmls_COT/'
base_dir_y = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/chain-of-Table/htmls_POS/'
if VIS_STYLE == 5:
    output_dir = 'side-by-side-compact-Freddy'
elif VIS_STYLE == 4:
    output_dir = 'side-by-side-CoT-Giang'
elif VIS_STYLE == 6:
    output_dir = 'side-by-side-color-coding-Sanjay'

subfolders = ['TP', 'FP', 'TN', 'FN']
prefix_x = 'test-'
suffix_x = '.html'
prefix_y = 'test-'
suffix_y = '.html'

# Find common IDs in corresponding subfolders
common_ids_in_subfolders = find_common_ids_in_subfolders(base_dir_x, base_dir_y, subfolders, prefix_x, suffix_x, prefix_y, suffix_y)

# Merge HTML files and save them in the output directory
for subfolder, common_ids in common_ids_in_subfolders.items():
    for id in common_ids:
        file_x = os.path.join(base_dir_x, subfolder, f"{prefix_x}{id}{suffix_x}")
        file_y = os.path.join(base_dir_y, subfolder, f"{prefix_y}{id}{suffix_y}")
        
        merged_content = merge_html_files(file_x, file_y)
        save_merged_html(output_dir, subfolder, id, merged_content)

print("Merged HTML files have been saved in 'side-by-side/' directory.")


########################################################


import os

def get_ids_from_directory(directory, prefix, suffix):
    """Extract IDs from files in a directory with a given prefix and suffix."""
    ids = set()
    for filename in os.listdir(directory):
        if filename.startswith(prefix) and filename.endswith(suffix):
            id_part = filename[len(prefix):-len(suffix)]
            ids.add(id_part)
    return ids

def find_tp_pos_fn_cot_ids(base_dir_pos, base_dir_cot, prefix, suffix):
    """Find IDs that are TP in POS but FN in COT."""
    tp_pos_dir = os.path.join(base_dir_pos, 'TP')
    fn_cot_dir = os.path.join(base_dir_cot, 'FN')
    
    ids_tp_pos = get_ids_from_directory(tp_pos_dir, prefix, suffix)
    ids_fn_cot = get_ids_from_directory(fn_cot_dir, prefix, suffix)
    
    tp_pos_fn_cot_ids = ids_tp_pos.intersection(ids_fn_cot)
    
    return tp_pos_fn_cot_ids

def split_content_by_hr(content):
    """Split the HTML content by <hr> tags and return the sections along with their lengths."""
    sections = content.split('<hr>')
    return sections

def merge_html_sections(sections_x, sections_y):
    """Merge sections from two lists of HTML content side by side with padding and <hr> separators."""
    max_length = max(len(sections_x), len(sections_y))
    merged_sections = []

    for i in range(max_length):
        section_x = sections_x[i] if i < len(sections_x) else ""
        section_y = sections_y[i] if i < len(sections_y) else ""

        # Determine the height of each section by counting lines
        height_x = section_x.count('\n')
        height_y = section_y.count('\n')

        # Pad the shorter section to match the length of the longer one
        if height_x > height_y and section_y:
            section_y = f'<div style="min-height: {height_x}em;">{section_y}</div>'
        elif height_y > height_x and section_x:
            section_x = f'<div style="min-height: {height_y}em;">{section_x}</div>'

        merged_sections.append(f"""
        <div class="container">
            <div class="left">
                {section_x}
            </div>
            <div class="right">
                {section_y}
            </div>
        </div>
        <hr>
        """)

    return ''.join(merged_sections)

def merge_html_files(file_x, file_y):
    """Merge the contents of two HTML files side by side."""
    with open(file_x, 'r') as f_x, open(file_y, 'r') as f_y:
        content_x = f_x.read()
        content_y = f_y.read()

    sections_x = split_content_by_hr(content_x)
    sections_y = split_content_by_hr(content_y)

    # Merge sections with alignment
    merged_content = merge_html_sections(sections_x[:len(sections_y)], sections_y[:len(sections_x)])

    # Append any remaining sections from the longer file without padding
    if len(sections_x) > len(sections_y):
        for section in sections_x[len(sections_y):]:
            merged_content += f"""
            <div class="container">
                <div class="left">
                    {section}
                </div>
                <div class="right"></div>
            </div>
            <hr>
            """
    elif len(sections_y) > len(sections_x):
        for section in sections_y[len(sections_x):]:
            merged_content += f"""
            <div class="container">
                <div class="left"></div>
                <div class="right">
                    {section}
                </div>
            </div>
            <hr>
            """

    final_html = f"""
    <html>
    <head>
    <style>
    .container {{
        display: flex;
    }}
    .left, .right {{
        width: 50%;
        padding: 10px;
    }}
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ text-align: center; }}
    .cot-title {{ color: blue; }}
    .pos-title {{ color: green; }}
    h2 {{ color: black; text-align: left; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    table, th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background-color: #f2f2f2; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .important {{ font-weight: bold; color: #ff5722; }}
    .highlight {{ background-color: #ffffcc; }}
    </style>
    </head>
    <body>
    {merged_content}
    </body>
    </html>
    """
    return final_html


def save_merged_html(output_dir, subfolder, id, content):
    """Save the merged HTML content into the specified output directory."""
    os.makedirs(os.path.join(output_dir, subfolder), exist_ok=True)
    output_file = os.path.join(output_dir, subfolder, f"test-{id}.html")
    with open(output_file, 'w') as f:
        f.write(content)

# Set the base directories and file naming conventions
base_dir_x = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/chain-of-Table/htmls_COT/'
base_dir_y = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/chain-of-Table/htmls_POS/'
if VIS_STYLE == 5:
    output_dir = 'side-by-side-compact-Freddy'
elif VIS_STYLE == 4:
    output_dir = 'side-by-side-CoT-Giang'
elif VIS_STYLE == 6:
    output_dir = 'side-by-side-color-coding-Sanjay'

prefix = 'test-'
suffix = '.html'

# Find common IDs that are TP for POS but FN for COT
tp_pos_fn_cot_ids = find_tp_pos_fn_cot_ids(base_dir_y, base_dir_x, prefix, suffix)

# Merge HTML files and save them in the output directory
for id in tp_pos_fn_cot_ids:
    file_x = os.path.join(base_dir_x, 'FN', f"{prefix}{id}{suffix}")
    file_y = os.path.join(base_dir_y, 'TP', f"{prefix}{id}{suffix}")
    
    merged_content = merge_html_files(file_x, file_y)
    save_merged_html(output_dir, 'TP_POS_FN_COT', id, merged_content)

print("Merged HTML files have been saved in 'side-by-side/TP_POS_FN_COT/' directory.")

##########################################################################

import os

def get_ids_from_directory(directory, prefix, suffix):
    """Extract IDs from files in a directory with a given prefix and suffix."""
    ids = set()
    for filename in os.listdir(directory):
        if filename.startswith(prefix) and filename.endswith(suffix):
            id_part = filename[len(prefix):-len(suffix)]
            ids.add(id_part)
    return ids

def find_fn_pos_tp_cot_ids(base_dir_pos, base_dir_cot, prefix, suffix):
    """Find IDs that are FN in POS but TP in COT."""
    fn_pos_dir = os.path.join(base_dir_pos, 'FN')
    tp_cot_dir = os.path.join(base_dir_cot, 'TP')
    
    ids_fn_pos = get_ids_from_directory(fn_pos_dir, prefix, suffix)
    ids_tp_cot = get_ids_from_directory(tp_cot_dir, prefix, suffix)
    
    fn_pos_tp_cot_ids = ids_fn_pos.intersection(ids_tp_cot)
    
    return fn_pos_tp_cot_ids

def split_content_by_hr(content):
    """Split the HTML content by <hr> tags and return the sections along with their lengths."""
    sections = content.split('<hr>')
    return sections

def merge_html_sections(sections_x, sections_y):
    """Merge sections from two lists of HTML content side by side with padding and <hr> separators."""
    max_length = max(len(sections_x), len(sections_y))
    merged_sections = []

    for i in range(max_length):
        section_x = sections_x[i] if i < len(sections_x) else ""
        section_y = sections_y[i] if i < len(sections_y) else ""

        # Determine the height of each section by counting lines
        height_x = section_x.count('\n')
        height_y = section_y.count('\n')

        # Pad the shorter section to match the length of the longer one
        if height_x > height_y and section_y:
            section_y = f'<div style="min-height: {height_x}em;">{section_y}</div>'
        elif height_y > height_x and section_x:
            section_x = f'<div style="min-height: {height_y}em;">{section_x}</div>'

        merged_sections.append(f"""
        <div class="container">
            <div class="left">
                {section_x}
            </div>
            <div class="right">
                {section_y}
            </div>
        </div>
        <hr>
        """)

    return ''.join(merged_sections)

def merge_html_files(file_x, file_y):
    """Merge the contents of two HTML files side by side."""
    with open(file_x, 'r') as f_x, open(file_y, 'r') as f_y:
        content_x = f_x.read()
        content_y = f_y.read()

    sections_x = split_content_by_hr(content_x)
    sections_y = split_content_by_hr(content_y)

    # Merge sections with alignment
    merged_content = merge_html_sections(sections_x[:len(sections_y)], sections_y[:len(sections_x)])

    # Append any remaining sections from the longer file without padding
    if len(sections_x) > len(sections_y):
        for section in sections_x[len(sections_y):]:
            merged_content += f"""
            <div class="container">
                <div class="left">
                    {section}
                </div>
                <div class="right"></div>
            </div>
            <hr>
            """
    elif len(sections_y) > len(sections_x):
        for section in sections_y[len(sections_x):]:
            merged_content += f"""
            <div class="container">
                <div class="left"></div>
                <div class="right">
                    {section}
                </div>
            </div>
            <hr>
            """

    final_html = f"""
    <html>
    <head>
    <style>
    .container {{
        display: flex;
    }}
    .left, .right {{
        width: 50%;
        padding: 10px;
    }}
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ text-align: center; }}
    .cot-title {{ color: blue; }}
    .pos-title {{ color: green; }}
    h2 {{ color: black; text-align: left; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    table, th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background-color: #f2f2f2; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .important {{ font-weight: bold; color: #ff5722; }}
    .highlight {{ background-color: #ffffcc; }}
    </style>
    </head>
    <body>
    {merged_content}
    </body>
    </html>
    """
    return final_html


def save_merged_html(output_dir, subfolder, id, content):
    """Save the merged HTML content into the specified output directory."""
    os.makedirs(os.path.join(output_dir, subfolder), exist_ok=True)
    output_file = os.path.join(output_dir, subfolder, f"test-{id}.html")
    with open(output_file, 'w') as f:
        f.write(content)

# Set the base directories and file naming conventions
base_dir_pos = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/chain-of-Table/htmls_POS/'
base_dir_cot = '/opt/omniai/work/instance1/jupyter/tabular_grounding_llms/chain-of-Table/htmls_COT/'
if VIS_STYLE == 5:
    output_dir = 'side-by-side-compact-Freddy'
elif VIS_STYLE == 4:
    output_dir = 'side-by-side-CoT-Giang'
elif VIS_STYLE == 6:
    output_dir = 'side-by-side-color-coding-Sanjay'

prefix = 'test-'
suffix = '.html'

# Find common IDs that are FN for POS but TP for COT
fn_pos_tp_cot_ids = find_fn_pos_tp_cot_ids(base_dir_pos, base_dir_cot, prefix, suffix)

# Merge HTML files and save them in the output directory
for id in fn_pos_tp_cot_ids:
    file_x = os.path.join(base_dir_pos, 'FN', f"{prefix}{id}{suffix}")
    file_y = os.path.join(base_dir_cot, 'TP', f"{prefix}{id}{suffix}")
    
    merged_content = merge_html_files(file_y, file_x)
    save_merged_html(output_dir, 'FN_POS_TP_COT', id, merged_content)

print("Merged HTML files have been saved in 'side-by-side/FN_POS_TP_COT/' directory.")
