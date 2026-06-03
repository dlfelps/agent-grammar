"""Toy FastAPI app used as the System Under Test in integration tests."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request


def build_app() -> FastAPI:
    app = FastAPI(title="sample-app")

    @app.post("/v1/auth/token")
    async def issue_token(payload: dict) -> dict:
        if not payload.get("seed"):
            raise HTTPException(status_code=400, detail="seed required")
        return {"access_token": "sample-token-abc123"}

    @app.post("/v1/materials", status_code=201)
    async def register_material(payload: dict, request: Request) -> dict:
        if not request.headers.get("authorization", "").startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        return {"id": "mat-001", **payload}

    return app
