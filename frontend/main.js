let engine = null;

// DB Simulada en memoria
let listaUsuarios = [];

let fileToEncrypt = null;
let fileToDecrypt = null;

// Inicialización
async function iniciarMotor() {
    try {
        console.log("Cargando Pyodide...");
        engine = await loadPyodide();
        
        console.log("Cargando Cryptography...");
        await engine.loadPackage("cryptography");
        
        console.log("Descargando SDK Local...");
        let response = await fetch("secure_document_vault.zip");
        if (!response.ok) throw new Error("No se pudo cargar el SDK.");
        
        let buffer = await response.arrayBuffer();
        engine.unpackArchive(buffer, "zip");
        
        // Actualizar UI
        const status = document.getElementById("pyodide-status");
        status.innerHTML = `<i data-lucide="check-circle" style="color:var(--success); width:16px;"></i> Motor E2EE Listo`;
        status.style.color = "var(--success)";
        status.style.borderColor = "var(--success)";
        lucide.createIcons();
        
        document.getElementById("btn-add-user").disabled = false;
    } catch (err) {
        alert("Error de Inicialización: " + err.message);
        console.error(err);
    }
}

// 1. Generar Perfil de Usuario 
document.getElementById("btn-add-user").addEventListener("click", async () => {
    let inputName = document.getElementById("new-username");
    let name = inputName.value.trim();
    if (!name) return alert("Escribe un nombre de usuario");

    let userId = name.toLowerCase().replace(/[^a-z0-9]/g, "_") + "_" + Math.floor(Math.random()*1000);

    try {
        document.getElementById("btn-add-user").innerHTML = `<div class="spinner"></div>`;
        
        await engine.runPythonAsync(`
            from secure_document_vault.modules.key_generation.generator import KeyManager
            
            # Instanciamos uno nuevo 
            km = KeyManager()
            km.generate_keys_for_user("${userId}")
            
            pub_bytes = km.get_public_key("${userId}")
            priv_bytes = km.get_private_key("${userId}")
            sign_pub_bytes = km.get_signing_public_key("${userId}")
            sign_priv_bytes = km.get_signing_private_key("${userId}")
            
            pub_str = pub_bytes.decode('utf-8')
            priv_str = priv_bytes.decode('utf-8')
            sign_pub_str = sign_pub_bytes.decode('utf-8')
            sign_priv_str = sign_priv_bytes.decode('utf-8')
        `);
        
        let pubStr = engine.globals.get('pub_str');
        let privStr = engine.globals.get('priv_str');
        let signPubStr = engine.globals.get('sign_pub_str');
        let signPrivStr = engine.globals.get('sign_priv_str');
        
        // Agregar a la "DB" JS
        let newUser = {
            id: userId,
            name: name,
            public_key: pubStr,
            private_key: privStr,
            signing_public_key: signPubStr,
            signing_private_key: signPrivStr
        };
        listaUsuarios.push(newUser);
        
        refrescarUIUsuarios();
        
        inputName.value = "";
        document.getElementById("btn-add-user").innerHTML = `<i data-lucide="user-plus"></i> Registrar Perfil`;
        lucide.createIcons();
        
        mostrarToast("Usuario registrado: " + name);
        
        // Habilitar encriptacion
        document.getElementById("encryption-section").style.opacity = "1";
        document.getElementById("encryption-section").style.pointerEvents = "auto";
        document.getElementById("decryption-section").style.opacity = "1";
        document.getElementById("decryption-section").style.pointerEvents = "auto";
        
    } catch (err) {
        alert(err.message);
    }
});

function refrescarUIUsuarios() {
    let dirCont = document.getElementById("users-list-container");
    let recpCont = document.getElementById("recipients-list");
    let logiCont = document.getElementById("login-selector");
    
    dirCont.innerHTML = "";
    recpCont.innerHTML = "";
    
    // Reset login options
    logiCont.innerHTML = '<option value="">-- Elige qué cuenta "Hackerás" / "Usarás" --</option>';
    
    if(listaUsuarios.length > 0) {
        document.getElementById("users-directory-display").classList.remove("hidden");
    }

    listaUsuarios.forEach((usr, index) => {
        // Directorio List
        dirCont.innerHTML += `
            <div class="user-item">
                <i data-lucide="user"></i>
                <div style="flex:1;">
                    <strong>${usr.name}</strong> <span style="font-size:0.7rem; color:var(--text-muted);">(${usr.id})</span>
                    <div style="font-size:0.6rem; margin-top:2px; font-family:monospace; color:var(--primary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:250px;">
                        PUB: ${usr.public_key.replace("-----BEGIN PUBLIC KEY-----\\n", "")}
                    </div>
                </div>
            </div>
        `;
        
        // Checkboxes Cifrado
        recpCont.innerHTML += `
            <label class="checkbox-item">
                <input type="checkbox" class="recipient-checkbox" value="${usr.id}">
                ${usr.name}
            </label>
        `;
        
        // Combobox Descifrado
        logiCont.innerHTML += `<option value="${usr.id}">Entrar como: ${usr.name}</option>`;
    });
    
    lucide.createIcons();
}


// Interacciones de Archivos (Inputs visuales)
document.getElementById("file-input").addEventListener("change", (e) => {
    fileToEncrypt = e.target.files[0];
    if (fileToEncrypt) {
        document.getElementById("file-name").textContent = fileToEncrypt.name;
        document.getElementById("btn-encrypt").disabled = false;
    }
});

document.getElementById("vault-input").addEventListener("change", (e) => {
    fileToDecrypt = e.target.files[0];
    if (fileToDecrypt) {
        document.getElementById("vault-name").textContent = fileToDecrypt.name;
        document.getElementById("btn-decrypt").disabled = false;
    }
});

