from src.api.app import start_app


if __name__ == "__main__":
    print("Hello world!")
    # taskiq worker src.infrastructure.taskiq_app:broker
    start_app()
