# Flask Expense Tracker API Documentation

## Table of Contents
- [Introduction](#introduction)
- [Authentication and User Management](#authentication-and-user-management)
- [Categories](#categories)
- [Wallets](#wallets)
- [Transactions](#transactions)
- [Inter-wallet Transactions](#inter-wallet-transactions)
- [Budgets](#budgets)
- [Recurring Transactions](#recurring-transactions)
- [Reports and Analytics](#reports-and-analytics)

## Introduction

The Flask Expense Tracker API is a robust financial management system designed to help users track their income and expenses. It provides a complete backend solution with secure authentication, comprehensive transaction management, and advanced reporting features.

---

## Authentication and User Management

The Authentication and User Management module provides comprehensive functionality for user registration, authentication, profile management, and hierarchical user relationships. The system supports role-based access control with three distinct user roles: Admin, Regular User, and Child User.

### Key Features

#### 1. User Roles
- **Admin**: Full access to manage all users, their financial data, and system resources. Can create additional admin accounts.
- **User**: Manage their own financial data (e.g., wallets, transactions, categories). View-only access to their child user’s assets (e.g., via `child_id` parameter in API requests).
- **Child User**: Restricted users created by parent users, with limited permissions to manage only their own data.

#### 2. JWT Authentication
- Secure token-based authentication using JWT (JSON Web Tokens)
- Includes access tokens (short-lived) and refresh tokens (longer-lived), with a role field encoded in the token claims
- Tokens must be included in the Authorization header as `Bearer <token>` for protected endpoints.

#### 3. User Registration and Verification
*Signup*
- Users register by providing their details (email, username, password, name) and an account verification link will be sent to their email for account verification.
- Once verification is done, the user account will be created, and a default wallet is created upon successful registration.
  
*Login*
- Users can log in using username or email and password.
- Returns access token (JWT) and refresh token upon successful login.

#### 4. Profile Management
- User profile updates (username, name, gender, date of birth)
- Users can change their own email with verification through OTP received on both current and new email.
- If an admin changes an email, a verification link will be sent to the new email, and after verification, the email will be updated.
- Password updates with current password verification.

#### 5. Parent-Child Relationships
- Parents can create and monitor child user accounts and their financial data.
- Children must verify their account for successful creation using the link sent to their email.
- Child accounts are linked through a dedicated parent-child relationship model.
- Each parent can have only one child user.

#### 6. Account Security
- Email verification for new accounts and email changes
- Password reset functionality with secure tokens
- Account deletion with password validation (password not required if an admin is deleting any user account).

### API Endpoints

#### List All Users (Admin Only)
**Endpoint:** `GET /api/users`  
- Retrieve a paginated list of all users (accessible only by admins)

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "username": "johndoe",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "USER",
      "is_verified": true,
      "is_deleted": false,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    },
    {
      "id": "98765432-fedc-ba98-7654-321098765432",
      "username": "janedoe",
      "email": "jane@example.com",
      "name": "Jane Doe",
      "role": "ADMIN",
      "is_verified": true,
      "is_deleted": false,
      "created_at": "2023-01-02T10:00:00Z",
      "updated_at": "2023-01-02T10:00:00Z"
    }
  ],
  "total_items": 50,
  "current_page": 1,
  "total_pages": 5,
  "per_page": 10
}
```

#### User Registration
**Endpoint:** `POST /api/auth/sign-up`  
- Register a new user account and send verification email

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "gender": "MALE",
  "date_of_birth": "1990-01-15"
}
```

**Response (200 OK):**
```json
{
  "message": "User registration request accepted. Please check your email to verify your account.",
  "token": "verification_token_string"
}
```

#### Email Verification
**Endpoint:** `GET /api/auth/verify-user/{token}`  
- Verify user's email using the token sent via email

**Response (200 OK):**
```json
{
  "message": "Your account has been verified successfully"
}
```

#### User Login
**Endpoint:** `POST /api/auth/login`  
- Authenticate user and generate access and refresh tokens

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Token Refresh
**Endpoint:** `POST /api/auth/refresh-token`  
- Generate a new access token using a valid refresh token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### User Logout
**Endpoint:** `POST /api/auth/logout`  
- Invalidate the current access token

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

#### Get User Profile
**Endpoint:** `GET /api/users/{id}`  
- Retrieve user profile information

**Response (200 OK):**
```json
{
  "id": "01234567-89ab-cdef-0123-456789abcdef",
  "username": "johndoe",
  "email": "john@example.com",
  "name": "John Doe",
  "role": "USER",
  "gender": "MALE",
  "date_of_birth": "1990-01-15",
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Update User Profile
**Endpoint:** `PATCH /api/users/{id}`  
- Update user profile information

**Request:**
```json
{
  "name": "John Smith",
  "gender": "MALE",
  "date_of_birth": "1990-01-20",
  "username": "johnsmith"
}
```

**Response (200 OK):**
```json
{
  "id": "01234567-89ab-cdef-0123-456789abcdef",
  "username": "johnsmith",
  "email": "john@example.com",
  "name": "John Smith",
  "role": "USER",
  "gender": "MALE",
  "date_of_birth": "1990-01-20",
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-02T10:30:00Z"
}
```

#### Update Password
**Endpoint:** `POST /api/users/{id}/update-password`  
- Update user's password

**Request:**
```json
{
  "current_password": "SecurePass123!",
  "new_password": "EvenMoreSecure456!",
  "confirm_password": "EvenMoreSecure456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully"
}
```

#### Request Email Change
**Endpoint:** `POST /api/users/{id}/update-email`  
- Initiate email change process by sending verification OTPs to both current and new email addresses

**Request:**
```json
{
  "new_email": "john.new@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Enter the otps sent to your current and new email addresses"
}
```

#### Confirm Email Change
**Endpoint:** `POST /api/users/{id}/update-email/confirm`  
- Confirm email change by verifying OTPs sent to both email addresses

**Request:**
```json
{
  "current_email_otp": "123456",
  "new_email_otp": "654321"
}
```

**Response (200 OK):**
```json
{
  "message": "Email address updated successfully"
}
```

#### Delete User Account
**Endpoint:** `DELETE /api/users/{id}`  
- Soft delete user account and related resources

**Request:**
```json
{
  "password": "SecurePass123!"
}
```

**Response (204 No Content)**

#### Request Password Reset
**Endpoint:** `POST /api/auth/reset-password`  
- Request a password reset link for a registered email

**Request:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset instructions have been sent to your email"
}
```

#### Reset Password with Token
**Endpoint:** `POST /api/auth/reset-password-confirm/{token}`  
- Reset password using token received via email

**Request:**
```json
{
  "password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully"
}
```

#### Create Child User
**Endpoint:** `POST /api/users/{id}/child`  
- Create a new child user linked to parent account

**Request:**
```json
{
  "username": "childsaccount",
  "email": "child@example.com",
  "password": "ChildPass123!",
  "name": "Child Name",
  "date_of_birth": "2010-05-15",
  "gender": "MALE"
}
```

**Response (200 OK):**
```json
{
  "message": "Child user registration initiated. Please check your email to verify the account."
}
```

#### Get Child User
**Endpoint:** `GET /api/users/{id}/child`  
- Retrieve child user linked to parent account

**Response (200 OK):**
```json
{
  "id": "98765432-fedc-ba98-7654-321098765432",
  "username": "childsaccount",
  "email": "child@example.com",
  "name": "Child Name",
  "role": "CHILD_USER",
  "gender": "MALE",
  "date_of_birth": "2010-05-15",
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2023-01-10T14:00:00Z",
  "updated_at": "2023-01-10T14:00:00Z"
}
```

#### Create Admin User (Admin Only)
**Endpoint:** `POST /api/admin/create`  
- Create a new admin user (accessible only by admins)

**Request:**
```json
{
  "username": "newadmin",
  "email": "admin@example.com",
  "password": "AdminPass123!",
  "name": "Admin User",
  "gender": "MALE",
  "date_of_birth": "1985-03-15"
}
```

**Response (200 OK):**
```json
{
  "message": "Admin user registration initiated. Please check the email to verify the account."
}
```

---

## Categories

Categories provide a classification system for organizing financial transactions. The module supports both system-defined default categories and user-created custom categories to enable meaningful organization and reporting.

### Features and Constraints
- **Predefined System Categories**: Default categories (Food, Transport, Utilities, etc.) available to all users.
- **Custom User Categories**: Users can create personalized categories to better organize their financial data.
- **Naming Rules**: Category names must be unique per user (case-insensitive) and cannot duplicate predefined category names.
- **Access Control**: Users can only access their own categories, while parents can view their child's categories and admins can see all categories.
- **Deletion Restrictions**: Categories with associated transactions, recurring transactions, or budgets cannot be deleted.
- **Soft Deletion**: Categories are soft-deleted to maintain data integrity in existing transactions.

### API Endpoints

#### List Categories
**Endpoint:** `GET /api/categories`  
- Retrieve paginated list of available categories

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)
- `child_id`: UUID of child user to view their categories (for parent users)
- `user_id`: Target user ID for admin requests

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "name": "groceries",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "is_predefined": false,
      "is_deleted": false,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    },
    {
      "id": "12345678-89ab-cdef-0123-456789abcdef",
      "name": "transportation",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "is_predefined": true,
      "is_deleted": false,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ],
  "total_items": 15,
  "current_page": 1,
  "total_pages": 2,
  "per_page": 10
}
```

#### Create Category
**Endpoint:** `POST /api/categories`  
- Create a new custom category

**Request:**
```json
{
  "name": "Office Supplies",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef"
}
```

**Response (201 Created):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "name": "office supplies",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "is_predefined": false,
  "is_deleted": false,
  "created_at": "2023-01-10T15:30:00Z",
  "updated_at": "2023-01-10T15:30:00Z"
}
```

#### Get Category
**Endpoint:** `GET /api/categories/{id}`  
- Retrieve a specific category's details

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "name": "office supplies",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "is_predefined": false,
  "is_deleted": false,
  "created_at": "2023-01-10T15:30:00Z",
  "updated_at": "2023-01-10T15:30:00Z"
}
```

#### Update Category
**Endpoint:** `PATCH /api/categories/{id}`  
- Update a category's name

**Request:**
```json
{
  "name": "Home Office Supplies"
}
```

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "name": "home office supplies",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "is_predefined": false,
  "is_deleted": false,
  "created_at": "2023-01-10T15:30:00Z",
  "updated_at": "2023-01-10T16:45:00Z"
}
```

#### Delete Category
**Endpoint:** `DELETE /api/categories/{id}`  
- Delete a category if it has no associated transactions

**Response (204 No Content)**

---

## Wallets

Users can manage their wallets, which store financial information such as balances, allowing users to organize their finances across multiple accounts or purposes.

### Features and Constraints
- **Wallet Management**: Users can create, retrieve, update, and delete their wallets. Admins can manage wallets for any user.
- **Balance Control**: Wallets maintain balance integrity through transaction validation. Balance is read-only and only modified through transactions. Initial balance of the wallet will always be zero.
- **Naming Rules**: Wallet names must be unique per user (case-insensitive).
- **Deletion Restrictions**: Wallets can only be deleted if they have zero balance and no associated transactions.
- **Access Control**: Users can access only their own wallets, parents can view their child's wallets, and admins can manage all wallets.
- **Inter-wallet Transfers**: Users can transfer funds between their own wallets through specialized transactions.

### API Endpoints

#### List Wallets
**Endpoint:** `GET /api/wallets`  
- Retrieve paginated list of available wallets

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)
- `child_id`: UUID of child user to view their wallets (for parent users)
- `user_id`: Target user ID for admin requests

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "name": "daily expenses",
      "balance": "125.50",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "is_deleted": false,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-10T15:30:00Z"
    },
    {
      "id": "12345678-89ab-cdef-0123-456789abcdef",
      "name": "savings",
      "balance": "1000.00",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "is_deleted": false,
      "created_at": "2023-01-05T10:30:00Z",
      "updated_at": "2023-01-10T15:30:00Z"
    }
  ],
  "total_items": 2,
  "current_page": 1,
  "total_pages": 1,
  "per_page": 10
}
```

#### Create Wallet
**Endpoint:** `POST /api/wallets`  
- Create a new wallet

**Request:**
```json
{
  "name": "Travel Fund",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef"
}
```

**Response (201 Created):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "name": "travel fund",
  "balance": "0.00",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "is_deleted": false,
  "created_at": "2023-01-15T09:30:00Z",
  "updated_at": "2023-01-15T09:30:00Z"
}
```

