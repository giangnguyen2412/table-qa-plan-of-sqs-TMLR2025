#!/bin/bash

# Define the paths to the Python scripts
VISUALIZE_POS_SCRIPT="visualize_POS.py"
VISUALIZE_COT_SCRIPT="visualize_COT.py"
EXTRACT_OVERLAPS_SCRIPT="extract_overlaps.py"

# Define the directories to remove
DIRS_TO_REMOVE=("../htmls_COT" "../htmls_POS" "../side-by-side" "../htmls_NO_XAI")

# Remove the specified directories if they exist
for dir in "${DIRS_TO_REMOVE[@]}"; do
    if [ -d "$dir" ]; then
        echo "Removing directory $dir..."
        rm -rf "$dir"
        if [ $? -ne 0 ]; then
            echo "Error: Failed to remove directory $dir."
            exit 1
        fi
    fi
done

# Check if the visualize_POS.py script exists
if [ -f "$VISUALIZE_POS_SCRIPT" ]; then
    echo "Running visualize_POS.py with XAI_METHOD=POS..."
    XAI_METHOD='POS' python "$VISUALIZE_POS_SCRIPT"
    if [ $? -ne 0 ]; then
        echo "Error: visualize_POS.py failed to run."
        exit 1
    fi

    echo "Running visualize_POS.py with XAI_METHOD=NO_XAI..."
    XAI_METHOD='NO_XAI' python "$VISUALIZE_POS_SCRIPT"
    if [ $? -ne 0 ]; then
        echo "Error: visualize_POS.py failed to run."
        exit 1
    fi
else
    echo "Error: $VISUALIZE_POS_SCRIPT not found."
    exit 1
fi

# Check if the visualize_COT.py script exists
if [ -f "$VISUALIZE_COT_SCRIPT" ]; then
    echo "Running visualize_COT.py with XAI_METHOD=COT..."
    XAI_METHOD='COT' python "$VISUALIZE_COT_SCRIPT"
    if [ $? -ne 0 ]; then
        echo "Error: visualize_COT.py failed to run."
        exit 1
    fi
else
    echo "Error: $VISUALIZE_COT_SCRIPT not found."
    exit 1
fi

# # Check if the extract_overlaps.py script exists
# if [ -f "$EXTRACT_OVERLAPS_SCRIPT" ]; then
#     echo "Running extract_overlaps.py..."
#     python "$EXTRACT_OVERLAPS_SCRIPT"
#     if [ $? -ne 0 ]; then
#         echo "Error: extract_overlaps.py failed to run."
#         exit 1
#     fi
# else
#     echo "Error: $EXTRACT_OVERLAPS_SCRIPT not found."
#     exit 1
# fi

echo "All scripts ran successfully."
