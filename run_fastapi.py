from src.infrastructure.rich.console_factory import create_console


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.infrastructure.fastapi.app:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
