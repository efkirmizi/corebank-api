#!/bin/sh
# Wait for the database, apply migrations (optionally seed), then serve.
set -e

echo "corebank-api: waiting for database at ${DB_HOST}:${DB_PORT} ..."
python - <<'PY'
import os, sys, time
import pymysql

for attempt in range(60):
    try:
        pymysql.connect(
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=3,
        ).close()
        print("database is ready")
        break
    except Exception as exc:  # noqa: BLE001
        print(f"  not ready yet ({exc.__class__.__name__}); retrying...")
        time.sleep(2)
else:
    sys.exit("database never became reachable")
PY

if [ -n "${SEED_DEMO_DATA}" ]; then
    python -m scripts.migrate --seed
else
    python -m scripts.migrate
fi

echo "corebank-api: starting gunicorn"
exec gunicorn \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
