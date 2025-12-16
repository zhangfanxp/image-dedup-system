#!/bin/bash
cd ~/Downloads/image-dedup-system || exit
source .venv/bin/activate
streamlit run app/main.py
