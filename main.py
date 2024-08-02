
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app:app",
        host="127.0.0.1",
        log_level="debug",
        port=8040,
        reload=True,
    )
