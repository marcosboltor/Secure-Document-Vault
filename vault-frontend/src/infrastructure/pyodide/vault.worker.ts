/* eslint-disable @typescript-eslint/no-explicit-any */
import { loadPyodide, type PyodideInterface } from "pyodide";

let pyodide: PyodideInterface | null = null;

async function initPyodide() {
  if (pyodide) return pyodide;

  pyodide = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/",
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

    def js_encriptar(file_bytes, name, recipients_json, signer_id, signer_key_pem):
        signer_key = serialization.load_pem_private_key(signer_key_pem.encode(), password=None)
        
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

    def js_desencriptar(vault_bytes, user_id, user_key_pem, signer_pub_pem):
        user_key = serialization.load_pem_private_key(user_key_pem.encode(), password=None)
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
        
        return {
            "encryption": {
                "private": priv_x.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).decode(),
                "public": pub_x.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
            },
            "signing": {
                "private": priv_ed.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).decode(),
                "public": pub_ed.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
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
      const { challenge, privateKeyPem } = payload;
      const result = py.runPython("js_sign_challenge")(challenge, privateKeyPem);
      self.postMessage({ id, type: "RESULT", payload: result });
    }
  } catch (error: any) {
    self.postMessage({ id, type: "ERROR", error: error.message });
  }
};
