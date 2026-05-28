# Secure Document Vault

A secure digital document vault built as part of a Cryptography course. It allows users to encrypt, sign, and share documents over untrusted channels using modern cryptographic primitives.

## What it does

The vault protects documents with a layered cryptographic approach:

- **Confidentiality** — each file is encrypted with a unique symmetric key (ChaCha20-Poly1305 AEAD)
- **Hybrid encryption** — the symmetric key is wrapped per-recipient using X25519 key agreement + HKDF, so multiple users can decrypt the same vault without sharing secrets
- **Integrity & authenticity** — every vault is signed with Ed25519; the signature is verified before any decryption attempt
- **Secure key storage** — private keys are protected with PBKDF2-HMAC-SHA256 (600,000 iterations) and stored as encrypted keystores
- **Key lifecycle** — keystores support rotation, revocation, and expiration

## Repository structure

```
/docs           Full security and architecture documentation
/src            Vault library source code
/tests          Integration and security tests
/examples       Runnable usage examples
/keys           Default location for keystore files (not committed)
/scripts        Build utilities
```

For full architecture details, cryptographic design decisions, threat model, and canonicalization strategy see the [docs/](docs/) folder.

## Installation

Requires Python 3.11+.

```bash
# With uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Usage

### Encrypt a document

```python
from secure_document_vault.core.facade import encriptar

vault_bytes = encriptar(
    archivo_en_bytes=open("report.pdf", "rb").read(),
    nombre_archivo="report.pdf",
    recipients_info=[
        {"id": "alice", "public_key": alice_enc_public_key},
        {"id": "bob",   "public_key": bob_enc_public_key},
    ],
    signer_id="alice",
    signer_keystore=alice_sign_keystore,
    signer_password="alice-password",
)
```

### Decrypt a document

```python
from secure_document_vault.core.facade import desencriptar

plaintext = desencriptar(
    archivo_vault=vault_bytes,
    user_id="bob",
    user_keystore=bob_enc_keystore,
    user_password="bob-password",
    signer_public_key=alice_sign_public_key,
)
```

See [examples/](examples/) for complete runnable scripts covering key generation, multi-user flows, and key lifecycle management.

## Running the tests

```bash
# With uv
uv run pytest

# Or directly
pytest tests/
```

## Security assumptions & known limitations

- The system assumes the local execution environment is trusted (no protection against keyloggers, malware, or OS-level compromise)
- Password strength is the user's responsibility — weak passwords reduce PBKDF2 effectiveness
- There is no centralized key recovery mechanism; losing a keystore password means losing access
- No protection against coercion or social engineering

For the full threat model see [docs/Secure Vault Documentation.md](docs/Secure%20Vault%20Documentation.md).

## Team

| Role | Member |
|------|--------|
| Development | Marcos Gabriel Flores Chávez |
| Software Architecture | Daniel Adrián Galindo Reyes |
| QA / Testing | Andrés Sebastián Hernández González |
| Technical Documentation | Ricardo Ángel Pineda Galindo |
