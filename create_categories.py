from app.extensions import db
from app.utils.logger import logger
from app.models.user import User, UserRole
from app.models.category import Category
from app import create_app


def create_default_categories():
    """
    Create default predefined categories that don’t already exist in the database.
    """
    # Find admin user to associate categories with
    admin_user = User.query.filter_by(role=UserRole.ADMIN, is_deleted=False).first()
    if not admin_user:
        logger.error("No admin user found. Please create an admin user first.")
        print("Error: No admin user found. Please create an admin user first.")
        return 0

    # Define default categories
    default_categories = [
        "Salary",
        "Bonus",
        "Investment",
        "Food",
        "Groceries",
        "Shopping",
        "Entertainment",
        "Healthcare",
        "Education",
        "Travel",
        "Miscellaneous",
    ]

    # Check existing predefined categories
    existing_categories = Category.query.filter_by(
        is_predefined=True, is_deleted=False
    ).all()
    existing_names = {
        cat.name.lower() for cat in existing_categories
    }  # Case-insensitive comparison

    # Filter out categories that already exist
    categories_to_create = [
        name for name in default_categories if name.lower() not in existing_names
    ]

    if not categories_to_create:
        logger.info("All predefined categories already exist in the database.")
        print("All predefined categories already exist in the database.")
        return 0

    # Create missing categories
    categories_created = 0
    for category_name in categories_to_create:
        category = Category(
            name=category_name,
            user_id=admin_user.id,
            is_predefined=True,
        )
        db.session.add(category)
        categories_created += 1

    db.session.commit()

    logger.info(f"Created {categories_created} new predefined categories")
    print(f"\nCreated {categories_created} new predefined categories:")
    for category_name in categories_to_create:
        print(f"- {category_name}")
    print()

    return categories_created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_default_categories()
