#!/bin/bash

echo "🔧 Running: setup_db.py to create tables..."
python setup_db.py

echo "🌱 Running: seed_full_db.py to generate sample data..."
python seed_full_db.py

echo "🚀 Starting Gunicorn server..."
gunicorn run:app