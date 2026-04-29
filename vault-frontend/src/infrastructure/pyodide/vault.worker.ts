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

    def js_encriptar(file_bytes, name, recipients_json, signer_id, signer_key_b64):
        signer_key = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(signer_key_b64))
        
        # Convert JS proxy to Python list of dicts
        recipients_list = recipients_json.to_py()
        
        recipients = []
        for r in recipients_list:
            pub_bytes = base64.b64decode(r['publicKeyBase64'])
            recipients.append({
                "id": r['id'],
                "public_key": x25519.X25519PublicKey.from_public_bytes(pub_bytes)
            })
            
        result = encriptar(file_bytes.to_bytes(), name, recipients, signer_id, signer_key)
        return result

    def js_desencriptar(vault_bytes, user_id, user_key_b64, signer_pub_b64):
        user_key = x25519.X25519PrivateKey.from_private_bytes(base64.b64decode(user_key_b64))
        signer_pub = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(signer_pub_b64))
        
        result = desencriptar(vault_bytes.to_bytes(), user_id, user_key, signer_pub)
        return result

    def js_generar_identidad():
        # Generar par de cifrado (X25519)
        priv_x = x25519.X25519PrivateKey.generate()
        pub_x = priv_x.public_key()
        
        # Generar par de firma (Ed25519)
        priv_ed = ed25519.Ed25519PrivateKey.generate()
        pub_ed = priv_ed.public_key()
        
        return {
            "encryption": {
                "private": base64.b64encode(priv_x.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )).decode(),
                "public": base64.b64encode(pub_x.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )).decode()
            },
            "signing": {
                "private": base64.b64encode(priv_ed.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )).decode(),
                "public": base64.b64encode(pub_ed.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )).decode()
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
      const { file, fileName, recipients, signerId, signerPrivateKeyBase64 } = payload;
      const result = py.runPython("js_encriptar")(file, fileName, recipients, signerId, signerPrivateKeyBase64);
      const output = result.toJs();
      self.postMessage({ id, type: "RESULT", payload: output }, [output.buffer]);
    } else if (type === "DECRYPT") {
      const { vaultFile, userId, userPrivateKeyBase64, signerPublicKeyBase64 } = payload;
      const result = py.runPython("js_desencriptar")(vaultFile, userId, userPrivateKeyBase64, signerPublicKeyBase64);
      const output = result.toJs();
      self.postMessage({ id, type: "RESULT", payload: output }, [output.buffer]);
    } else if (type === "GENERATE_IDENTITY") {
      const result = py.runPython("js_generar_identidad")();
      self.postMessage({ id, type: "RESULT", payload: result.toJs() });
    }
  } catch (error: any) {
    self.postMessage({ id, type: "ERROR", error: error.message });
  }
};
