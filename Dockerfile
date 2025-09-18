# 🌌 NEXUS MULTI-LANGUAGE TEST - Simple & Deployable
# Python + Rust dans un seul container Docker

# ===============================================
# 🦀 ÉTAPE 1: COMPILER RUST
# ===============================================
FROM rust:1.70 AS rust-builder

WORKDIR /rust
RUN echo 'fn main() {}' > src/main.rs
RUN echo '[package]
name = "nexus-rust"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]' > Cargo.toml

# Code Rust simple pour test
RUN echo 'use std::ffi::{CStr, CString};
use std::os::raw::c_char;

#[no_mangle]
pub extern "C" fn rust_hello() -> *mut c_char {
    let response = CString::new("Hello from Rust! 🦀").unwrap();
    response.into_raw()
}

#[no_mangle]
pub extern "C" fn rust_compute(x: i32, y: i32) -> i32 {
    x * y + 42
}

#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    unsafe {
        if s.is_null() { return; }
        CString::from_raw(s);
    }
}' > src/lib.rs

# Compiler la bibliothèque Rust
RUN cargo build --release --lib

# ===============================================
# 🐍 ÉTAPE 2: APPLICATION PYTHON
# ===============================================
FROM python:3.11-slim AS final

# Copier la bibliothèque Rust compilée
COPY --from=rust-builder /rust/target/release/libnexus_rust.so /usr/local/lib/

# Installer les dépendances Python
RUN pip install --no-cache-dir flask gunicorn

# Code Python qui utilise Rust
RUN echo 'import ctypes
from flask import Flask, jsonify

app = Flask(__name__)

# Charger la bibliothèque Rust
rust_lib = ctypes.CDLL("/usr/local/lib/libnexus_rust.so")

# Configurer les types de fonctions
rust_lib.rust_hello.restype = ctypes.c_char_p
rust_lib.rust_compute.argtypes = [ctypes.c_int, ctypes.c_int]
rust_lib.rust_compute.restype = ctypes.c_int

@app.route("/")
def home():
    return {
        "message": "🌌 NEXUS Multi-Language Container",
        "languages": ["Python 🐍", "Rust 🦀"],
        "status": "SUCCESS"
    }

@app.route("/rust-hello")
def rust_hello():
    message = rust_lib.rust_hello().decode("utf-8")
    return {"rust_says": message}

@app.route("/rust-compute/<int:x>/<int:y>")
def rust_compute(x, y):
    result = rust_lib.rust_compute(x, y)
    return {
        "input": {"x": x, "y": y},
        "rust_computation": f"{x} * {y} + 42 = {result}",
        "result": result
    }

@app.route("/health")
def health():
    try:
        # Test que Rust fonctionne
        test_result = rust_lib.rust_compute(2, 3)
        rust_working = test_result == 48  # 2*3+42 = 48
        
        return {
            "status": "healthy" if rust_working else "error",
            "python": "OK",
            "rust": "OK" if rust_working else "ERROR",
            "test_computation": test_result
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
' > /app.py

# Variables d'environnement
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "/app.py"]
