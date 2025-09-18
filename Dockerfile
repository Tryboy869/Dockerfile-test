# ======================================================================
# 🌌 NEXUS MULTI-LANGUAGE TEST - Version Fichier Unique
# Python + Rust + Frontend dans un seul container Docker auto-suffisant
# ======================================================================

# ===============================================
# 🦀 ÉTAPE 1: COMPILER LA BIBLIOTHÈQUE RUST
# ===============================================
# On utilise une image Rust officielle comme "builder"
FROM rust:1.70 AS rust-builder

WORKDIR /rust

# Créer le fichier de configuration Cargo.toml
RUN <<EOF > Cargo.toml
[package]
name = "nexus_rust"
version = "0.1.0"
edition = "2021"

[lib]
name = "nexus_rust"
# "cdylib" produit une bibliothèque dynamique compatible C
crate-type = ["cdylib"]
EOF

# Créer le répertoire source et le code Rust
RUN mkdir src
RUN <<EOF > src/lib.rs
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

/// Renvoie une chaîne de caractères allouée par Rust.
/// L'appelant est responsable de la libération de la mémoire via free_string.
#[no_mangle]
pub extern "C" fn rust_hello() -> *mut c_char {
    let response = CString::new("Hello from Rust! 🦀").unwrap();
    response.into_raw()
}

/// Effectue un calcul simple.
#[no_mangle]
pub extern "C" fn rust_compute(x: i32, y: i32) -> i32 {
    x * y + 42
}

/// CORRECTION CRITIQUE: Libère la mémoire allouée par Rust.
/// Sans cela, chaque appel à rust_hello() causerait une fuite de mémoire.
#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    if s.is_null() {
        return;
    }
    unsafe {
        // from_raw reprend possession du pointeur et libère la mémoire
        // automatiquement à la fin de cette fonction.
        let _ = CString::from_raw(s);
    }
}
EOF

# Compiler la bibliothèque Rust en mode "release" pour les performances
RUN cargo build --release

# ===============================================
# 🐍 ÉTAPE 2: APPLICATION PYTHON FINALE
# ===============================================
# On utilise une image Python légère pour l'application finale
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances Python (Flask et Gunicorn pour la production)
RUN pip install --no-cache-dir flask gunicorn

# Copier la bibliothèque Rust compilée depuis l'étage de build précédent
COPY --from=rust-builder /rust/target/release/libnexus_rust.so /usr/local/lib/

# Créer l'application Flask (app.py)
RUN <<EOF > app.py
import ctypes
import os
from flask import Flask, jsonify, render_template

# Initialisation de l'application Flask
app = Flask(__name__)

# --- Chargement de la bibliothèque Rust ---
try:
    rust_lib = ctypes.CDLL("/usr/local/lib/libnexus_rust.so")

    # --- Configuration des signatures de fonctions ---
    rust_lib.rust_hello.restype = ctypes.c_char_p
    rust_lib.rust_compute.argtypes = [ctypes.c_int, ctypes.c_int]
    rust_lib.rust_compute.restype = ctypes.c_int
    
    # CORRECTION: Définir la signature pour la fonction de libération mémoire
    rust_lib.free_string.argtypes = [ctypes.c_char_p]
    
    RUST_LOADED = True
except OSError as e:
    RUST_LOADED = False
    RUST_ERROR = str(e)

# --- Routes de l'API et du Frontend ---

@app.route("/")
def home():
    """Sert la page HTML principale qui contient le client JS."""
    return render_template('index.html')

@app.route("/api/rust-hello")
def rust_hello_route():
    if not RUST_LOADED:
        return jsonify({"error": "Bibliothèque Rust non chargée", "details": RUST_ERROR}), 500

    rust_pointer = None
    try:
        # Appeler Rust, qui nous donne un pointeur mémoire
        rust_pointer = rust_lib.rust_hello()
        message = rust_pointer.decode("utf-8")
        return jsonify({"rust_says": message})
    finally:
        # CORRECTION: On s'assure de toujours libérer la mémoire allouée par Rust
        if rust_pointer:
            rust_lib.free_string(rust_pointer)

@app.route("/api/rust-compute/<int:x>/<int:y>")
def rust_compute_route(x, y):
    if not RUST_LOADED:
        return jsonify({"error": "Bibliothèque Rust non chargée", "details": RUST_ERROR}), 500
    
    result = rust_lib.rust_compute(x, y)
    return jsonify({
        "input": {"x": x, "y": y},
        "rust_computation": f"{x} * {y} + 42 = {result}",
        "result": result
    })

