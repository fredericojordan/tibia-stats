import os


def run():
    from .app import app

    host = os.getenv("HOST") or "0.0.0.0"
    port = os.getenv("PORT") or 10_000
    app.run(host=host, port=port, debug=True, dev_tools_hot_reload=True)


if __name__ == "__main__":
    run()
