from fastapi import FastAPI

app = FastAPI(title="DFS Sim Optimizer")

@app.get("/health")
def health():
    return {"status": "ok"}
