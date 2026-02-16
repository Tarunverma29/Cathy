import sys
import os

# Force project root into Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from app.telegram_bot import main

if __name__ == "__main__":
    main()

