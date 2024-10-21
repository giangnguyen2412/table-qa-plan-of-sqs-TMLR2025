#!/bin/bash

# Define the paths to the Python scripts
VISUALIZE_POS_SCRIPT="visualization/script/visualize_POS.py"


# Check if the visualize_POS.py script exists
if [ -f "$VISUALIZE_POS_SCRIPT" ]; then
    echo "Running visualize_POS.py with XAI_METHOD=POS..."
    XAI_METHOD='POS' python "$VISUALIZE_POS_SCRIPT"
    if [ $? -ne 0 ]; then
        echo "Error: visualize_POS.py failed to run."
        exit 1
    fi
else
    echo "Error: $VISUALIZE_POS_SCRIPT not found."
    exit 1
fi


echo "Visualized POS successfully."
