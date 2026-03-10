import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import mysql.connector

HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10
session = requests.Session()
session.headers.update(HEADERS)

def guardar_urls(domain, urls):

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="scraper-api"
    )

    cursor = conn.cursor()

    sql = """
    INSERT INTO urls (domain, tipo, url, timestamp)
    VALUES (%s,%s,%s,%s)
    """

    valores = [(domain, u["url"], u["tipo"], u["timestamp"]) for u in urls]

    cursor.executemany(sql, valores)

    conn.commit()
    conn.close()
def detectar_tipo(url):
    url = url.lower()

    if url.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")):
        return "imagen"

    if url.endswith(".pdf"):
        return "pdf"

    if url.endswith((".zip", ".rar", ".7z")):
        return "archivo"

    if url.endswith((".mp4", ".webm", ".avi")):
        return "video"

    if url.endswith((".js", ".css")):
        return "recurso"

    return "html"
def normalizar(url):
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), p.params, p.query, ""))
def misma_web(url, base_url):
    u = urlparse(url).netloc.lower()
    b = urlparse(base_url).netloc.lower()
    if u.startswith("www."):
        u = u[4:]
    if b.startswith("www."):
        b = b[4:]
    return u == b
def extraer_urls(url, base_url):
    urls = set()
    try:
        r = session.get(url, timeout=TIMEOUT)
        r.raise_for_status()
    except:
        return urls
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:")):
            continue
        url_abs = urljoin(url, href)
        if misma_web(url_abs, base_url):
            urls.add(normalizar(url_abs))
    return urls
def scrapear(base_url, max_workers=50):
    visitadas = set()
    pendientes = set([base_url])
    resultado = []
    while pendientes:
        batch = [u for u in pendientes if u not in visitadas]
        pendientes.clear()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(extraer_urls, url, base_url): url for url in batch}
            for future in as_completed(future_to_url):
                url_base = future_to_url[future]
                url_base_n = normalizar(url_base)
                if url_base_n not in visitadas:
                    visitadas.add(url_base_n)
                    resultado.append({
                        "url": url_base_n,
                        "tipo": detectar_tipo(url_base_n),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                try:
                    nuevas = future.result()
                except Exception:
                    nuevas = set()
                for u in nuevas:
                    u_n = normalizar(u)
                    if u_n not in visitadas:
                        pendientes.add(u_n)
    return sorted(resultado, key=lambda x: x["timestamp"])
