/* eslint-disable @typescript-eslint/no-explicit-any */

// Load Pyodide directly from CDN to avoid Webpack bundling issues (IN_NODE error)
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/";
declare function importScripts(...urls: string[]): void;
importScripts(`${PYODIDE_CDN}pyodide.js`);

declare function loadPyodide(options?: any): Promise<any>;

let pyodide: any = null;

async function initPyodide() {
    if (pyodide) return pyodide;

    pyodide = await loadPyodide({
        indexURL: PYODIDE_CDN,
    });

    // Load cryptography (pre-built package)
    await pyodide.loadPackage(["cryptography"]);

    // Load local library via Fetch and Unpack
    const response = await fetch("/library.zip");
    const buffer = await response.arrayBuffer();
    pyodide.unpackArchive(buffer, "zip");

    // Add to sys.path so we can import 'secure_document_vault'
    // The zip contains 'src/secure_document_vault', so we add 'src' to path
    pyodide.runPython(`
    import sys
    import os
    import json
    import base64
    sys.path.append(os.getcwd())
    sys.path.append("/")
    sys.path.append(os.path.abspath("src"))

    from secure_document_vault.core.facade import encriptar, desencriptar
    from secure_document_vault.modules.key_store.generator import KeyProtector
    from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
    from cryptography.hazmat.primitives import serialization

    def js_proteger_llaves(password, priv_x_raw_b64, priv_ed_raw_b64, user_id):
        """Encrypt both private keys with password using KeyProtector.

        Takes raw base64-encoded private key bytes and returns two keystore
        dicts (encryption + signing) that can be safely stored in the
        identity JSON file.
        """
        # Reconstruct key objects from raw bytes
        priv_x = x25519.X25519PrivateKey.from_private_bytes(
            base64.b64decode(priv_x_raw_b64)
        )
        priv_ed = ed25519.Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(priv_ed_raw_b64)
        )

        try:
            enc_keystore = KeyProtector.protect_key(password, priv_x, user_id)
            sign_keystore = KeyProtector.protect_key(password, priv_ed, user_id)
        finally:
            del priv_x
            del priv_ed

        return json.dumps({
            "encryption_keystore": enc_keystore,
            "signing_keystore": sign_keystore
        })

    def js_firmar_con_keystore(challenge_str, sign_keystore_json, password):
        """Unlock signing key from keystore, sign challenge, zeroize key.

        Used during login to prove identity without ever exposing
        the raw private key outside this function scope.
        """
        sign_keystore = json.loads(sign_keystore_json)
        priv_key = KeyProtector.verify_password(password, sign_keystore)
        try:
            signature = priv_key.sign(challenge_str.encode())
            return base64.b64encode(signature).decode()
        finally:
            del priv_key

    def js_encriptar(file_bytes, name, recipients_json, signer_id, sign_keystore_json, password):
        """Encrypt a file using the keystore-protected signing key.

        The signing key is unlocked with the password via KeyProtector,
        used for signing, and immediately zeroized in a finally block.
        """
        sign_keystore = json.loads(sign_keystore_json)
        signer_key = KeyProtector.verify_password(password, sign_keystore)

        try:
            # Convert JS proxy to Python list of dicts
            recipients_list = recipients_json.to_py()

            recipients = []
            for r in recipients_list:
                pub_pem = r['publicKeyPem']
                recipients.append({
                    "id": r['id'],
                    "public_key": serialization.load_pem_public_key(pub_pem.encode())
                })

            # Get signer identity from the unlocked key
            signer_pub = signer_key.public_key()
            from secure_document_vault.modules.signing.signer import DocumentSigner
            fingerprint = DocumentSigner.get_fingerprint(signer_pub)

            # Use the core facade modules directly (bypass facade.encriptar
            # since it expects a keystore dict, and we already unlocked the key)
            from secure_document_vault.modules.randomness import RandomnessManager
            from secure_document_vault.modules.vault_builder import VaultBuilder
            from secure_document_vault.modules.key_wrapping import ECCKeyWrapper
            from secure_document_vault.modules.aead import AEAD_Engine

            randomness = RandomnessManager()
            builder = VaultBuilder()

            file_key = randomness.generate_key()
            recipients_metadata = []
            for recipient in recipients:
                wrapped_data = ECCKeyWrapper.wrap_key(file_key, recipient["public_key"])
                recipients_metadata.append(
                    {"id": recipient["id"], "encrypted_key": wrapped_data}
                )

            aad_bytes = builder.recolectar_metadatos(
                name,
                recipients=recipients_metadata,
                signer_id=signer_id,
                signer_fingerprint=fingerprint,
            )

            engine = AEAD_Engine(file_key)
            nonce = randomness.generate_nonce()
            ciphertext = engine.encrypt(nonce, file_bytes.to_bytes(), aad_bytes)

            data_to_sign = aad_bytes + ciphertext
            sign = DocumentSigner.sign(signer_key, data_to_sign)

            result = builder.empaquetar(
                nonce=nonce,
                aad_metadatos=aad_bytes,
                ciphertext_con_tag=ciphertext,
                signature=sign,
            )
            return result
        finally:
            del signer_key

    def js_desencriptar(vault_bytes, user_id, enc_keystore_json, password, signer_pub_pem):
        """Decrypt a vault file using the keystore-protected encryption key.

        The encryption key is unlocked with the password via KeyProtector,
        used for decryption, and immediately zeroized in a finally block.
        """
        enc_keystore = json.loads(enc_keystore_json)
        user_key = KeyProtector.verify_password(password, enc_keystore)

        try:
            signer_pub = serialization.load_pem_public_key(signer_pub_pem.encode())

            # Use the core facade modules directly (bypass facade.desencriptar
            # since it expects a keystore dict, and we already unlocked the key)
            from secure_document_vault.modules.vault_builder import VaultBuilder
            from secure_document_vault.modules.signing.signer import DocumentSigner
            from secure_document_vault.modules.key_wrapping import ECCKeyWrapper
            from secure_document_vault.modules.aead import AEAD_Engine
            from secure_document_vault.core.exceptions import IntegrityErrorException
            import hmac
            import json as json_mod

            builder = VaultBuilder()
            result = builder.desempaquetar(vault_bytes.to_bytes())

            if len(result) != 4:
                raise IntegrityErrorException("El archivo no contiene una firma digital.")

            nonce, aad, ciphertext, signature = result

            # 1. Verify signature first (on raw bytes)
            data_signed = aad + ciphertext
            try:
                DocumentSigner.verify(signer_pub, data_signed, signature)
            except Exception:
                raise IntegrityErrorException("ALERTA: Firma digital inválida.")

            # 2. Parse and verify fingerprint
            try:
                metadatos = json_mod.loads(aad.decode("utf-8"))
            except (json_mod.JSONDecodeError, UnicodeDecodeError):
                raise IntegrityErrorException("Metadatos AAD inválidos o corruptos.")

            signer_info = metadatos.get("signer")
            if signer_info:
                expected_fp = signer_info.get("fingerprint", "")
                actual_fp = DocumentSigner.get_fingerprint(signer_pub)
                if not hmac.compare_digest(expected_fp, actual_fp):
                    raise IntegrityErrorException(
                        "ALERTA: El fingerprint del firmante no coincide."
                    )

            # 3. Find user's encrypted file key
            recipients = metadatos.get("recipients", [])
            user_entry = next((r for r in recipients if r["id"] == user_id), None)
            if not user_entry:
                raise IntegrityErrorException(
                    f"Usuario {user_id} no autorizado para este archivo."
                )

            try:
                file_key = ECCKeyWrapper.unwrap_key(user_entry["encrypted_key"], user_key)
            except Exception as e:
                raise IntegrityErrorException(f"Error al descifrar llave contenedora: {e}")

            # 4. Decrypt
            engine = AEAD_Engine(file_key)
            return engine.decrypt(nonce, ciphertext, aad)
        finally:
            del user_key

    def js_generar_identidad():
        # Generate encryption keypair (X25519)
        priv_x = x25519.X25519PrivateKey.generate()
        pub_x = priv_x.public_key()

        # Generate signing keypair (Ed25519)
        priv_ed = ed25519.Ed25519PrivateKey.generate()
        pub_ed = priv_ed.public_key()

        # Raw bytes (base64) for internal cryptographic operations
        priv_x_raw = base64.b64encode(priv_x.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )).decode()
        pub_x_raw = base64.b64encode(pub_x.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )).decode()
        priv_ed_raw = base64.b64encode(priv_ed.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )).decode()
        pub_ed_raw = base64.b64encode(pub_ed.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )).decode()

        # PEM format for backend registration
        pub_x_pem = pub_x.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        pub_ed_pem = pub_ed.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        return {
            "encryption": {
                "private": priv_x_raw,
                "public": pub_x_raw,
                "publicPem": pub_x_pem
            },
            "signing": {
                "private": priv_ed_raw,
                "public": pub_ed_raw,
                "publicPem": pub_ed_pem
            }
        }
  `);

    return pyodide;
}