#### Get Wallet
**Endpoint:** `GET /api/wallets/{id}`  
- Retrieve a specific wallet's details

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "name": "travel fund",
  "balance": "0.00",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "is_deleted": false,
  "created_at": "2023-01-15T09:30:00Z",
  "updated_at": "2023-01-15T09:30:00Z"
}
```

#### Update Wallet
**Endpoint:** `PATCH /api/wallets/{id}`  
- Update a wallet's name

**Request:**
```json
{
  "name": "Vacation Fund"
}
```

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "name": "vacation fund",
  "balance": "0.00",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "is_deleted": false,
  "created_at": "2023-01-15T09:30:00Z",
  "updated_at": "2023-01-15T10:45:00Z"
}
```

#### Delete Wallet
**Endpoint:** `DELETE /api/wallets/{id}`  
- Delete a wallet (requires zero balance and no associated transactions)

**Response (204 No Content)**

---

## Transactions

Transactions represent financial activities (income and expenses) within the user's wallets. All transactions are soft-deleted to maintain financial records and support accurate reporting.

### Features and Constraints
- **Transaction Types**: Supports two transaction types - CREDIT (income) and DEBIT (expense).
- **Wallet Integration**: Each transaction is linked to a specific wallet and updates the wallet's balance automatically.
- **Category Classification**: Every transaction must be associated with a category for better organization and reporting.
- **Date Tracking**: Transactions include timestamps for chronological tracking and time-based reporting.
- **Access Control**: Users can only access their own transactions, while parents can view their child's transactions and admins can access any user's transactions.
- **Budget Impact**: Expense transactions automatically affect any matching budget's spent amount.
- **Validation Rules**: The amount must be between 0 and 99999999.99. The category used in the transaction must belong to the user or be global and not be deleted. The wallet used in the transaction must belong to the user and not be deleted.

