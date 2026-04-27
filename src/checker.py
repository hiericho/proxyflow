import asyncio
import aiohttp
import time
import logging
import random
from datetime import datetime
from src.database import get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

from urllib.parse import urlparse

async def check_proxy(proxy_url: str, target_url: str = "https://www.google.com", timeout_sec: int = 10):
    """
    Checks a single proxy against a target and returns (status, latency)
    Supports http://user:pass@host:port
    """
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    start_time = time.perf_counter()
    
    proxy_auth = None
    try:
        parsed = urlparse(proxy_url)
        if parsed.username and parsed.password:
            proxy_auth = aiohttp.BasicAuth(parsed.username, parsed.password)
            # aiohttp proxy param shouldn't include credentials if using proxy_auth
            # but usually it handles both. To be safe:
            clean_proxy_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        else:
            clean_proxy_url = proxy_url

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(
                target_url, 
                proxy=clean_proxy_url, 
                proxy_auth=proxy_auth,
                allow_redirects=True
            ) as response:
                if response.status == 200:
                    latency = time.perf_counter() - start_time
                    return "active", latency
                else:
                    return "dead", 999.0
    except Exception:
        return "dead", 999.0

async def update_proxy_status(db, url, status, latency):
    await db.execute(
        "UPDATE proxies SET status = ?, latency = ?, last_check = ? WHERE url = ?",
        (status, latency, datetime.now(), url)
    )
    await db.commit()

async def run_checker_cycle(target_url: str = "https://www.google.com", concurrency: int = 50):
    """
    Main loop for checking proxies with controlled concurrency
    """
    async with get_db_session() as db:
        cursor = await db.execute("SELECT url FROM proxies")
        rows = await cursor.fetchall()
        
        if not rows:
            logger.info("No proxies found in database to check.")
            return

        semaphore = asyncio.Semaphore(concurrency)

        async def sem_check(url):
            async with semaphore:
                status, latency = await check_proxy(url, target_url=target_url)
                if status == "active":
                    logger.info(f"  [+] ACTIVE: {url} ({latency:.3f}s)")
                else:
                    logger.info(f"  [-] DEAD:   {url}")
                await update_proxy_status(db, url, status, latency)

        tasks = [sem_check(row["url"]) for row in rows]
        await asyncio.gather(*tasks)
        logger.info(f"Completed check cycle for {len(rows)} proxies against {target_url}.")
