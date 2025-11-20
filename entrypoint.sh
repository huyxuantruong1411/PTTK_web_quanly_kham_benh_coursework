#!/bin/bash

# Retry connect DB (10 lần, 5s mỗi)
for i in {1..10}; do
  python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')); engine.connect()" && break
  echo "DB not ready, retry $i/10..."
  sleep 5
done

python setup_db.py
python seed_full_db.py

# Chạy Gunicorn với eventlet cho SocketIO
gunicorn -k eventlet -w 1 run:app