### API Endpoints

#### List Transactions
**Endpoint:** `GET /api/transactions`  
- Retrieve paginated list of transactions with filtering options

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)
- `child_id`: UUID of child user to view their transactions (for parent users)
- `user_id`: Target user ID for admin requests
- `wallet_id`: Filter by specific wallet
- `category_id`: Filter by specific category
- `type`: Filter by transaction type (CREDIT or DEBIT)
- `from_date`: Filter transactions from this date (format: YYYY-MM-DD)
- `to_date`: Filter transactions to this date (format: YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "type": "CREDIT",
      "category": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "salary"
      },
      "wallet": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "main account"
      },
      "amount": "1500.00",
      "transaction_at": "2023-01-15T10:00:00Z",
      "description": "Monthly salary",
      "is_deleted": false,
      "created_at": "2023-01-15T10:00:00Z",
      "updated_at": "2023-01-15T10:00:00Z"
    },
    {
      "id": "12345678-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "type": "DEBIT",
      "category": {
        "id": "12345678-89ab-cdef-0123-456789abcdef",
        "name": "groceries"
      },
      "wallet": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "main account"
      },
      "amount": "50.25",
      "transaction_at": "2023-01-16T15:30:00Z",
      "description": "Weekly groceries",
      "is_deleted": false,
      "created_at": "2023-01-16T15:30:00Z",
      "updated_at": "2023-01-16T15:30:00Z"
    }
  ],
  "total_items": 15,
  "current_page": 1,
  "total_pages": 8,
  "per_page": 2
}
```

#### Create Transaction
**Endpoint:** `POST /api/transactions`  
- Create a new transaction

**Request:**
```json
{
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category_id": "12345678-89ab-cdef-0123-456789abcdef",
  "wallet_id": "01234567-89ab-cdef-0123-456789abcdef",
  "amount": "75.50",
  "transaction_at": "2023-01-20T12:00:00Z",
  "description": "Shopping at mall"
}
```

**Response (201 Created):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "shopping"
  },
  "wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "amount": "75.50",
  "transaction_at": "2023-01-20T12:00:00Z",
  "description": "Shopping at mall",
  "is_deleted": false,
  "created_at": "2023-01-20T18:30:45Z",
  "updated_at": "2023-01-20T18:30:45Z"
}
```

