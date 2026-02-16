import sys

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "telegram"

    if mode == "telegram":
        from app.telegram_bot import main
        main()

    elif mode == "local":
        from app.local_cli import main
        main()

    else:
        print("Usage:")
        print("  python run.py telegram")
        print("  python run.py local")

