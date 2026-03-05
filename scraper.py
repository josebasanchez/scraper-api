import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10

def normalizar(url):
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), p.params, p.query, ""))

def misma_web(url, base_url):
    return urlparse(url).netloc == urlparse(base_url).netloc

def extraer_urls(url, base_url):
    urls = set()
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
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

def scrapear(base_url, max_workers=10):
    visitadas = set()
    pendientes = set([base_url])
    resultado = []
    while pendientes:
        batch = list(pendientes)
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