#### Get Transaction
**Endpoint:** `GET /api/transactions/{id}`  
- Retrieve details of a specific transaction

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "shopping"
  },
  "wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "amount": "75.50",
  "transaction_at": "2023-01-20T12:00:00Z",
  "description": "Shopping at mall",
  "is_deleted": false,
  "created_at": "2023-01-20T18:30:45Z",
  "updated_at": "2023-01-20T18:30:45Z"
}
```

#### Update Transaction
**Endpoint:** `PATCH /api/transactions/{id}`  
- Update a transaction

**Request:**
```json
{
  "amount": "85.75",
  "category_id": "34567890-89ab-cdef-0123-456789abcdef",
  "description": "Shopping at mall and restaurant",
  "type": "DEBIT",
  "transaction_at": "2023-01-20T12:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category": {
    "id": "34567890-89ab-cdef-0123-456789abcdef",
    "name": "dining"
  },
  "wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "amount": "85.75",
  "transaction_at": "2023-01-20T12:00:00Z",
  "description": "Shopping at mall and restaurant",
  "is_deleted": false,
  "created_at": "2023-01-20T18:30:45Z",
  "updated_at": "2023-01-20T19:15:30Z"
}
```

#### Delete Transaction
**Endpoint:** `DELETE /api/transactions/{id}`  
- Soft delete a transaction

**Response (204 No Content)**

---

## Budgets

Budgets provide a monthly financial planning tool for tracking and controlling expenses by category. The system supports budget creation, monitoring, and automated notifications when spending approaches or exceeds defined limits.

### Features and Constraints
- **Category-Based Budgeting**: Each budget is tied to a specific expense category for targeted monitoring.
- **Monthly Planning**: Budgets are created for specific month and year combinations, enabling time-based financial planning.
- **Spending Tracking**: The system automatically tracks spending against budgets when transactions are created, updated, or deleted.
- **Threshold Notifications**: Users receive email notifications when spending reaches warning (customizable percentage) or exceeding thresholds.
- **Access Control**: Users can manage their own budgets while parents can view their child's budgets.
- **Budget Analytics**: Provides percentage calculations, remaining amount tracking, and spending trends.
- **Validation Rules**: System prevents duplicate budgets for the same user-category-month-year combination and validates reasonable budget amounts.

### API Endpoints

#### List Budgets
**Endpoint:** `GET /api/budgets`  
- Retrieve paginated list of budgets with filtering options

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)
- `child_id`: UUID of child user to view their budgets (for parent users)
- `user_id`: Target user ID for admin requests
- `category_id`: Filter by specific category
- `month`: Filter by month (1-12)
- `year`: Filter by year

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "category": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "groceries"
      },
      "amount": "500.00",
      "spent_amount": "325.75",
      "month": 3,
      "year": 2025,
      "is_deleted": false,
      "created_at": "2025-02-28T12:00:00Z",
      "updated_at": "2025-03-15T15:30:00Z"
    },
    {
      "id": "12345678-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "category": {
        "id": "12345678-89ab-cdef-0123-456789abcdef",
        "name": "entertainment"
      },
      "amount": "200.00",
      "spent_amount": "150.25",
      "month": 3,
      "year": 2025,
      "is_deleted": false,
      "created_at": "2025-02-28T12:30:00Z",
      "updated_at": "2025-03-10T18:45:00Z"
    }
  ],
  "total_items": 5,
  "current_page": 1,
  "total_pages": 3,
  "per_page": 2
}
```

