#!/bin/sh
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PYTHON=${PYTHON:-python3}

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python not found. Install Python 3.10+ and its venv package." >&2
    exit 1
fi

"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10+ is required.")'
"$PYTHON" -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -c "import database; database.init_db(); print('Database ready at:', database.DB_PATH)"

echo "Setup complete. Start the app with: sh run.sh"