#!/bin/bash

echo "Running main.py..."
python3 main.py

if [ $? -eq 0 ]; then
    echo "main.py executed successfully."
    
    echo "Running benchmark.py..."
    python3 benchmark.py > benchmark_results.txt

    if [ $? -eq 0 ]; then
        echo "benchmark.py executed successfully. Results saved to output/benchmark_results.txt."
    else
        echo "Error: benchmark.py failed to execute."
    fi
else
    echo "Error: main.py failed to execute. Skipping benchmark.py."
fi