#### Create Budget
**Endpoint:** `POST /api/budgets`  
- Create a new budget for a specific category, month, and year

**Request:**
```json
{
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "category_id": "01234567-89ab-cdef-0123-456789abcdef",
  "amount": "500.00",
  "month": 4,
  "year": 2025
}
```

**Response (201 Created):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "category": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "groceries"
  },
  "amount": "500.00",
  "spent_amount": "0.00",
  "month": 4,
  "year": 2025,
  "is_deleted": false,
  "created_at": "2025-03-23T14:30:00Z",
  "updated_at": "2025-03-23T14:30:00Z"
}
```

#### Get Budget
**Endpoint:** `GET /api/budgets/{id}`  
- Retrieve details of a specific budget

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "category": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "groceries"
  },
  "amount": "500.00",
  "spent_amount": "125.50",
  "month": 4,
  "year": 2025,
  "is_deleted": false,
  "created_at": "2025-03-23T14:30:00Z",
  "updated_at": "2025-03-25T16:45:00Z"
}
```

#### Update Budget
**Endpoint:** `PATCH /api/budgets/{id}`  
- Update a budget's amount or category

**Request:**
```json
{
  "amount": "600.00",
  "category_id": "01234567-89ab-cdef-0123-456789abcdef"
}
```

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "category": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "groceries"
  },
  "amount": "600.00",
  "spent_amount": "125.50",
  "month": 4,
  "year": 2025,
  "is_deleted": false,
  "created_at": "2025-03-23T14:30:00Z",
  "updated_at": "2025-03-25T17:15:00Z"
}
```

#### Delete Budget
**Endpoint:** `DELETE /api/budgets/{id}`  
- Soft delete a budget

**Response (204 No Content)**

---

## Recurring Transactions

Recurring Transactions automate regular financial activities by scheduling transactions to occur at defined intervals. They allow users to set up recurring payments or income sources that are processed automatically on scheduled dates.

### Features and Constraints
- **Automated Processing**: System automatically creates regular transactions based on user-defined schedules.
- **Frequency Options**: Supports daily, weekly, monthly, and yearly recurring transactions.
- **Time Range Control**: Users can set both start and optional end dates for recurring transactions.
- **Wallet Integration**: All recurring transactions are linked to specific wallets and maintain balance integrity.
- **Category Classification**: Each recurring transaction must be associated with a category for better organization.
- **Email Notifications**: Users receive email notifications when recurring transactions are processed.
- **Validation Rules**: The system prevents creating recurring transactions with invalid dates, insufficient wallet balance, or invalid category/wallet combinations. The wallet used in the transaction must belong to the user and not be deleted. The category used in the transaction must belong to the user or be global and not be deleted.
- **Access Control**: Users can only access their own recurring transactions, while parents can view their child's transactions.

### API Endpoints

#### List Recurring Transactions
**Endpoint:** `GET /api/recurring-transactions`  
- Retrieve paginated list of recurring transactions with filtering options

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)
- `child_id`: UUID of child user to view their recurring transactions (for parent users)
- `user_id`: Target user ID for admin requests
- `wallet_id`: Filter by specific wallet
- `category_id`: Filter by specific category
- `type`: Filter by transaction type (CREDIT or DEBIT)
- `frequency`: Filter by frequency (DAILY, WEEKLY, MONTHLY, YEARLY)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "type": "CREDIT",
      "category": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "salary"
      },
      "wallet": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "main account"
      },
      "amount": "1500.00",
      "description": "Monthly salary",
      "frequency": "MONTHLY",
      "start_at": "2025-01-01T10:00:00Z",
      "end_at": "2025-12-31T10:00:00Z",
      "next_execution_at": "2025-04-01T10:00:00Z",
      "last_executed_at": "2025-03-01T10:00:00Z",
      "is_deleted": false,
      "created_at": "2024-12-15T14:30:00Z",
      "updated_at": "2025-03-01T10:00:00Z"
    },
    {
      "id": "12345678-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "type": "DEBIT",
      "category": {
        "id": "12345678-89ab-cdef-0123-456789abcdef",
        "name": "rent"
      },
      "wallet": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "main account"
      },
      "amount": "800.00",
      "description": "Monthly rent payment",
      "frequency": "MONTHLY",
      "start_at": "2025-01-05T09:00:00Z",
      "end_at": null,
      "next_execution_at": "2025-04-05T09:00:00Z",
      "last_executed_at": "2025-03-05T09:00:00Z",
      "is_deleted": false,
      "created_at": "2024-12-20T16:45:00Z",
      "updated_at": "2025-03-05T09:00:00Z"
    }
  ],
  "total_items": 5,
  "current_page": 1,
  "total_pages": 3,
  "per_page": 2
}
```

