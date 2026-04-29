# Issue 3: Users Module Implementation (Identity and Authentication)

**Status**: Pending
**Priority**: Critical

---

## Description

Implement the core identity and authentication system for the Secure Document Vault. This module handles user registration, login (identity verification), and public key management.

## Files to Create/Modify

1. app/modules/users/domain/entities/user.py
2. app/modules/users/domain/repositories/user_repository.py
3. app/modules/users/application/use_cases/ (Create register_user_usecase.py, login_usecase.py, list_users_usecase.py)
4. app/modules/users/infrastructure/models/user_models.py
5. app/modules/users/infrastructure/repositories/user_repository_impl.py
6. app/modules/users/presentation/api/users_router.py
7. app/modules/users/presentation/schemas/user_schemas.py
8. app/modules/users/presentation/di/dependencies.py
9. app/modules/users/exceptions/users_exceptions.py

---

## Feature Requirements

### 1. Register User

* Domain: Define User entity with id, email, username, public_encryption_key, and public_signing_key.
* Use Case: Handle new user creation. Validate that the email is unique. Store public keys provided by the client.
* Logic: The server must NOT receive or store any private keys.

### 2. Login (Identity Verification)

* Concept: Since this is Zero-Knowledge, "Login" consists of the client signing a challenge (e.g., a timestamp or nonce) with their private key. The server verifies this signature against the stored public_signing_key.
* Use Case: Verify the client's signature. If valid, return an authentication token (JWT or Session).

### 3. Logout

* Use Case: Invalidate the user session or token.

### 4. List Users (with Public Keys)

* Use Case: Retrieve a list of all registered users including their public encryption keys.
* Purpose: This is required so users can select recipients when uploading/sharing a file.

---

## Error Handling (Mandatory)

* Raise UserAlreadyExistsError (409 Conflict) if the email is taken during registration.
* Raise InvalidCredentialsError (401 Unauthorized) if the login signature verification fails.
* Raise UserNotFoundError (404) when searching for a specific non-existent user.

---

## Technical Rationale

* Zero-Knowledge: By only storing public keys, the server can facilitate sharing between users (via encryption keys) and verify identity (via signing keys) without ever knowing the users' secrets.
* Scalability: Using a modular approach ensures that the identity logic is decoupled from the file management logic.

---

## Acceptance Criteria

1. Registration successfully stores public keys and unique emails.
2. Login correctly verifies Ed25519 signatures (Identity-based login).
3. The public key list is accessible for file sharing orchestration.
4. Code passes uv run black . and uv run flake8 vault-backend.
