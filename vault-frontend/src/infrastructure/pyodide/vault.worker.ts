/* eslint-disable @typescript-eslint/no-explicit-any */

// Load Pyodide directly from CDN to avoid Webpack bundling issues (IN_NODE error)
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/";
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
    sys.path.append(os.path.abspath("src"))
    
    from secure_document_vault.core.facade import encriptar, desencriptar
    from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
    from cryptography.hazmat.primitives import serialization
    import base64

    def js_firmar_challenge(challenge_str, signer_key_b64):
        signer_key = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(signer_key_b64))
        signature = signer_key.sign(challenge_str.encode())
        return base64.b64encode(signature).decode()

    def js_encriptar(file_bytes, name, recipients_json, signer_id, signer_key_b64):
        signer_key = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(signer_key_b64))
        
        # Convert JS proxy to Python list of dicts
        recipients_list = recipients_json.to_py()
        
        recipients = []
        for r in recipients_list:
            # Check if key is available, if not handle accordingly. Assume it's a PEM string.
            pub_pem = r['publicKeyPem']
            recipients.append({
                "id": r['id'],
                "public_key": serialization.load_pem_public_key(pub_pem.encode())
            })
            
        result = encriptar(file_bytes.to_bytes(), name, recipients, signer_id, signer_key)
        return result

    def js_desencriptar(vault_bytes, user_id, user_key_b64, signer_pub_pem):
        user_key = x25519.X25519PrivateKey.from_private_bytes(base64.b64decode(user_key_b64))
        signer_pub = serialization.load_pem_public_key(signer_pub_pem.encode())
        
        result = desencriptar(vault_bytes.to_bytes(), user_id, user_key, signer_pub)
        return result

    def js_sign_challenge(challenge_str, private_key_pem):
        priv_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        signature = priv_key.sign(challenge_str.encode())
        return base64.b64encode(signature).decode()

    def js_generar_identidad():
        # Generar par de cifrado (X25519)
        priv_x = x25519.X25519PrivateKey.generate()
        pub_x = priv_x.public_key()

        # Generar par de firma (Ed25519)
        priv_ed = ed25519.Ed25519PrivateKey.generate()
        pub_ed = priv_ed.public_key()

        # Raw bytes (base64) para operaciones criptograficas internas
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

        # PEM format para registro en el backend
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
        } else if (type === "ENCRYPT") {
            const { file, fileName, recipients, signerId, signerPrivateKeyPem } = payload;
            const result = py.runPython("js_encriptar")(file, fileName, recipients, signerId, signerPrivateKeyPem);
            const output = result.toJs();
            self.postMessage({ id, type: "RESULT", payload: output }, [output.buffer]);
        } else if (type === "DECRYPT") {
            const { vaultFile, userId, userPrivateKeyPem, signerPublicKeyPem } = payload;
            const result = py.runPython("js_desencriptar")(vaultFile, userId, userPrivateKeyPem, signerPublicKeyPem);
            const output = result.toJs();
            self.postMessage({ id, type: "RESULT", payload: output }, [output.buffer]);
        } else if (type === "GENERATE_IDENTITY") {
            const result = py.runPython("js_generar_identidad")();
            self.postMessage({ id, type: "RESULT", payload: result.toJs() });
        } else if (type === "SIGN_CHALLENGE") {
            const { challenge, signerPrivateKeyBase64 } = payload;
            const result = py.runPython("js_firmar_challenge")(challenge, signerPrivateKeyBase64);

            self.postMessage({ id, type: "RESULT", payload: result });
        }
    } catch (error: any) {
        self.postMessage({ id, type: "ERROR", error: error.message });
    }
};
