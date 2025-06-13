import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
import os


class DatabaseManager:
    def __init__(self, db_path: str = "evaluaciones.db"):
        """
        Inicializa el gestor de base de datos.
        db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Crea la tabla si no existe"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    objetivo_estrategico TEXT NOT NULL,
                    indicador TEXT NOT NULL,
                    meta TEXT NOT NULL,
                    fuente_dato TEXT NOT NULL,
                    formula TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    respuesta_gemini TEXT NOT NULL,
                    calificacion TEXT,
                    recomendaciones TEXT
                )
            """)
            conn.commit()

    def guardar_evaluacion(
        self,
        objetivo_estrategico: str,
        indicador: str,
        meta: str,
        fuente_dato: str,
        formula: str,
        tipo: str,
        respuesta_gemini: str,
    ) -> int:
        """
        Guarda una nueva evaluación en la base de datos.
        Retorna el ID de la evaluación creada.
        """
        # Extraer calificación y recomendaciones de la respuesta
        calificacion, recomendaciones = self.extraer_calificacion_y_recomendaciones(
            respuesta_gemini
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evaluaciones 
                (objetivo_estrategico, indicador, meta, fuente_dato, formula, tipo, 
                 respuesta_gemini, calificacion, recomendaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    objetivo_estrategico,
                    indicador,
                    meta,
                    fuente_dato,
                    formula,
                    tipo,
                    respuesta_gemini,
                    calificacion,
                    recomendaciones,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def extraer_calificacion_y_recomendaciones(self, respuesta_gemini: str) -> tuple:
        """
        Extrae la calificación y recomendaciones de la respuesta de Gemini.
        Retorna una tupla (calificacion, recomendaciones)
        """
        calificacion = None
        recomendaciones = None

        # Buscar la calificación
        if "**Calificación:**" in respuesta_gemini:
            try:
                calificacion_parte = respuesta_gemini.split("**Calificación:**")[
                    1
                ].strip()
                # Tomar solo la primera línea que debería contener la calificación
                calificacion = calificacion_parte.split("\n")[0].strip()
                # Limpiar caracteres extra
                for palabra in ["Buena", "Regular", "Mala"]:
                    if palabra.lower() in calificacion.lower():
                        calificacion = palabra
                        break
            except:
                pass

        # Buscar las recomendaciones
        if "**Recomendaciones:**" in respuesta_gemini:
            try:
                recomendaciones_parte = respuesta_gemini.split("**Recomendaciones:**")[
                    1
                ]
                if "**Calificación:**" in recomendaciones_parte:
                    recomendaciones = recomendaciones_parte.split("**Calificación:**")[
                        0
                    ].strip()
                else:
                    recomendaciones = recomendaciones_parte.strip()
            except:
                pass

        return calificacion, recomendaciones

    def obtener_evaluaciones(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene las evaluaciones más recientes.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM evaluaciones 
                ORDER BY fecha_creacion DESC 
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas básicas de las evaluaciones.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total de evaluaciones
            cursor.execute("SELECT COUNT(*) as total FROM evaluaciones")
            total = cursor.fetchone()[0]

            # Distribución por calificación
            cursor.execute("""
                SELECT calificacion, COUNT(*) as cantidad 
                FROM evaluaciones 
                WHERE calificacion IS NOT NULL
                GROUP BY calificacion
            """)
            calificaciones = dict(cursor.fetchall())

            # Distribución por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad 
                FROM evaluaciones 
                GROUP BY tipo
            """)
            tipos = dict(cursor.fetchall())

            return {
                "total_evaluaciones": total,
                "por_calificacion": calificaciones,
                "por_tipo": tipos,
            }


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()