#### Create Recurring Transaction
**Endpoint:** `POST /api/recurring-transactions`  
- Create a new recurring transaction

**Request:**
```json
{
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category_id": "12345678-89ab-cdef-0123-456789abcdef",
  "wallet_id": "01234567-89ab-cdef-0123-456789abcdef",
  "amount": "50.00",
  "description": "Weekly grocery shopping",
  "frequency": "WEEKLY",
  "start_at": "2025-04-01T12:00:00Z",
  "end_at": "2025-12-31T12:00:00Z"
}
```

**Response (201 Created):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "groceries"
  },
  "wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "amount": "50.00",
  "description": "Weekly grocery shopping",
  "frequency": "WEEKLY",
  "start_at": "2025-04-01T12:00:00Z",
  "end_at": "2025-12-31T12:00:00Z",
  "next_execution_at": "2025-04-01T12:00:00Z",
  "last_executed_at": null,
  "is_deleted": false,
  "created_at": "2025-03-23T15:30:00Z",
  "updated_at": "2025-03-23T15:30:00Z"
}
```

#### Get Recurring Transaction
**Endpoint:** `GET /api/recurring-transactions/{id}`  
- Retrieve details of a specific recurring transaction

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "groceries"
  },
  "wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "amount": "50.00",
  "description": "Weekly grocery shopping",
  "frequency": "WEEKLY",
  "start_at": "2025-04-01T12:00:00Z",
  "end_at": "2025-12-31T12:00:00Z",
  "next_execution_at": "2025-04-01T12:00:00Z",
  "last_executed_at": null,
  "is_deleted": false,
  "created_at": "2025-03-23T15:30:00Z",
  "updated_at": "2025-03-23T15:30:00Z"
}
```

#### Update Recurring Transaction
**Endpoint:** `PATCH /api/recurring-transactions/{id}`  
- Update a recurring transaction

