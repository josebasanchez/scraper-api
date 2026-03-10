import mysql.connector

def crear_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )

    cursor = conn.cursor()

    cursor.execute("""
        CREATE DATABASE IF NOT EXISTS scraper-api
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
    """)

    cursor.execute("USE scraper-api")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INT AUTO_INCREMENT PRIMARY KEY,
            domain VARCHAR(255),
            tipo VARCHAR(20),
            url TEXT,
            timestamp DATETIME,
            INDEX idx_domain (domain(100))
        )
    """)

    conn.commit()
    conn.close()