// 2. Encriptar para Multiples
document.getElementById("btn-encrypt").addEventListener("click", async () => {
    if (!fileToEncrypt) return;
    
    // Obtener destinatarios checados
    let checkedBoxes = document.querySelectorAll(".recipient-checkbox:checked");
    if (checkedBoxes.length === 0) return alert("Debes seleccionar mínimo a un destinatario.");
    
    let destinatariosElegidos = [];
    checkedBoxes.forEach(cb => {
        let userId = cb.value;
        let usrObj = listaUsuarios.find(u => u.id === userId);
        if(usrObj) {
            // Mandamos los PEMS, en Python los regeneraremos
            destinatariosElegidos.push({
                id: usrObj.id,
                pub_pem: usrObj.public_key
            });
        }
    });

    try {
        let buffer = await fileToEncrypt.arrayBuffer();
        let bytesArray = new Uint8Array(buffer);
        
        let destinatariosJSON = JSON.stringify(destinatariosElegidos);
        
        // Usaremos al primer usuario de la lista como el "Firmante" (Signer) por defecto
        let signer = listaUsuarios[0];
        
        // Inyectar a Python
        engine.globals.set("f_bytes", bytesArray);
        engine.globals.set("f_nombre", fileToEncrypt.name);
        engine.globals.set("f_destinatarios_json", destinatariosJSON);
        engine.globals.set("f_signer_id", signer.id);
        engine.globals.set("f_signer_priv_pem", signer.signing_private_key);
        
        await engine.runPythonAsync(`
            from secure_document_vault.core.facade import encriptar
            from cryptography.hazmat.primitives import serialization
            import json
            
            # Parseamos el JSON de recipients string desde Javascript
            dest_list = json.loads(f_destinatarios_json)
            
            # Recrear objetos Serialization
            objetos_destinatarios = []
            for d in dest_list:
                pub_obj = serialization.load_pem_public_key(d["pub_pem"].encode('utf-8'))
                objetos_destinatarios.append({
                    "id": d["id"],
                    "public_key": pub_obj
                })
            
            # Recrear llave privada del firmante
            signer_priv_obj = serialization.load_pem_private_key(f_signer_priv_pem.encode('utf-8'), password=None)

            # Mandamos llamar al facade multi-usuario nativo tuyo
            vault_bytes = encriptar(bytes(f_bytes), f_nombre, objetos_destinatarios, f_signer_id, signer_priv_obj)
            vault_ba = bytearray(vault_bytes)
        `);
        
        let vaultPyProxy = engine.globals.get('vault_ba');
        let jsUint8Array = vaultPyProxy.toJs();
        vaultPyProxy.destroy(); 
        
        descargarBlob(jsUint8Array, fileToEncrypt.name + ".vault");
        mostrarToast("Archivo Cifrado para " + destinatariosElegidos.length + " cuentas!");
        
    } catch(err) {
        alert("Error cifrando: " + err.message);
        console.error(err);
    }
});

// 3. Descifrar (Simulando estar loggeado)
document.getElementById("btn-decrypt").addEventListener("click", async () => {
    if (!fileToDecrypt) return;
    
    let loginId = document.getElementById("login-selector").value;
    if(!loginId) return alert("Debes seleccionar una cuenta activa primero.");
    
    let loggeado = listaUsuarios.find(u => u.id === loginId);
    
    try {
        let buffer = await fileToDecrypt.arrayBuffer();
        let vaultArray = new Uint8Array(buffer);
        
        engine.globals.set("v_bytes", vaultArray);
        engine.globals.set("v_id", loggeado.id);
        engine.globals.set("v_priv_pem", loggeado.private_key);
        
        // Usamos la llave del primer usuario como la del firmante (demo)
        let signer = listaUsuarios[0];
        engine.globals.set("v_signer_pub_pem", signer.signing_public_key);
        
        await engine.runPythonAsync(`
            from secure_document_vault.core.facade import desencriptar
            from secure_document_vault.core.exceptions import IntegrityErrorException
            from cryptography.hazmat.primitives import serialization
            
            priv_key_obj = serialization.load_pem_private_key(v_priv_pem.encode('utf-8'), password=None)
            signer_pub_obj = serialization.load_pem_public_key(v_signer_pub_pem.encode('utf-8'))
            
            original_bytes = desencriptar(bytes(v_bytes), v_id, priv_key_obj, signer_pub_obj)
            original_ba = bytearray(original_bytes)
            v_error = ""
        `);
        
        let originalPyProxy = engine.globals.get('original_ba');
        let originalBytes = originalPyProxy.toJs();
        originalPyProxy.destroy();
        
        let nombreRecuperado = fileToDecrypt.name.replace(".vault", "");
        descargarBlob(originalBytes, nombreRecuperado);
        mostrarToast("✓ Archivo Recuperado a la perfección como: " + loggeado.name);
        
    } catch(err) {
        // En un ambiente E2EE productivo no revelamos información criptográfica sensible al UI
        alert("🛡️ Acceso Denegado:\\n\\nEl usuario actual no está autorizado para abrir este archivo o el documento se encuentra corrupto.");
        
        // El verdadero error permanece escondido en consola web para los ingenieros
        console.error("Detalle técnico fallido:", err);
    }
});


// Utilidades
function descargarBlob(uint8Array, fName) {
    let blob = new Blob([uint8Array], { type: "application/octet-stream" });
    let url = URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.href = url;
    a.download = fName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function mostrarToast(msg) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 3000);
}

window.onload = iniciarMotor;