**Request:**
```json
{
  "amount": "75.00",
  "description": "Increased weekly grocery budget",
  "frequency": "WEEKLY",
  "category_id": "12345678-89ab-cdef-0123-456789abcdef"
}
```

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "type": "DEBIT",
  "category": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "groceries"
  },
  "wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "amount": "75.00",
  "description": "Increased weekly grocery budget",
  "frequency": "WEEKLY",
  "start_at": "2025-04-01T12:00:00Z",
  "end_at": "2025-12-31T12:00:00Z",
  "next_execution_at": "2025-04-01T12:00:00Z",
  "last_executed_at": null,
  "is_deleted": false,
  "created_at": "2025-03-23T15:30:00Z",
  "updated_at": "2025-03-23T16:15:00Z"
}
```

#### Delete Recurring Transaction
**Endpoint:** `DELETE /api/recurring-transactions/{id}`  
- Soft delete a recurring transaction

**Response (204 No Content)**

---

## Inter-wallet Transactions

Inter-wallet Transactions enable users to transfer funds between their own wallets, providing flexibility in financial management and organization. This module maintains the integrity of wallet balances while creating a clear record of fund movements.

### Features and Constraints
- **Wallet-to-Wallet Transfers**: Users can move funds between any of their personal wallets.
- **Balance Validation**: System prevents transfers when source wallet has insufficient funds.
- **Distinct Wallet Requirement**: Source and destination must be different wallets.
- **Ownership Validation**: Both wallets must belong to the same user.
- **Transaction History**: All transfers are tracked with timestamps and descriptions.
- **Hierarchical Access**: Parents can view their child user's transfers, and admins can access all transfers.
- **Deletion Rules**: Soft deletion automatically reverses the transfer effect on wallet balances.

### API Endpoints

#### List Inter-wallet Transactions
**Endpoint:** `GET /api/interwallet-transactions`  
- Retrieve paginated list of transfers between wallets

**Query Parameters:**
- `page`: Page number for pagination (default: 1)
- `per_page`: Number of items per page (default: 10)
- `child_id`: UUID of child user to view their transfers (for parent users)
- `user_id`: Target user ID for admin requests
- `from_date`: Filter transfers from this date (format: YYYY-MM-DD)
- `to_date`: Filter transfers to this date (format: YYYY-MM-DD)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "01234567-89ab-cdef-0123-456789abcdef",
      "user_id": "01234567-89ab-cdef-0123-456789abcdef",
      "source_wallet": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "main account"
      },
      "destination_wallet": {
        "id": "12345678-89ab-cdef-0123-456789abcdef",
        "name": "savings"
      },
      "amount": "500.00",
      "transaction_at": "2023-01-25T14:00:00Z",
      "description": "Transfer to savings",
      "is_deleted": false,
      "created_at": "2023-01-25T14:00:00Z",
      "updated_at": "2023-01-25T14:00:00Z"
    }
  ],
  "total_items": 5,
  "current_page": 1,
  "total_pages": 5,
  "per_page": 1
}
```

#### Create Inter-wallet Transfer
**Endpoint:** `POST /api/interwallet-transactions`  
- Create a transfer between wallets

**Request:**
```json
{
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "source_wallet_id": "01234567-89ab-cdef-0123-456789abcdef",
  "destination_wallet_id": "12345678-89ab-cdef-0123-456789abcdef",
  "amount": "250.00",
  "description": "Monthly savings transfer"
}
```

**Response (201 Created):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "source_wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "destination_wallet": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "savings"
  },
  "amount": "250.00",
  "transaction_at": "2023-01-30T16:45:22Z",
  "description": "Monthly savings transfer",
  "is_deleted": false,
  "created_at": "2023-01-30T16:45:22Z",
  "updated_at": "2023-01-30T16:45:22Z"
}
```

#### Get Inter-wallet Transfer
**Endpoint:** `GET /api/interwallet-transactions/{id}`  
- Retrieve details of a specific transfer

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "source_wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "destination_wallet": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "savings"
  },
  "amount": "250.00",
  "transaction_at": "2023-01-30T16:45:22Z",
  "description": "Monthly savings transfer",
  "is_deleted": false,
  "created_at": "2023-01-30T16:45:22Z",
  "updated_at": "2023-01-30T16:45:22Z"
}
```

#### Update Inter-wallet Transfer
**Endpoint:** `PATCH /api/interwallet-transactions/{id}`  
- Update a transfer between wallets

**Request:**
```json
{
  "amount": "300.00",
  "description": "Increased monthly savings transfer",
  "source_wallet_id": "01234567-89ab-cdef-0123-456789abcdef",
  "destination_wallet_id": "12345678-89ab-cdef-0123-456789abcdef",
  "transaction_at": "2023-01-30T16:45:22Z"
}
```

