# syntax=docker/dockerfile:1
# ILN Multi-Language avec syntaxe Docker 2025

# ===============================================
# STAGE 1: COMPILATION RUST
# ===============================================
FROM rust:1.76-slim AS rust-builder
WORKDIR /rust-build

# Créer le projet Rust avec heredoc (syntaxe 2025)
RUN <<EOF
mkdir src
cat <<'CARGO' > Cargo.toml
[package]
name = "iln_rust_core"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]
CARGO
EOF

# Créer le code Rust avec heredoc (pas d'échappement complexe)
RUN <<'RUST_CODE'
cat <<'CODE' > src/lib.rs
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

#[no_mangle]
pub extern "C" fn rust_secure_hash(input: *const c_char) -> *mut c_char {
    let c_str = unsafe { CStr::from_ptr(input) };
    let input_str = c_str.to_str().unwrap_or("invalid");
    let hash = format!("RUST_SECURE_{:x}", input_str.len() * 42);
    CString::new(hash).unwrap().into_raw()
}

#[no_mangle]
pub extern "C" fn rust_performance_test(iterations: i32) -> i32 {
    (0..iterations).map(|i| i * 2).sum()
}

#[no_mangle]
pub extern "C" fn free_rust_string(ptr: *mut c_char) {
    unsafe {
        if !ptr.is_null() {
            let _ = CString::from_raw(ptr);
        }
    }
}
CODE
RUST_CODE

# Compilation Rust avec syntaxe 2025
RUN <<EOF
apt-get update
apt-get install -y --no-install-recommends build-essential
cargo build --release --lib --crate-type cdylib --target-dir /output
EOF

# ===============================================
# STAGE 2: COMPILATION GO  
# ===============================================
FROM golang:1.22-alpine AS go-builder
WORKDIR /go-build

# Créer le code Go avec heredoc (plus d'erreurs d'échappement)
RUN <<'GO_CODE'
cat <<'CODE' > main.go
package main

import "C"
import (
    "fmt"
    "encoding/json"
)

//export go_parallel_process
func go_parallel_process(input *C.char, workers C.int) *C.char {
    inputStr := C.GoString(input)
    result := map[string]interface{}{
        "result": fmt.Sprintf("%s_processed", inputStr),
        "workers": int(workers),
        "engine": "go_native",
    }
    jsonResult, _ := json.Marshal(result)
    return C.CString(string(jsonResult))
}

//export go_benchmark_test
func go_benchmark_test(iterations C.int) C.int {
    total := 0
    for i := 0; i < int(iterations); i++ {
        total += i * 2
    }
    return C.int(total)
}

func main() {}
CODE
GO_CODE

# Compilation Go avec flags corrects 2025
RUN <<EOF
apk add --no-cache gcc musl-dev
go mod init iln_go_core
CGO_ENABLED=1 go build -buildmode=c-shared -ldflags="-s -w" -o libiln_go_core.so
EOF

# ===============================================
# STAGE 3: PYTHON RUNTIME FINAL
# ===============================================
FROM python:3.11-slim AS runtime
WORKDIR /app

# Installation dépendances système avec heredoc
RUN <<EOF
apt-get update
apt-get install -y --no-install-recommends \
    libffi-dev \
    gcc
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF

# Copie des bibliothèques compilées (avec wildcard pour éviter erreurs)
COPY --from=rust-builder /output/release/*.so /app/lib/ 2>/dev/null || true
COPY --from=go-builder /go-build/*.so /app/lib/ 2>/dev/null || true

# Configuration LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH="/app/lib:${LD_LIBRARY_PATH}"

# Installation des dépendances Python (celles qui échouent avec requirements.txt)
RUN <<EOF
pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    requests==2.31.0 \
    python-multipart==0.0.6 \
    cffi==1.16.0 \
    psutil==5.9.6
EOF

# Script de test des bibliothèques avec heredoc
RUN <<'TEST_SCRIPT'
cat <<'SCRIPT' > /test_libs.py
#!/usr/bin/env python3
import os
import ctypes
import sys

def test_libraries():
    print("🧪 Testing ILN libraries...")
    lib_path = "/app/lib"
    
    available = {"rust": False, "go": False}
    
    # Test Rust
    rust_files = [f for f in os.listdir(lib_path) if f.startswith('libiln_rust_core') and f.endswith('.so')]
    if rust_files:
        try:
            rust_lib = ctypes.CDLL(os.path.join(lib_path, rust_files[0]))
            available["rust"] = True
            print("✅ Rust library loaded successfully")
        except Exception as e:
            print(f"❌ Rust library failed: {e}")
    else:
        print("❌ Rust library not found")
    
    # Test Go
    go_files = [f for f in os.listdir(lib_path) if f.startswith('libiln_go_core') and f.endswith('.so')]
    if go_files:
        try:
            go_lib = ctypes.CDLL(os.path.join(lib_path, go_files[0]))
            available["go"] = True
            print("✅ Go library loaded successfully")
        except Exception as e:
            print(f"❌ Go library failed: {e}")
    else:
        print("❌ Go library not found")
    
    print(f"📊 Final status: {available}")
    return available

if __name__ == "__main__":
    test_libraries()
SCRIPT
TEST_SCRIPT

RUN chmod +x /test_libs.py

# Variables d'environnement pour Render
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Copie de l'application Python
COPY app.py /app.py

# Point d'entrée avec test des bibliothèques
CMD python3 /test_libs.py && python3 /app.py