@app.route("/api/health")
def health():
    rust_status = "ERROR"
    test_result = None
    if RUST_LOADED:
        try:
            test_result = rust_lib.rust_compute(2, 3)
            if test_result == 48:
                rust_status = "OK"
        except Exception:
            pass

    return jsonify({
        "status": "healthy" if rust_status == "OK" else "unhealthy",
        "python": "OK",
        "rust": rust_status
    })
EOF

# Créer le répertoire des templates et le fichier HTML/JS
RUN mkdir templates
RUN <<EOF > templates/index.html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌌 NEXUS Multi-Language Test</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #111827; color: #d1d5db; }
        .card { background-color: #1f2937; border: 1px solid #374151; }
        .btn { transition: all 0.2s ease-in-out; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4); }
        .status-ok { color: #22c55e; } .status-error { color: #ef4444; }
    </style>
</head>
<body class="font-sans flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-2xl mx-auto space-y-8">
        <div class="text-center">
            <h1 class="text-4xl font-bold text-white">🌌 NEXUS Multi-Language Test</h1>
            <p class="text-lg text-gray-400 mt-2">Une app <span class="font-semibold text-cyan-400">Python 🐍</span> appelant du code <span class="font-semibold text-orange-400">Rust 🦀</span>.</p>
        </div>
        <div class="card p-6 rounded-lg shadow-lg">
            <h2 class="text-2xl font-semibold text-white mb-4">1. Salutation depuis Rust</h2>
            <button id="btn-hello" class="btn bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 px-4 rounded-lg w-full">Appeler <code>rust_hello()</code></button>
            <pre id="result-hello" class="mt-4 bg-gray-900 p-4 rounded-md text-gray-300 h-24 overflow-auto">Cliquez pour obtenir une réponse...</pre>
        </div>
        <div class="card p-6 rounded-lg shadow-lg">
            <h2 class="text-2xl font-semibold text-white mb-4">2. Calcul avec Rust</h2>
            <div class="flex space-x-4 mb-4">
                <input type="number" id="input-x" value="7" class="w-1/2 bg-gray-700 text-white border border-gray-600 rounded-lg p-2 text-center focus:outline-none focus:ring-2 focus:ring-orange-500">
                <span class="text-2xl font-bold text-gray-400 self-center">*</span>
                <input type="number" id="input-y" value="6" class="w-1/2 bg-gray-700 text-white border border-gray-600 rounded-lg p-2 text-center focus:outline-none focus:ring-2 focus:ring-orange-500">
            </div>
            <button id="btn-compute" class="btn bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 px-4 rounded-lg w-full">Appeler <code>rust_compute(x, y)</code></button>
            <pre id="result-compute" class="mt-4 bg-gray-900 p-4 rounded-md text-gray-300 h-32 overflow-auto">Entrez des nombres et cliquez...</pre>
        </div>
        <div class="card p-4 rounded-lg text-center">
             <h2 class="text-xl font-semibold text-white">Statut du Système</h2>
             <div id="status-container" class="mt-2 text-lg">Vérification...</div>
        </div>
    </div>
    <script>
        function showResult(elId, data, isLoading=false, isError=false) {
            const el = document.getElementById(elId);
            el.textContent = isLoading ? 'Chargement...' : JSON.stringify(data, null, 2);
            el.style.color = isError ? '#ef4444' : '#d1d5db';
        }
        document.getElementById('btn-hello').addEventListener('click', async () => {
            showResult('result-hello', null, true);
            try {
                const res = await fetch('/api/rust-hello');
                const data = await res.json();
                if (!res.ok) throw data;
                showResult('result-hello', data);
            } catch (err) { showResult('result-hello', err, false, true); }
        });
        document.getElementById('btn-compute').addEventListener('click', async () => {
            const x = document.getElementById('input-x').value;
            const y = document.getElementById('input-y').value;
            showResult('result-compute', null, true);
            try {
                const res = await fetch(`/api/rust-compute/\${x}/\${y}`);
                const data = await res.json();
                if (!res.ok) throw data;
                showResult('result-compute', data);
            } catch (err) { showResult('result-compute', err, false, true); }
        });
        async function checkHealth() {
            const statusEl = document.getElementById('status-container');
            try {
                const res = await fetch('/api/health');
                const data = await res.json();
                const pyStatus = `<span class="status-ok">\${data.python}</span>`;
                const rustStatus = data.rust === 'OK' ? `<span class="status-ok">\${data.rust}</span>` : `<span class="status-error">\${data.rust}</span>`;
                statusEl.innerHTML = `🐍 Python: \${pyStatus} | 🦀 Rust: \${rustStatus}`;
            } catch (err) { statusEl.innerHTML = `<span class="status-error">Erreur de connexion.</span>`; }
        }
        window.onload = checkHealth;
    </script>
EOF

# Variables d'environnement
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 5000

# CORRECTION: Commande de démarrage avec Gunicorn, le serveur de production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]

