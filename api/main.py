from fastapi import FastAPI

app = FastAPI(title="Auto-patching")

@app.get("/health")
def health():
    return {"status": "ok"}