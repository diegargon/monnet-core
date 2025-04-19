"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

from pathlib import Path
import sys

from monnet_gateway.tests_cli.common_cli import init_context

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting test_config CLI", "info")

    db = ctx.get_database()
    if db:
        try:
            users = db.fetchall("SELECT * FROM users")
            print(users)
        except RuntimeError as e:
            print(f"Database query error: {e}")
    else:
        print("Database connection is not available")
