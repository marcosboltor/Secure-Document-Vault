import pytest
from secure_document_vault.modules.key_generation.generator import KeyManager

def test_generate_and_retrieve_success():
    """Verifies that the manager can generate and return keys in the correct format."""
    manager = KeyManager()
    manager.generate_keys_for_user("alice")

    pub_key = manager.get_public_key("alice")
    priv_key = manager.get_private_key("alice")

    # Verify that the keys are generated in PEM format (bytes)
    assert pub_key.startswith(b"-----BEGIN PUBLIC KEY-----")
    assert priv_key.startswith(b"-----BEGIN PRIVATE KEY-----")

def test_different_users_have_different_keys():
    """Verifies that different users have different keys."""
    manager = KeyManager()
    manager.generate_keys_for_user("alice")
    manager.generate_keys_for_user("bob")

    alice_pub = manager.get_public_key("alice")
    bob_pub = manager.get_public_key("bob")

    # Verify that Alice and Bob have cryptographically distinct keys
    assert alice_pub != bob_pub

def test_missing_user_raises_error():
    """Verifies that the system handles requests for non-existent users correctly."""
    manager = KeyManager()
    
    with pytest.raises(ValueError, match="not found"):
        manager.get_public_key("annonymous_user")
        
    with pytest.raises(ValueError, match="not found"):
        manager.get_private_key("annonymous_user")