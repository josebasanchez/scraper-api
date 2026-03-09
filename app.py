from flask import Flask, request
from flask_smorest import Api, Blueprint
from urllib.parse import urlparse
from scraper import scrapear
from models import db, UrlScrape
from datetime import datetime
from marshmallow import Schema, fields
from auth import login, verificar_token


class ScrapRequestSchema(Schema):
    domain = fields.String(
        required=True,
        metadata={"example": "https://www.innotu.com"}
    )


class ScrapResponseSchema(Schema):
    domain = fields.String(metadata={"example": "https://www.innotu.com"})
    total_urls = fields.Integer(metadata={"example": 99})
    urls = fields.List(
        fields.String(),
        metadata={"example": [
            "https://www.innotu.com/",
            "https://www.innotu.com/contact",
            "https://www.innotu.com/blog"
        ]}
    )


app = Flask(__name__)
app.config["API_TITLE"] = "Scraper API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/api"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///urls.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
api = Api(app)
api.spec.components.security_scheme(
    "BearerAuth", {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
)
app.config["OPENAPI_URL_PREFIX"] = "/api"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
blp = Blueprint("scraper", "scraper", url_prefix="/api")
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/swagger"
API_URL = "/api/openapi.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Scraper API"}
)


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    user = data.get("user", "").strip()
    password = data.get("password", "").strip()
    if not user or not password:
        return {"error": "Debe enviar 'user' y 'password'"}, 400
    token = login(user, password)
    if not token:
        return {"error": "Usuario o contraseña incorrectos"}, 401
    return {"token": token}


app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def url_segura(url):
    netloc = urlparse(url).hostname
    if not netloc:
        return False
    privadas = ("127.", "10.", "192.168.", "localhost")
    return not any(netloc.startswith(p) for p in privadas)


@blp.route("/getScrap", methods=["POST"])
@blp.arguments(ScrapRequestSchema)
@blp.response(200, ScrapResponseSchema, description="Recibe un dominio, scrapea sus URLs y devuelve listado con timestamp. Requiere token Bearer en el header 'Authorization'.")
@blp.doc(security=[{"BearerAuth": []}])
def getScrap(data):
    token_header = request.headers.get("Authorization", "").strip()
    if not token_header or not token_header.lower().startswith("bearer "):
        return {"error": "Token inválido o no proporcionado"}, 401
    token = token_header[7:]
    if not verificar_token(token):
        return {"error": "Token inválido o no proporcionado"}, 401
    domain = data["domain"].strip()
    if not domain:
        return {"error": "Debes enviar un domain"}, 400
    if not urlparse(domain).scheme:
        domain = "https://" + domain
    if not url_segura(domain):
        return {"error": "URL no segura"}, 400
    urls_con_timestamp = scrapear(domain)
    registros = []
    for item in urls_con_timestamp:
        registros.append(
            UrlScrape(
                domain=domain,
                url=item["url"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
            )
        )
    db.session.add_all(registros)
    db.session.commit()
    return {
        "domain": domain,
        "total_urls": len(urls_con_timestamp),
        "urls": [item["url"] for item in urls_con_timestamp],
    }


api.register_blueprint(blp)
with app.app_context():
    db.create_all()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
