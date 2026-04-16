"""
Dashboard Router — Arayüz sunucu endpoint'i.
"""

import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from loguru import logger

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard", response_class=HTMLResponse, summary="Gösterge Paneli Arayüzü")
async def get_dashboard():
    """
    Kullanıcı dostu, gerçek zamanlı dashboard arayüzünü (HTML) döner.
    """
    html_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "ui", 
        "dashboard.html"
    )
    
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        logger.error(f"Dashboard HTML bulunamadı: {html_path}")
        return HTMLResponse(content="<h1>404 - Dashboard dosyası bulunamadı</h1>", status_code=404)
