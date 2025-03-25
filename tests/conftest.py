import os
import sys
import pytest
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
load_dotenv()

# Set environment to testing
os.environ["FLASK_ENV"] = "testing"

from app.config import TestConfig
from app.models.user import User, UserRole, ParentChildRelation
from app.models.category import Category
from app.models.wallet import Wallet
from app.models.interwallet_transaction import InterWalletTransaction
from app.extensions import db, bcrypt
from app.models.transaction import Transaction, TransactionType
from app.utils.enums import TransactionFrequency
from app.models.recurring_transaction import RecurringTransaction

from app.models.budget import Budget
from app import create_app


# @pytest.fixture(scope="session", autouse=True)
# def setup_database():
#     """Set up test database once per test session."""
#     from setup_testdb import setup_test_database

#     setup_test_database()


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing."""
    # Use your existing app factory with test config
    test_app = create_app(TestConfig)

    # Create application context
    with test_app.app_context():
        db.create_all()

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def db_session(app):
    """Provide a session-wide database fixture."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()  # Start a transaction
        db.session.remove()  # Remove previous session
        db.session.configure(
            bind=connection, autoflush=False
        )  # Use transaction-bound session

        yield db.session  # Provide session to tests

        db.session.rollback()  # Rollback instead of commit
        connection.close()


@pytest.fixture
def client(app):
    """Flask test client for API requests."""
    return app.test_client()


@pytest.fixture
def test_user(db_session):
    """Create a fresh test user for each test."""

    # Create new test user
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="user@test.com",
        password=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
        name="Test User",
        role=UserRole.USER,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def test_user2(db_session):
    """Create a fresh test user for each test."""

    # Create new test user
    user = User(
        id=uuid.uuid4(),
        username="testuser2",
        email="user@test2.com",
        password=bcrypt.generate_password_hash("Password123!").decode("utf-8"),
        name="Test User2",
        role=UserRole.USER,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def admin_user(db_session):
    """Create a fresh admin user for each test."""

    # Create new admin user
    admin = User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@test.com",
        password=bcrypt.generate_password_hash("Admin123!").decode("utf-8"),
        name="Admin User",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    yield admin

    db_session.delete(admin)
    db_session.commit()


@pytest.fixture
def child_user(db_session, test_user):
    """Create a child user with parent-child relationship."""

    # Create child user
    child = User(
        id=uuid.uuid4(),
        username="childuser",
        email="child@test.com",
        password=bcrypt.generate_password_hash("ChildPass123!").decode("utf-8"),
        name="Child User",
        role=UserRole.CHILD_USER,
        is_verified=True,
    )
    db_session.add(child)

    # Create parent-child relation
    relation = ParentChildRelation(parent_id=test_user.id, child_id=child.id)
    db_session.add(relation)
    db_session.commit()
    db_session.refresh(child)

    yield child

    # Clean up in reverse order (relation first, then child)
    relation = (
        db_session.query(ParentChildRelation).filter_by(child_id=child.id).first()
    )
    if relation:
        db_session.delete(relation)

    db_session.delete(child)
    db_session.commit()


@pytest.fixture
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_token(client):
    """Get auth token for the regular test user."""
    response = client.post(
        "/api/auth/login",
        json={"username": "user@test.com", "password": "Password123!"},
    )
    data = response.get_json()
    return data["access_token"]


@pytest.fixture
def auth_token2(client):
    """Get auth token for the regular test user2."""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser2", "password": "Password123!"},
    )
    data = response.get_json()
    return data["access_token"]


@pytest.fixture
def admin_token(client):
    """Get auth token for the admin user."""
    response = client.post(
        "/api/auth/login", json={"username": "admin@test.com", "password": "Admin123!"}
    )
    data = response.get_json()
    return data["access_token"]


@pytest.fixture
def auth_headers(test_user, auth_token):
    """Create authorization headers with user token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def auth_headers_user2(test_user2, auth_token2):
    """Create authorization headers with user token."""
    return {"Authorization": f"Bearer {auth_token2}"}


@pytest.fixture
def admin_headers(admin_user, admin_token):
    """Create authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def child_token(client):
    """Get auth token for the child user."""
    response = client.post(
        "/api/auth/login",
        json={"username": "child@test.com", "password": "ChildPass123!"},
    )
    data = response.get_json()
    return data["access_token"]


@pytest.fixture
def child_headers(child_user, child_token):
    """Create authorization headers with child token."""
    return {"Authorization": f"Bearer {child_token}"}


