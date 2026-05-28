# examples/

Standalone scripts that demonstrate the main workflows of the Secure Document Vault.
Each script is self-contained and can be run independently.

## Prerequisites

Install the project before running any example:

```bash
pip install -e .
# or with uv:
uv sync
```

## Scripts

| Script | What it shows |
|--------|--------------|
| [01_generate_keys.py](01_generate_keys.py) | Generate X25519 + Ed25519 key pairs and save them as an encrypted keystore bundle |
| [02_encrypt_document.py](02_encrypt_document.py) | Encrypt a document for multiple recipients and save the `.vault` file |
| [03_decrypt_document.py](03_decrypt_document.py) | Decrypt a vault, verify the signature, and demonstrate access control |
| [04_full_flow_multiuser.py](04_full_flow_multiuser.py) | Full end-to-end flow with a 4-person team, signature verification, and tamper detection |
| [05_key_lifecycle.py](05_key_lifecycle.py) | Key expiration, rotation, revocation, and integrity validation |

## Running an example

```bash
# From the project root
python examples/01_generate_keys.py
python examples/02_encrypt_document.py
python examples/03_decrypt_document.py
python examples/04_full_flow_multiuser.py
python examples/05_key_lifecycle.py
```

## Security properties demonstrated

- **AEAD** — ChaCha20-Poly1305 authenticated encryption (examples 2–4)
- **Hybrid encryption** — X25519 key agreement + per-file symmetric key (examples 2–4)
- **Digital signatures** — Ed25519 sign-before-encrypt, verify-before-decrypt (examples 3–4)
- **Secure key storage** — PBKDF2-HMAC-SHA256 (600,000 iterations) + ChaCha20-Poly1305 (examples 1, 5)
- **Fail-closed behavior** — unauthorized access and tampered vaults are always rejected (examples 3–4)
- **Key lifecycle** — rotation, revocation, expiration, integrity checksums (example 5)
