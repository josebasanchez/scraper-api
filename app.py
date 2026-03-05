from flask import Flask, request
from flask_smorest import Api, Blueprint
from urllib.parse import urlparse
from scraper import scrapear
from models import db, UrlScrape
from datetime import datetime

app = Flask(__name__)

# --- Configuración de la API y Swagger ---
app.config["API_TITLE"] = "Scraper API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"

# Ruta base para los endpoints de la API
app.config["OPENAPI_URL_PREFIX"] = "/api"

# Configuración de la base de datos
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///urls.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
api = Api(app)
app.config["OPENAPI_URL_PREFIX"] = "/api"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
blp = Blueprint("scraper", "scraper", url_prefix="/api")
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/swagger"  # URL donde quieres la UI
API_URL = "/api/openapi.json"  # JSON generado por Flask-Smorest

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Scraper API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# --- Funciones auxiliares ---
def url_segura(url):
    netloc = urlparse(url).hostname
    if not netloc:
        return False
    privadas = ("127.", "10.", "192.168.", "localhost")
    return not any(netloc.startswith(p) for p in privadas)


# --- Endpoint con documentación Swagger ---
@blp.route("/getScrap", methods=["POST"])
@blp.doc(description="Recibe un dominio, scrapea sus URLs y devuelve un listado con timestamp.")
@blp.arguments(dict, location="json", example={"domain": "https://www.innotu.com"})
@blp.response(200, dict, description="Resultado del scrap: dominio, total de URLs y listado de URLs.")
def getScrap(data):
    domain = data.get("domain", "").strip()

    if not domain:
        return {"error": "Debes enviar un domain"}, 400

    if not urlparse(domain).scheme:
        domain = "https://" + domain

    if not url_segura(domain):
        return {"error": "URL no segura"}, 400

    urls_con_timestamp = scrapear(domain)

    registros = []
    for item in urls_con_timestamp:
        # Convertimos a datetime para SQLite
        registros.append(
            UrlScrape(
                domain=domain,
                url=item["url"],
                timestamp=datetime.fromisoformat(item["timestamp"])
            )
        )

    db.session.add_all(registros)
    db.session.commit()

    return {
        "domain": domain,
        "total_urls": len(urls_con_timestamp),
        "urls": [item["url"] for item in urls_con_timestamp]
    }


# --- Registro del blueprint ---
api.register_blueprint(blp)

# --- Crear tablas si no existen ---
with app.app_context():
    db.create_all()


# --- Arranque de la app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)