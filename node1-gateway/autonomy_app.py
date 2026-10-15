"""Run with: uvicorn autonomy_app:app  (main.py stays untouched)."""
from main import app, verify_mcp_auth
from autonomy_api import build_router

app.include_router(build_router(verify_mcp_auth))