**Response (200 OK):**
```json
{
  "id": "23456789-89ab-cdef-0123-456789abcdef",
  "user_id": "01234567-89ab-cdef-0123-456789abcdef",
  "source_wallet": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "main account"
  },
  "destination_wallet": {
    "id": "12345678-89ab-cdef-0123-456789abcdef",
    "name": "savings"
  },
  "amount": "300.00",
  "transaction_at": "2023-01-30T16:45:22Z",
  "description": "Increased monthly savings transfer",
  "is_deleted": false,
  "created_at": "2023-01-30T16:45:22Z",
  "updated_at": "2023-01-30T17:20:15Z"
}
```

#### Delete Inter-wallet Transfer
**Endpoint:** `DELETE /api/interwallet-transactions/{id}`  
- Soft delete a transfer between wallets

**Response (204 No Content)**

---

## Reports and Analytics

The Reports and Analytics module provides comprehensive financial insights by aggregating transaction data into meaningful summaries, trends, and exportable formats. It helps users track their spending patterns and make informed financial decisions.

### Features and Constraints
- **Transaction Summary Reports**: Detailed overview of financial activities including totals by category and wallet.
- **Spending Trends Analysis**: Category-based spending breakdowns with percentage calculations and visualizations.
- **Data Export Options**: Export transaction history in both PDF and CSV formats for offline analysis.
- **Flexible Date Filtering**: All reports can be filtered by custom date ranges for precise time period analysis.
- **Hierarchical Access**: Parents can view their child's reports, while admins can access reports for any user.
- **Email Delivery**: Exported reports are automatically sent to the user's email address as attachments.
- **Asynchronous Processing**: Large report generation is handled by background tasks to optimize user experience.

### API Endpoints

#### Transaction Summary Report
**Endpoint:** `GET /api/transactions/summary-report`  
- Generate a comprehensive summary report of transactions with date range filtering

**Query Parameters:**
- `start_date`: Start date for filtering (format: YYYY-MM-DD)
- `end_date`: End date for filtering (format: YYYY-MM-DD)
- `user_id`: Target user ID for admin requests
- `child_id`: Child user ID for parent users

**Response (200 OK):**
```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-01-31",
  "total_credit": "2500.00",
  "total_debit": "1450.75",
  "category_summary": [
    {
      "category": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "groceries"
      },
      "total_credit": "0.00",
      "total_debit": "450.25",
      "transaction_count": 5
    },
    {
      "category": {
        "id": "12345678-89ab-cdef-0123-456789abcdef",
        "name": "salary"
      },
      "total_credit": "2500.00",
      "total_debit": "0.00",
      "transaction_count": 1
    }
  ],
  "wallet_summary": [
    {
      "wallet": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "main account"
      },
      "total_credit": "2500.00",
      "total_debit": "1450.75",
      "transaction_count": 12
    }
  ]
}
```

#### Spending Trends
**Endpoint:** `GET /api/transactions/spending-trends`  
- Generate category-based spending trends with percentage breakdowns

**Query Parameters:**
- `start_date`: Start date for filtering (format: YYYY-MM-DD)
- `end_date`: End date for filtering (format: YYYY-MM-DD)
- `user_id`: Target user ID for admin requests
- `child_id`: Child user ID for parent users

**Response (200 OK):**
```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-01-31",
  "total_credit": "2500.00",
  "total_debit": "1450.75",
  "spending_trends": [
    {
      "category": {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "name": "groceries"
      },
      "amount": "450.25",
      "percentage": "31.03",
      "transaction_count": 5
    },
    {
      "category": {
        "id": "23456789-89ab-cdef-0123-456789abcdef",
        "name": "dining"
      },
      "amount": "350.50",
      "percentage": "24.16",
      "transaction_count": 8
    },
    {
      "category": {
        "id": "34567890-89ab-cdef-0123-456789abcdef",
        "name": "transportation"
      },
      "amount": "300.00",
      "percentage": "20.68",
      "transaction_count": 15
    }
  ]
}
```

#### Export Transaction History
**Endpoint:** `GET /api/transactions/history/export`  
- Generate and email a detailed transaction history report in PDF or CSV format

**Query Parameters:**
- `start_date`: Start date for filtering (format: YYYY-MM-DD)
- `end_date`: End date for filtering (format: YYYY-MM-DD)
- `user_id`: Target user ID for admin requests
- `child_id`: Child user ID for parent users
- `format`: Export format, either "pdf" or "csv" (default: "pdf")

**Response (202 Accepted):**
```json
{
  "message": "Transaction history export request received. The PDF will be sent to john@example.com shortly."
}
```

#### Utility Scripts
- Terminal script which creates an admin user if none exists.
- Terminal script which creates missing global categories (e.g., Salary, Food) if not present.

### Background Tasks (Cron Jobs)
- Permanently removes soft-deleted categories, wallets, and users after a certain period via a scheduled task.

---