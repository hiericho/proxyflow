import asyncio
import logging
import os
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from src.database import init_db, get_db_session
from src.checker import run_checker_cycle
from src.models import HealthCheckTarget, DashboardStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TARGET = "https://www.google.com"

async def load_initial_proxies():
    if not os.path.exists("proxies.txt"):
        return
    async with get_db_session() as db:
        with open("proxies.txt", "r") as f:
            for line in f:
                url = line.strip()
                if url:
                    try:
                        await db.execute("INSERT OR IGNORE INTO proxies (url) VALUES (?)", (url,))
                    except: pass
        await db.commit()

async def background_worker():
    while True:
        logger.info(f"Starting background check cycle...")
        await run_checker_cycle(target_url=DEFAULT_TARGET)
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await load_initial_proxies()
    asyncio.create_task(background_worker())
    yield

app = FastAPI(title="ProxyFlow API", lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "ProxyFlow API is running",
        "endpoints": {
            "get_proxy": "/get-proxy",
            "export": "/export",
            "stats": "/dashboard",
            "add_proxies": "/proxies",
            "trigger_check": "/check-now"
        }
    }

@app.get("/export", response_class=PlainTextResponse)
async def export_proxies():
    """Returns all active proxies as a plain text list."""
    async with get_db_session() as db:
        cursor = await db.execute("SELECT url FROM proxies WHERE status='active'")
        rows = await cursor.fetchall()
        content = "\n".join([row["url"] for row in rows])
        return content

@app.get("/get-proxy")
async def get_best_proxy():
    async with get_db_session() as db:
        cursor = await db.execute(
            "SELECT url, latency FROM proxies WHERE status='active' ORDER BY latency ASC LIMIT 1"
        )
        row = await cursor.fetchone()
        if row:
            return {"proxy": row["url"], "latency": row["latency"]}
        raise HTTPException(status_code=404, detail="No active proxies available")

@app.get("/dashboard", response_model=DashboardStats)
async def get_dashboard():
    async with get_db_session() as db:
        cursor = await db.execute("SELECT COUNT(*) as total FROM proxies")
        total = (await cursor.fetchone())["total"]
        cursor = await db.execute("SELECT status, COUNT(*) as count FROM proxies GROUP BY status")
        status_map = {row["status"]: row["count"] for row in (await cursor.fetchall())}
        cursor = await db.execute("SELECT AVG(latency) as avg_lat FROM proxies WHERE status='active'")
        avg_lat = (await cursor.fetchone())["avg_lat"] or 0.0
        cursor = await db.execute("SELECT MAX(last_check) as last_val FROM proxies")
        last_val = (await cursor.fetchone())["last_val"]
        cursor = await db.execute("SELECT url, latency, status FROM proxies ORDER BY last_check DESC LIMIT 10")
        recent = [dict(row) for row in (await cursor.fetchall())]
        return {
            "total": total,
            "active": status_map.get("active", 0),
            "dead": status_map.get("dead", 0),
            "unknown": status_map.get("unknown", 0),
            "avg_latency": round(avg_lat, 3),
            "last_cycle_at": last_val,
            "fastest_proxies": recent
        }

@app.post("/proxies")
async def add_proxies(urls: List[str]):
    added = 0
    async with get_db_session() as db:
        for url in urls:
            try:
                await db.execute("INSERT OR IGNORE INTO proxies (url) VALUES (?)", (url.strip(),))
                added += 1
            except: continue
        await db.commit()
    return {"message": f"Successfully added {added} proxies"}

@app.post("/check-now")
async def trigger_check(target: HealthCheckTarget, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_checker_cycle, target_url=target.url)
    return {"message": "Check cycle initiated"}

@app.delete("/proxies")
async def delete_proxies(urls: List[str]):
    """
    Removes specific proxy URLs from the database.
    """
    removed = 0
    async with get_db_session() as db:
        for url in urls:
            cursor = await db.execute("DELETE FROM proxies WHERE url = ?", (url.strip(),))
            if cursor.rowcount > 0:
                removed += 1
        await db.commit()
    return {"message": f"Successfully removed {removed} proxies from the pool"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
