from flask import Blueprint
from flask_restful import Api, Resource
from sqlalchemy.exc import OperationalError
from app.extensions import db

health_bp = Blueprint("health", __name__)
health_api = Api(health_bp)


class HealthCheckResource(Resource):
    def get(self):
        try:
            from sqlalchemy import text

            db.session.execute(text("SELECT 1;"))

            tables = db.session.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
                )
            ).fetchall()
            num_tables = len(tables)

            if num_tables == 0:
                return {"message": "No tables found in the database"}, 500

            return {"message": "Database is healthy", "table_count": num_tables}, 200

        except OperationalError as e:
            return {"message": "Database connection failed", "error": str(e)}, 500

        except Exception as e:
            return {"message": "An unexpected error occurred", "error": str(e)}, 500


health_api.add_resource(HealthCheckResource, "/health-check")
