from flask import Flask, request
from flask_smorest import Api, Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from urllib.parse import urlparse
from scraper import scrapear, scrapear_pagina, post_check_url, misma_web, build_url_items
from datetime import datetime
from marshmallow import Schema, fields
from auth import login, verificar_token
from db_mysql import crear_db
from scraper import guardar_urls

crear_db()

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
class LinksResponseSchema(Schema):
    domain = fields.String(metadata={"example": "https://www.innotu.com"})
    total_urls = fields.Integer(metadata={"example": 10})
    urls = fields.List(fields.String())
class LinksRequestSchema(Schema):
    domain = fields.String(required=True)
class PostCheckRequestSchema(Schema):
    domain = fields.String(required=True)
    url = fields.String(required=True)
class PostCheckResponseSchema(Schema):
    url = fields.String()
    ok = fields.Boolean()
    status_code = fields.Integer(allow_none=True)
class TokenRequestSchema(Schema):
    username = fields.String(required=True, metadata={"location": "form"})
    password = fields.String(required=True, metadata={"location": "form"})
class TokenResponseSchema(Schema):
    access_token = fields.String(metadata={"example": "eyJhbGc..."})
    token_type = fields.String(metadata={"example": "bearer"})
app = Flask(__name__)
app.config["API_TITLE"] = "Scraper API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/api"
api = Api(app)
api.spec.components.security_scheme(
    "BearerAuth",
    {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
)
app.config["OPENAPI_URL_PREFIX"] = "/api"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
blp = Blueprint("scraper", "scraper", url_prefix="/api")
SWAGGER_URL = "/swagger"
API_URL = "/api/openapi.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Scraper API",
        "oauth2RedirectUrl": "http://localhost:5000/swagger/oauth2-redirect.html"
    }
)
@blp.route("/token", methods=["POST"])
@blp.arguments(TokenRequestSchema, location="form")
@blp.response(200, TokenResponseSchema)
@blp.doc(
    summary="Login OAuth2",
    description="Obtiene un token JWT usando OAuth2 Password Flow"
)
def api_token(data):
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    token = login(username, password)
    if not token:
        return {"error": "Usuario o contraseña incorrectos"}, 401
    return {
        "access_token": token,
        "token_type": "bearer"
    }
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
def url_segura(url):
    netloc = urlparse(url).hostname
    if not netloc:
        return False
    privadas = ("127.", "10.", "192.168.", "localhost")
    return not any(netloc.startswith(p) for p in privadas)
@blp.route("/getScrap", methods=["POST"])
@blp.arguments(ScrapRequestSchema)
@blp.response(200, ScrapResponseSchema)
@blp.doc(
    summary="Scraping de URLs de un dominio",
    description="""
        Recibe un dominio y realiza scraping para obtener todas las URLs internas.
        Proceso:
        - valida el dominio recibido
        - ejecuta el scraper
        - guarda las URLs en la base de datos
        - devuelve el listado encontrado
        Requiere autenticación con **Bearer Token** en el header:
        Authorization: Bearer <token>
        """,
    security=[{"BearerAuth": []}]
)
def getScrap(data):
    token_header = request.headers.get("Authorization", "").strip()
    if not token_header or not token_header.lower().startswith("bearer "):
        return {"error": "Token inválido o no proporcionado"}, 401
    token = token_header[7:]
    if not verificar_token(token):
        return {"error": "Token inválido"}, 401
    domain = data["domain"].strip()
    if not domain:
        return {"error": "Debes enviar un domain"}, 400
    if not urlparse(domain).scheme:
        domain = "https://" + domain
    if not url_segura(domain):
        return {"error": "URL no segura"}, 400
    urls_con_timestamp = scrapear(domain)
    guardar_urls(domain, urls_con_timestamp)
    return {
        "domain": domain,
        "total_urls": len(urls_con_timestamp),
        "urls": [item["url"] for item in urls_con_timestamp],
    }

@blp.route("/getLinks", methods=["POST"])
@blp.arguments(LinksRequestSchema)
@blp.response(200, LinksResponseSchema)
@blp.doc(
    summary="Scraping de enlaces de una sola pagina",
    description="""
        Recibe un dominio/pagina y devuelve los enlaces internos encontrados
        en esa pagina, sin recursion.
        Requiere autenticacion con **Bearer Token** en el header:
        Authorization: Bearer <token>
        """,
    security=[{"BearerAuth": []}]
)
def getLinks(data):
    token_header = request.headers.get("Authorization", "").strip()
    if not token_header or not token_header.lower().startswith("bearer "):
        return {"error": "Token invalido o no proporcionado"}, 401
    token = token_header[7:]
    if not verificar_token(token):
        return {"error": "Token invalido"}, 401
    domain = data["domain"].strip()
    if not domain:
        return {"error": "Debes enviar un domain"}, 400
    if not urlparse(domain).scheme:
        domain = "https://" + domain
    if not url_segura(domain):
        return {"error": "URL no segura"}, 400
    urls = scrapear_pagina(domain)
    items = build_url_items(domain, urls)
    if items:
        guardar_urls(domain, items)
    return {
        "domain": domain,
        "total_urls": len(urls),
        "urls": urls
    }

@blp.route("/postCheck", methods=["POST"])
@blp.arguments(PostCheckRequestSchema)
@blp.response(200, PostCheckResponseSchema)
@blp.doc(
    summary="POST a una URL y guarda en base de datos",
    description="""
        Hace un POST a la URL indicada, utiliza BeautifulSoup para parsear
        la respuesta y guarda la URL en base de datos.
        Requiere autenticacion con **Bearer Token** en el header:
        Authorization: Bearer <token>
        """,
    security=[{"BearerAuth": []}]
)
def postCheck(data):
    token_header = request.headers.get("Authorization", "").strip()
    if not token_header or not token_header.lower().startswith("bearer "):
        return {"error": "Token invalido o no proporcionado"}, 401
    token = token_header[7:]
    if not verificar_token(token):
        return {"error": "Token invalido"}, 401
    domain = data["domain"].strip()
    url = data["url"].strip()
    if not domain or not url:
        return {"error": "Debes enviar domain y url"}, 400
    if not urlparse(domain).scheme:
        domain = "https://" + domain
    if not urlparse(url).scheme:
        url = "https://" + url
    if not url_segura(domain) or not url_segura(url):
        return {"error": "URL no segura"}, 400
    if not misma_web(url, domain):
        return {"error": "URL fuera de dominio"}, 400
    return post_check_url(url, domain)
api.register_blueprint(blp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
