from app.extensions import db
from app.utils.logger import logger
from app.models.user import User, UserRole
from app import create_app
from app.extensions import bcrypt


def create_admin_user(
    username="adminuser",
    email="adminuser@gmail.com",
    password="Admin@123",
    name="Admin User",
):
    """
    Create default admin user if no admin exists
    """
    # Check if admin user already exists
    admin = User.query.filter_by(role=UserRole.ADMIN, is_deleted=False).first()
    if admin:
        logger.info(f"Admin user already exists: {admin.email}")
        print(f"Admin user already exists: {admin.email}")
        return admin

    # Create new admin user
    admin_user = User(
        username=username,
        name=name,
        email=email,
        password=bcrypt.generate_password_hash(password).decode("utf-8"),
        role=UserRole.ADMIN,
        is_verified=True,
    )

    db.session.add(admin_user)
    db.session.commit()

    logger.info(f"Created admin user: {admin_user.email}")
    print(f"\nAdmin user created successfully:")
    print(f"Email: {admin_user.email}")
    print(f"Password: {password}")
    print("IMPORTANT: Please change this password after first login!\n")

    return admin_user


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_admin_user()
