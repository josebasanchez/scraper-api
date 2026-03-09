# Scraper API

API para scrapear URLs internas de un dominio y guardar los resultados en SQLite. Incluye autenticación JWT con OAuth2 Password Flow y documentación Swagger.

---

## 🔹 Requisitos

- Python 3.10+
- Pip
- Dependencias (instalar con `pip install -r requirements.txt`)

---

## 🔹 Instalación

```bash
git clone https://github.com/josebasanchez/scraper-api
cd scraper-api
pip install -r requirements.txt
```

---

## 🔹 Ejecución

```bash
python app.py
```

La API estará disponible en:

- API: `http://localhost:5000/api`
- Swagger UI: `http://localhost:5000/swagger`

---

## 🔹 Endpoints principales

### 1. Obtener token (OAuth2 Password Flow)

**POST** `/api/token`  

**Parámetros (form-data):**

| Campo     | Descripción            | Ejemplo      |
|-----------|-----------------------|-------------|
| username  | Usuario válido         | admin       |
| password  | Contraseña del usuario | admin123    |

**Respuesta:**

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

**Ejemplo con curl:**

```bash
curl -X POST http://localhost:5000/api/token \
  -d "username=admin&password=admin123"
```

---

### 2. Scrapeo de URLs

**POST** `/api/getScrap`  

**Headers:**

```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Body:**

```json
{
  "domain": "https://www.innotu.com"
}
```

**Respuesta:**

```json
{
  "domain": "https://www.innotu.com",
  "total_urls": 99,
  "urls": [
    "https://www.innotu.com/",
    "https://www.innotu.com/contact",
    "https://www.innotu.com/blog"
  ]
}
```

**Ejemplo con curl:**

```bash
curl -X POST http://localhost:5000/api/getScrap \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"domain":"https://www.innotu.com"}'
```

---

## 🔹 Swagger UI

1. Accede a `http://localhost:5000/swagger`
2. Haz clic en **Authorize** e introduce tu token obtenido de `/api/token`.
3. Ejecuta `getScrap` desde la UI con el token válido.


---

## 🔹 Seguridad

- La API requiere token JWT en el header `Authorization` para `/getScrap`.
- Tokens caducan en 1 hora.
- Las credenciales están hardcodeadas (`admin/admin123`). Se pueden reemplazar por una base de datos de usuarios en producción.

---

## 🔹 Base de datos

- SQLite: `urls.db`
- Tabla `UrlScrape`:
  - `domain` (string)
  - `url` (string)
  - `timestamp` (datetime)

