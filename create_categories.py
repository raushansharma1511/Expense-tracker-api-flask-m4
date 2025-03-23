from app.extensions import db
from app.utils.logger import logger
from app.models.user import User, UserRole
from app.models.category import Category
from app import create_app


def create_default_categories():
    """
    Create default predefined categories
    """

    # Check if predefined categories already exist
    existing_predefined = Category.query.filter_by(
        is_predefined=True, is_deleted=False
    ).count()
    if existing_predefined > 0:
        logger.info(f"Predefined categories already exist: {existing_predefined} found")
        print(f"Predefined categories already exist: {existing_predefined} found")
        return 0

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

    # Create each category
    categories_created = 0
    for category_name in default_categories:
        category = Category(
            name=category_name,
            user_id=admin_user.id,
            is_predefined=True,
        )
        db.session.add(category)
        categories_created += 1

    db.session.commit()

    logger.info(f"Created {categories_created} predefined categories")
    print(f"\nCreated {categories_created} predefined categories:")
    for category_name in default_categories:
        print(f"- {category_name}")
    print()

    return categories_created


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_default_categories()
