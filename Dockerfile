# ======================================================================
# 🌌 NEXUS MULTI-LANGUAGE TEST - Version Fichier Unique Robuste
# ======================================================================

# ===============================================
# 🦀 ÉTAPE 1: COMPILER LA BIBLIOTHÈQUE RUST
# ===============================================
FROM rust:1.70 AS rust-builder
WORKDIR /rust

# Créer le Cargo.toml avec une méthode plus portable (echo)
RUN echo '[package]' > Cargo.toml && \
    echo 'name = "nexus_rust"' >> Cargo.toml && \
    echo 'version = "0.1.0"' >> Cargo.toml && \
    echo 'edition = "2021"' >> Cargo.toml && \
    echo '' >> Cargo.toml && \
    echo '[lib]' >> Cargo.toml && \
    echo 'name = "nexus_rust"' >> Cargo.toml && \
    echo 'crate-type = ["cdylib"]' >> Cargo.toml

# Créer le code source Rust
RUN mkdir src
RUN echo 'use std::ffi::{CStr, CString};' > src/lib.rs && \
    echo 'use std::os::raw::c_char;' >> src/lib.rs && \
    echo '' >> src/lib.rs && \
    echo '#[no_mangle]' >> src/lib.rs && \
    echo 'pub extern "C" fn rust_hello() -> *mut c_char {' >> src/lib.rs && \
    echo '    let response = CString::new("Hello from Rust! 🦀").unwrap();' >> src/lib.rs && \
    echo '    response.into_raw()' >> src/lib.rs && \
    echo '}' >> src/lib.rs && \
    echo '' >> src/lib.rs && \
    echo '#[no_mangle]' >> src/lib.rs && \
    echo 'pub extern "C" fn rust_compute(x: i32, y: i32) -> i32 {' >> src/lib.rs && \
    echo '    x * y + 42' >> src/lib.rs && \
    echo '}' >> src/lib.rs && \
    echo '' >> src/lib.rs && \
    echo '#[no_mangle]' >> src/lib.rs && \
    echo 'pub extern "C" fn free_string(s: *mut c_char) {' >> src/lib.rs && \
    echo '    if s.is_null() { return; }' >> src/lib.rs && \
    echo '    unsafe { let _ = CString::from_raw(s); }' >> src/lib.rs && \
    echo '}' >> src/lib.rs

# Compiler la bibliothèque Rust
RUN cargo build --release

# ===============================================
# 🐍 ÉTAPE 2: APPLICATION PYTHON FINALE
# ===============================================
FROM python:3.11-slim
WORKDIR /app

# Installer les dépendances Python
RUN pip install --no-cache-dir flask gunicorn

# Copier la bibliothèque Rust compilée depuis l'étage précédent
COPY --from=rust-builder /rust/target/release/libnexus_rust.so /usr/local/lib/

# Créer l'application Flask (app.py)
RUN <<EOF > app.py
import ctypes, os
from flask import Flask, jsonify, render_template

app = Flask(__name__)

try:
    rust_lib = ctypes.CDLL("/usr/local/lib/libnexus_rust.so")
    rust_lib.rust_hello.restype = ctypes.c_char_p
    rust_lib.rust_compute.argtypes = [ctypes.c_int, ctypes.c_int]
    rust_lib.rust_compute.restype = ctypes.c_int
    rust_lib.free_string.argtypes = [ctypes.c_char_p]
    RUST_LOADED = True
except OSError as e:
    RUST_LOADED = False
    RUST_ERROR = str(e)

@app.route("/")
def home(): return render_template('index.html')

@app.route("/api/rust-hello")
def rust_hello_route():
    if not RUST_LOADED: return jsonify({"error": "Rust lib not loaded", "details": RUST_ERROR}), 500
    p = None
    try:
        p = rust_lib.rust_hello()
        return jsonify({"rust_says": p.decode("utf-8")})
    finally:
        if p: rust_lib.free_string(p)

@app.route("/api/rust-compute/<int:x>/<int:y>")
def rust_compute_route(x, y):
    if not RUST_LOADED: return jsonify({"error": "Rust lib not loaded", "details": RUST_ERROR}), 500
    res = rust_lib.rust_compute(x, y)
    return jsonify({"input": {"x": x, "y": y}, "result": res})