self.onmessage = async (e: MessageEvent) => {
    const { type, payload, id } = e.data;

    try {
        const py = await initPyodide();

        if (type === "INIT") {
            self.postMessage({ id, type: "READY" });
        } else if (type === "PROTECT_KEYS") {
            const { password, privXB64, privEdB64, userId } = payload;
            const result = py.runPython("js_proteger_llaves")(password, privXB64, privEdB64, userId);
            self.postMessage({ id, type: "RESULT", payload: result });
        } else if (type === "SIGN_CHALLENGE_KEYSTORE") {
            const { challenge, signKeystoreJson, password } = payload;
            const result = py.runPython("js_firmar_con_keystore")(challenge, signKeystoreJson, password);
            self.postMessage({ id, type: "RESULT", payload: result });
        } else if (type === "ENCRYPT") {
            const { file, fileName, recipients, signerId, signerKeystoreJson, password } = payload;
            const result = py.runPython("js_encriptar")(file, fileName, recipients, signerId, signerKeystoreJson, password);
            const output = result.toJs();
            (self as any).postMessage({ id, type: "RESULT", payload: output }, [output.buffer]);
        } else if (type === "DECRYPT") {
            const { vaultFile, userId, userKeystoreJson, password, signerPublicKeyPem } = payload;
            const result = py.runPython("js_desencriptar")(vaultFile, userId, userKeystoreJson, password, signerPublicKeyPem);
            const output = result.toJs();
            (self as any).postMessage({ id, type: "RESULT", payload: output }, [output.buffer]);
        } else if (type === "GENERATE_IDENTITY") {
            const result = py.runPython("js_generar_identidad")();
            self.postMessage({ id, type: "RESULT", payload: result.toJs() });
        }
    } catch (error: any) {
        self.postMessage({ id, type: "ERROR", error: error.message });
    }
};
