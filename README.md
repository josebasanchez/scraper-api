# Scraper API

API para scrapear URLs internas y guardar resultados en MySQL. Incluye autenticacion JWT con OAuth2 Password Flow y Swagger.

## Requisitos

- Python 3.10+
- MySQL o MariaDB
- Pip

## Instalacion

```
pip install -r requirements.txt
```

## Ejecucion

```
python app.py
```

API en `http://localhost:5000/api`
Swagger en `http://localhost:5000/swagger`

## Endpoints

### Token

**POST** `/api/token`

Form-data:

- `username`
- `password`

### Scrapeo recursivo (original)

**POST** `/api/getScrap`

Body:

```json
{ "domain": "https://www.innotu.com" }
```

### Enlaces de una sola pagina (sin recursion)

**POST** `/api/getLinks`

Body:

```json
{ "domain": "https://www.innotu.com" }
```

### POST y guardar en base de datos

**POST** `/api/postCheck`

Body:

```json
{
  "domain": "https://www.innotu.com",
  "url": "https://www.innotu.com/contact"
}
```

## Seguridad

- JWT obligatorio en `Authorization: Bearer <token>`
- Token dura 1 hora
- Credenciales por defecto: `admin/admin123`

## Base de datos

- Base: `scraper_api`
- Tabla: `urls`
- Unico por dominio+url para evitar duplicados

## Integracion con VerSitemap

1. Ejecuta `python app.py`
2. En VerSitemap configura `ScraperApi:BaseUrl`
3. El front usa `getLinks` y `postCheck`
