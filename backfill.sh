#!/bin/bash

for ((i=0; i<=38; i++)); do
    python main.py --gameweek $((i+1))
done
