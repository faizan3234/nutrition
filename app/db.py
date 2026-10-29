import sqlite3
import os
from contextlib import contextmanager
DB_PATH = os.getenv('NUTRITION_DB_PATH', '/tmp/nutrition.sqlite3' if (os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME')) else './nutrition.sqlite3')


def init_db():
    with connection() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS meal_logs
            (id TEXT PRIMARY KEY, profile TEXT NOT NULL, food_id TEXT NOT NULL,
             food_name TEXT NOT NULL, grams REAL NOT NULL, meal TEXT NOT NULL,
             kcal REAL NOT NULL,protein REAL NOT NULL,carbs REAL NOT NULL,fat REAL NOT NULL,
             created_at TEXT NOT NULL)''')
        existing={r['name'] for r in c.execute('PRAGMA table_info(meal_logs)').fetchall()}
        if 'unit' not in existing:
            c.execute("ALTER TABLE meal_logs ADD COLUMN unit TEXT NOT NULL DEFAULT 'g'")
        if 'source' not in existing:
            c.execute("ALTER TABLE meal_logs ADD COLUMN source TEXT NOT NULL DEFAULT 'illustrative_starter_not_verified'")
        # Store the food offered/served separately from food eaten. Existing logs remain valid.
        if 'served_amount' not in existing:
            c.execute('ALTER TABLE meal_logs ADD COLUMN served_amount REAL')
        if 'consumed_percent' not in existing:
            c.execute('ALTER TABLE meal_logs ADD COLUMN consumed_percent REAL')
        c.execute('CREATE INDEX IF NOT EXISTS meal_logs_idx ON meal_logs(profile,created_at)')


@contextmanager
def connection():
    c = sqlite3.connect(DB_PATH)
    c.row_factory=sqlite3.Row
    try:
        yield c;c.commit()
    finally:c.close()