@app.route("/api/health")
def health():
    rust_ok = False
    if RUST_LOADED:
        try:
            if rust_lib.rust_compute(2, 3) == 48: rust_ok = True
        except: pass
    return jsonify({"python": "OK", "rust": "OK" if rust_ok else "ERROR"})
EOF

# Créer le template HTML/JS (avec les '$' échappés pour le shell)
RUN mkdir templates
RUN <<EOF > templates/index.html
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🌌 NEXUS Test</title><script src="https://cdn.tailwindcss.com"></script><style>body{background-color:#111827;color:#d1d5db}.card{background-color:#1f2937;border:1px solid #374151}.btn{transition:all .2s ease-in-out}.btn:hover{transform:translateY(-2px);box-shadow:0 4px 10px rgba(0,0,0,.4)}.status-ok{color:#22c55e}.status-error{color:#ef4444}</style></head><body class="font-sans flex items-center justify-center min-h-screen p-4"><div class="w-full max-w-2xl mx-auto space-y-8"><div class="text-center"><h1 class="text-4xl font-bold text-white">🌌 NEXUS Multi-Language Test</h1><p class="text-lg text-gray-400 mt-2">App <span class="font-semibold text-cyan-400">Python 🐍</span> & <span class="font-semibold text-orange-400">Rust 🦀</span></p></div><div class="card p-6 rounded-lg shadow-lg"><h2 class="text-2xl font-semibold text-white mb-4">1. Salutation Rust</h2><button id="btn-hello" class="btn bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 px-4 rounded-lg w-full">Appeler <code>rust_hello()</code></button><pre id="result-hello" class="mt-4 bg-gray-900 p-4 rounded-md text-gray-300 h-24 overflow-auto">Cliquez pour obtenir une réponse...</pre></div><div class="card p-6 rounded-lg shadow-lg"><h2 class="text-2xl font-semibold text-white mb-4">2. Calcul Rust</h2><div class="flex space-x-4 mb-4"><input type="number" id="input-x" value="7" class="w-1/2 bg-gray-700 text-white border border-gray-600 rounded-lg p-2 text-center focus:outline-none focus:ring-2 focus:ring-orange-500"><span class="text-2xl font-bold text-gray-400 self-center">*</span><input type="number" id="input-y" value="6" class="w-1/2 bg-gray-700 text-white border border-gray-600 rounded-lg p-2 text-center focus:outline-none focus:ring-2 focus:ring-orange-500"></div><button id="btn-compute" class="btn bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 px-4 rounded-lg w-full">Appeler <code>rust_compute(x, y)</code></button><pre id="result-compute" class="mt-4 bg-gray-900 p-4 rounded-md text-gray-300 h-24 overflow-auto">Entrez des nombres et cliquez...</pre></div><div class="card p-4 rounded-lg text-center"><h2 class="text-xl font-semibold text-white">Statut</h2><div id="status-container" class="mt-2 text-lg">Vérification...</div></div></div><script>function showResult(e,t,s,c){const l=document.getElementById(e);l.textContent=s?"Chargement...":JSON.stringify(t,null,2),l.style.color=c?"#ef4444":"#d1d5db"}document.getElementById("btn-hello").addEventListener("click",async()=>{showResult("result-hello",null,!0);try{const e=await fetch("/api/rust-hello"),t=await e.json();if(!e.ok)throw t;showResult("result-hello",t)}catch(e){showResult("result-hello",e,!1,!0)}}),document.getElementById("btn-compute").addEventListener("click",async()=>{const e=document.getElementById("input-x").value,t=document.getElementById("input-y").value;showResult("result-compute",null,!0);try{const s=await fetch(`/api/rust-compute/\${e}/\${t}`),c=await s.json();if(!s.ok)throw c;showResult("result-compute",c)}catch(e){showResult("result-compute",e,!1,!0)}}),async function(){const e=document.getElementById("status-container");try{const t=await fetch("/api/health"),s=await t.json();e.innerHTML=`🐍 Python: <span class="status-ok">\${s.python}</span> | 🦀 Rust: <span class="\${"OK"===s.rust?"status-ok":"status-error"}">\${s.rust}</span>`}catch(t){e.innerHTML='<span class="status-error">Erreur de connexion.</span>'}}();</script></body></html>
EOF

# Variables d'environnement
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 5000

# Commande de démarrage avec Gunicorn pour la production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

