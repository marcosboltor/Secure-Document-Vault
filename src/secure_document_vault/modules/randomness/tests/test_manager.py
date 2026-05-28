from secure_document_vault.modules.randomness.manager import RandomnessManager


def test_generate_key_length():
    key = RandomnessManager.generate_key()
    assert len(key) == 32


def test_generate_custom_key_length():
    key = RandomnessManager.generate_key(16)
    assert len(key) == 16


def test_generate_nonce_length():
    nonce = RandomnessManager.generate_nonce()
    assert len(nonce) == 12


def test_generate_custom_nonce_length():
    nonce = RandomnessManager.generate_nonce(16)
    assert len(nonce) == 16


def test_randomness():
    val1 = RandomnessManager.generate_key()
    val2 = RandomnessManager.generate_key()
    assert val1 != val2
