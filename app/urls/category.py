from flask import Blueprint
from flask_restful import Api
from app.resources.category import CategoryListResource, CategoryDetailResource


category_bp = Blueprint("category", __name__)
category_api = Api(category_bp)

# Register endpoints
category_api.add_resource(CategoryListResource, "", endpoint="categories")
category_api.add_resource(CategoryDetailResource, "/<id>", endpoint="category-detail")
