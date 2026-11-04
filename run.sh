#!/bin/sh
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

case "${1:-}" in
    ""|--demo) ;;
    *) echo "Usage: sh run.sh [--demo]" >&2; exit 1 ;;
esac
if [ "$#" -gt 1 ]; then
    echo "Usage: sh run.sh [--demo]" >&2
    exit 1
fi

if [ ! -x venv/bin/python ]; then
    echo "Virtual environment not found. Run: sh setup.sh" >&2
    exit 1
fi

if [ "${1:-}" = "--demo" ]; then
    export EM_DB=data/demo.db
    if [ ! -f "$EM_DB" ]; then
        venv/bin/python create_demo_db.py
    fi
fi

echo "Starting Expense Monitor at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop."
exec venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1