@pytest.fixture
def predefined_category(db_session, admin_user):
    """Create a predefined category (created by admin)."""

    # Create predefined category
    category = Category(
        id=uuid.uuid4(),
        name="Test predefined",
        user_id=admin_user.id,
        is_predefined=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    yield category

    db_session.delete(category)
    db_session.commit()


@pytest.fixture
def user_category(db_session, test_user):
    """Create a regular user category."""
    # Create user category
    category = Category(
        id=uuid.uuid4(),
        name="Test category",
        user_id=test_user.id,
        is_predefined=False,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    yield category

    db_session.delete(category)
    db_session.commit()


@pytest.fixture
def child_category(db_session, child_user):
    """Create a child user category."""
    # Create child category
    category = Category(
        id=uuid.uuid4(),
        name="Child category",
        user_id=child_user.id,
        is_predefined=False,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    yield category

    db_session.delete(category)
    db_session.commit()


@pytest.fixture
def user_wallet(db_session, test_user):
    """Create a wallet for the test user."""
    wallet = Wallet(
        id=uuid.uuid4(),
        name="Test wallet",
        balance=0.00,
        user_id=test_user.id,
    )
    db_session.add(wallet)
    db_session.commit()
    db_session.refresh(wallet)

    yield wallet

    db_session.delete(wallet)
    db_session.commit()


@pytest.fixture
def second_wallet(db_session, test_user):
    """Create a persistent second wallet for the test user."""
    wallet = Wallet(
        id=uuid.uuid4(),
        name="Second wallet",
        balance=100.00,
        user_id=test_user.id,
    )
    db_session.add(wallet)
    db_session.commit()
    yield wallet
    db_session.delete(wallet)
    db_session.commit()


@pytest.fixture
def child_wallet(db_session, child_user):
    """Create a wallet for the child user."""
    wallet = Wallet(
        id=uuid.uuid4(),
        name="Child wallet",
        balance=0.00,
        user_id=child_user.id,
    )
    db_session.add(wallet)
    db_session.commit()
    db_session.refresh(wallet)

    yield wallet

    db_session.delete(wallet)
    db_session.commit()


@pytest.fixture
def child_second_wallet(db_session, child_user):
    """Create a persistent second wallet for the child user."""
    wallet = Wallet(
        id=uuid.uuid4(),
        name="Child second wallet",
        balance=100.00,
        user_id=child_user.id,
    )
    db_session.add(wallet)
    db_session.commit()
    yield wallet
    db_session.delete(wallet)
    db_session.commit()


@pytest.fixture
def mock_check_budget(mocker):
    """Mock check_budget_thresholds.delay to do nothing."""
    return mocker.patch(
        "app.tasks.budget.check_budget_thresholds.delay", return_value=None
    )


@pytest.fixture
def user_transaction(db_session, test_user, user_wallet, user_category):
    """Create a transaction for the test user (EXPENSE) with wallet balance update."""
    transaction = Transaction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        wallet_id=user_wallet.id,
        category_id=user_category.id,
        amount=50.00,
        type=TransactionType.DEBIT,
        description="Test expense",
    )
    # Update wallet balance as per create_transaction logic
    user_wallet.update_balance(-transaction.amount)  # DEBIT decreases balance
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    db_session.refresh(user_wallet)  # Ensure wallet is refreshed
    yield transaction
    # Cleanup: Reverse the balance update to maintain fixture isolation
    user_wallet.update_balance(transaction.amount)  # Restore balance
    db_session.delete(transaction)
    db_session.commit()


@pytest.fixture
def child_transaction(db_session, child_user, child_wallet, child_category):
    """Create a transaction for the child user (EXPENSE) with wallet balance update."""
    transaction = Transaction(
        id=uuid.uuid4(),
        user_id=child_user.id,
        wallet_id=child_wallet.id,
        category_id=child_category.id,
        type=TransactionType.DEBIT,
        amount=30.00,
        description="Child expense",
    )
    # Update wallet balance
    child_wallet.update_balance(-transaction.amount)  # DEBIT decreases balance
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    db_session.refresh(child_wallet)
    yield transaction
    # Cleanup
    child_wallet.update_balance(transaction.amount)  # Restore balance
    db_session.delete(transaction)
    db_session.commit()


@pytest.fixture
def user_income_transaction(db_session, test_user, user_wallet, user_category):
    """Create an income transaction for the test user with wallet balance update."""
    transaction = Transaction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        wallet_id=user_wallet.id,
        category_id=user_category.id,
        amount=100.00,
        type=TransactionType.CREDIT,
        description="Test income",
    )
    # Update wallet balance
    user_wallet.update_balance(transaction.amount)  # CREDIT increases balance
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    db_session.refresh(user_wallet)
    yield transaction
    # Cleanup
    user_wallet.update_balance(-transaction.amount)  # Restore balance
    db_session.delete(transaction)
    db_session.commit()


@pytest.fixture
def user_budget(db_session, test_user, user_wallet, user_category):
    """Create a budget for the test user."""
    current_year = datetime.now(timezone.utc).year
    current_month = datetime.now(timezone.utc).month
    budget = Budget(
        id=uuid.uuid4(),
        user_id=test_user.id,
        category_id=user_category.id,
        amount=Decimal("100.00"),
        spent_amount=Decimal("0.00"),
        month=current_month,
        year=current_year,
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    yield budget
    db_session.delete(budget)
    db_session.commit()


@pytest.fixture
def child_budget(db_session, child_user, child_wallet, child_category):
    """Create a budget for the child user."""
    current_year = datetime.now(timezone.utc).year
    current_month = datetime.now(timezone.utc).month
    budget = Budget(
        id=uuid.uuid4(),
        user_id=child_user.id,
        category_id=child_category.id,
        amount=Decimal("50.00"),
        spent_amount=Decimal("0.00"),
        month=current_month,
        year=current_year,
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    yield budget
    db_session.delete(budget)
    db_session.commit()


@pytest.fixture
def budget_data(test_user, user_category):
    """Sample budget data for creation."""
    current_year = datetime.now(timezone.utc).year
    current_month = datetime.now(timezone.utc).month
    return {
        "user_id": str(test_user.id),
        "category_id": str(user_category.id),
        "amount": "100.00",
        "month": current_month,
        "year": current_year,
    }


@pytest.fixture
def user_interwallet_transaction(db_session, test_user, user_wallet, second_wallet):
    """Create an interwallet transaction for the test user."""
    transaction = InterWalletTransaction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        source_wallet_id=second_wallet.id,
        destination_wallet_id=user_wallet.id,
        amount=Decimal("50.00"),
        description="Test transfer",
    )
    db_session.add(transaction)
    db_session.commit()
    transaction.apply_to_wallets()
    db_session.commit()
    db_session.refresh(transaction)
    db_session.refresh(user_wallet)
    db_session.refresh(second_wallet)
    yield transaction
    transaction.reverse_from_wallets()
    db_session.delete(transaction)
    db_session.commit()


@pytest.fixture
def child_interwallet_transaction(
    db_session, child_user, child_wallet, child_second_wallet
):
    """Create an interwallet transaction for the child user."""
    transaction = InterWalletTransaction(
        id=uuid.uuid4(),
        user_id=child_user.id,
        source_wallet_id=child_second_wallet.id,
        destination_wallet_id=child_wallet.id,
        amount=Decimal("30.00"),
        description="Child transfer",
    )
    db_session.add(transaction)
    db_session.commit()
    transaction.apply_to_wallets()
    db_session.commit()
    db_session.refresh(transaction)
    db_session.refresh(child_wallet)
    db_session.refresh(child_second_wallet)
    yield transaction
    transaction.reverse_from_wallets()
    db_session.delete(transaction)
    db_session.commit()


@pytest.fixture
def interwallet_transaction_data(test_user, user_wallet, second_wallet):
    """Sample data for creating an interwallet transaction."""
    data = {
        "user_id": str(test_user.id),
        "source_wallet_id": str(second_wallet.id),
        "destination_wallet_id": str(user_wallet.id),
        "amount": "50.00",
        "description": "Test transfer",
    }
    yield data


@pytest.fixture
def recurring_transaction(db_session, test_user, user_wallet, user_category):
    """Create a recurring transaction for the test user."""
    tx = RecurringTransaction(
        amount=50.00,
        description="Monthly bill",
        type=TransactionType.DEBIT,
        frequency=TransactionFrequency.MONTHLY,
        start_at=datetime.now(timezone.utc) + timedelta(days=1),
        next_execution_at=datetime.now(timezone.utc) + timedelta(days=1),
        user_id=test_user.id,
        wallet_id=user_wallet.id,
        category_id=user_category.id,
    )
    db_session.add(tx)
    db_session.commit()
    yield tx
    db_session.delete(tx)
    db_session.commit()


@pytest.fixture
def child_recurring_transaction(db_session, child_user, child_wallet, child_category):
    """Create a recurring transaction for the child user."""
    tx = RecurringTransaction(
        amount=30.00,
        description="Weekly child expense",
        type=TransactionType.DEBIT,
        frequency=TransactionFrequency.WEEKLY,
        start_at=datetime.now(timezone.utc) + timedelta(days=1),
        next_execution_at=datetime.now(timezone.utc) + timedelta(days=1),
        user_id=child_user.id,
        wallet_id=child_wallet.id,
        category_id=child_category.id,
    )
    db_session.add(tx)
    db_session.commit()
    yield tx
    db_session.delete(tx)
    db_session.commit()


@pytest.fixture
def recurring_transaction_data(test_user, user_wallet, user_category):
    """Sample data for creating a recurring transaction."""
    return {
        "amount": 20.00,
        "description": "Test recurring transaction",
        "type": "DEBIT",
        "frequency": "DAILY",
        "start_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "user_id": str(test_user.id),
        "wallet_id": str(user_wallet.id),
        "category_id": str(user_category.id),
    }
