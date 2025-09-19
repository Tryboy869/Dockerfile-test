#!/usr/bin/env python3
"""
ILN Advanced Application - Test des Limites Techniques
Architecture Progressive : Python + Rust + Go avec fallbacks intelligents
"""

import os
import sys
import ctypes
import json
import time
import psutil
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager

# FastAPI et dépendances avancées
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, validator
import uvicorn
import requests
import asyncpg
import aiofiles

# ===============================================
# SYSTÈME DE DÉTECTION DES CAPACITÉS ILN
# ===============================================
class ILNCapabilityDetector:
    """Détecte automatiquement les capacités disponibles dans le container"""
    
    def __init__(self):
        self.capabilities = {
            "rust": False,
            "go": False,
            "python": True,  # Toujours disponible
            "native_libs": False,
            "async_support": False,
            "database_support": False,
        }
        self._detect_all_capabilities()
    
    def _detect_all_capabilities(self):
        """Détection progressive des capacités"""
        
        # Test Rust
        try:
            self.rust_lib = ctypes.CDLL("/usr/lib/libiln_rust_core.so")
            self._setup_rust_bindings()
            self.capabilities["rust"] = True
            print("🦀 Rust capabilities detected")
        except OSError:
            self.capabilities["rust"] = False
            print("⚠️ Rust capabilities not available - using Python fallbacks")
        
        # Test Go
        try:
            self.go_lib = ctypes.CDLL("/usr/lib/libiln_go_core.so")
            self._setup_go_bindings()
            self.capabilities["go"] = True
            print("🐹 Go capabilities detected")
        except OSError:
            self.capabilities["go"] = False
            print("⚠️ Go capabilities not available - using Python fallbacks")
        
        # Test support async
        try:
            import asyncio
            import aiofiles
            self.capabilities["async_support"] = True
            print("⚡ Async capabilities available")
        except ImportError:
            self.capabilities["async_support"] = False
        
        # Test support database
        try:
            import asyncpg
            self.capabilities["database_support"] = True
            print("🗄️ Database capabilities available")
        except ImportError:
            self.capabilities["database_support"] = False
    
    def _setup_rust_bindings(self):
        """Configuration des bindings Rust"""
        if not self.capabilities["rust"]:
            return
        
        # rust_secure_process
        self.rust_lib.rust_secure_process.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self.rust_lib.rust_secure_process.restype = ctypes.c_char_p
        
        # free_rust_string
        self.rust_lib.free_rust_string.argtypes = [ctypes.c_char_p]
        self.rust_lib.free_rust_string.restype = None
    
    def _setup_go_bindings(self):
        """Configuration des bindings Go"""
        if not self.capabilities["go"]:
            return
        
        # go_concurrent_process
        self.go_lib.go_concurrent_process.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.go_lib.go_concurrent_process.restype = ctypes.c_char_p
        
        # go_memory_benchmark
        self.go_lib.go_memory_benchmark.argtypes = []
        self.go_lib.go_memory_benchmark.restype = ctypes.c_char_p

# ===============================================
# IMPLÉMENTATION DES ESSENCES ILN
# ===============================================
class ILNEssenceEngine:
    """Moteur principal des essences ILN avec fallbacks intelligents"""
    
    def __init__(self):
        self.detector = ILNCapabilityDetector()
        self.performance_metrics = {
            "requests_processed": 0,
            "average_response_time": 0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
        }
    
    def own_secure(self, data: str, mode: str = "balanced") -> Dict[str, Any]:
        """Essence Rust: Ownership sécurisé avec fallback Python"""
        start_time = time.time()
        
        if self.capabilities["rust"] and mode in ["secure", "balanced"]:
            try:
                # Appel natif Rust
                data_bytes = data.encode('utf-8')
                result_ptr = self.detector.rust_lib.rust_secure_process(data_bytes, len(data_bytes))
                result_json = ctypes.string_at(result_ptr).decode('utf-8')
                self.detector.rust_lib.free_rust_string(result_ptr)
                
                result = json.loads(result_json)
                result["engine"] = "rust_native"
                result["processing_time"] = time.time() - start_time
                return result
                
            except Exception as e:
                print(f"Rust processing failed: {e}, falling back to Python")
        
        # Fallback Python
        import hashlib
        secure_hash = hashlib.sha256(data.encode()).hexdigest()[:16]
        
        return {
            "secure_hash": secure_hash,
            "length": len(data),
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "engine": "python_fallback",
            "processing_time": time.time() - start_time
        }
    
    def chan_parallel(self, data: str, workers: int = 4) -> Dict[str, Any]:
        """Essence Go: Traitement parallèle avec fallback asyncio"""
        start_time = time.time()
        
        if self.capabilities["go"]:
            try:
                # Appel natif Go
                data_bytes = data.encode('utf-8')
                result_ptr = self.detector.go_lib.go_concurrent_process(data_bytes, workers)
                result_json = ctypes.string_at(result_ptr).decode('utf-8')
                self.detector.go_lib.free_go_string(result_ptr)
                
                result = json.loads(result_json)
                result["engine"] = "go_native"
                result["processing_time"] = time.time() - start_time
                return result
                
            except Exception as e:
                print(f"Go processing failed: {e}, falling back to Python asyncio")
        
        # Fallback Python asyncio
        import concurrent.futures
        
        def process_chunk(chunk_id):
            return f"python_worker_{chunk_id}_processed_{data[:10]}"
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(process_chunk, i) for i in range(workers)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return {
            "results": results,
            "worker_count": workers,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "goroutines": workers,  # Équivalent
            "engine": "python_asyncio_fallback",
            "processing_time": time.time() - start_time
        }
    
    def event_reactive(self, data: str, event_type: str = "process") -> Dict[str, Any]:
        """Essence JavaScript: Réactivité événementielle native Python"""
        start_time = time.time()
        
        # Simulation événementielle avec asyncio
        event_id = f"{event_type}_{int(time.time() * 1000)}"
        
        # Calcul de score de réactivité
        reactivity_score = len(data) * 0.314159  # Pi approximation
        
        return {
            "event_id": event_id,
            "event_type": event_type,
            "reactivity_score": round(reactivity_score, 3),
            "data_length": len(data),
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "engine": "python_event_simulation",
            "processing_time": time.time() - start_time
        }
    
    @property
    def capabilities(self):
        return self.detector.capabilities
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Métriques système détaillées"""
        process = psutil.Process()
        
        return {
            "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": round(process.cpu_percent(), 2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "capabilities": self.capabilities,
            "requests_processed": self.performance_metrics["requests_processed"],
        }

# ===============================================
# MODÈLES DE DONNÉES AVANCÉS
# ===============================================
class ILNProcessingRequest(BaseModel):
    data: str
    processing_mode: str = "balanced"  # secure, fast, reactive, balanced
    use_native_libs: bool = True
    workers: int = 4
    benchmark: bool = False
    
    @validator("processing_mode")
    def validate_mode(cls, v):
        valid_modes = ["secure", "fast", "reactive", "balanced", "benchmark"]
        if v not in valid_modes:
            raise ValueError(f"Mode must be one of: {valid_modes}")
        return v

class ILNProcessingResult(BaseModel):
    status: str
    original_data: str
    security_result: Dict[str, Any]
    parallel_result: Dict[str, Any]
    reactive_result: Dict[str, Any]
    processing_mode: str
    total_processing_time: float
    system_metrics: Dict[str, Any]
    capabilities_used: List[str]
    timestamp: datetime

# ===============================================
# APPLICATION FASTAPI AVANCÉE
# ===============================================

# Initialisation de l'engine ILN
iln_engine = ILNEssenceEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🌌 ILN Advanced Application Starting...")
    print(f"🧪 Detected capabilities: {iln_engine.capabilities}")
    
    # Warm-up des bibliothèques
    if iln_engine.capabilities["rust"]:
        test_result = iln_engine.own_secure("warmup_test")
        print(f"🦀 Rust warm-up: {test_result['engine']}")
    
    if iln_engine.capabilities["go"]:
        test_result = iln_engine.chan_parallel("warmup_test", 2)
        print(f"🐹 Go warm-up: {test_result['engine']}")
    
    print("✅ All systems ready!")
    yield
    print("🛑 ILN Application shutting down...")

app = FastAPI(
    title="🌌 ILN Advanced Multi-Language Engine",
    description="Test des limites : Python + Rust + Go avec fallbacks intelligents",
    version="2.0.0-advanced",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================================
# ROUTES AVANCÉES
# ===============================================

@app.get("/")
async def advanced_dashboard():
    """Dashboard interactif avec métriques en temps réel"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌌 ILN Advanced Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
            .metric-card { background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; }
            .capability-indicator { display: inline-block; padding: 5px 10px; margin: 5px; border-radius: 20px; font-size: 12px; }
            .available { background: #4CAF50; }
            .fallback { background: #FF9800; }
            .unavailable { background: #f44336; }
            .test-section { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }
            input, textarea, select { width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 8px; background: rgba(255,255,255,0.9); color: #333; }
            button { background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 10px 5px; }
            button:hover { transform: translateY(-2px); transition: all 0.3s; }
            .results { background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin: 20px 0; white-space: pre-wrap; font-family: monospace; }
            .benchmark-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>🌌 ILN Advanced Multi-Language Engine</h1>
            <p>Test des limites techniques : Architecture progressive avec fallbacks intelligents</p>
            
            <div id="capabilities-status" class="test-section">
                <h3>🧪 Capacités Système</h3>
                <div id="capability-indicators">Chargement des capacités...</div>
            </div>
            
            <div class="metrics-grid" id="metrics-grid">
                <div class="metric-card">
                    <h4>📊 Métriques Temps Réel</h4>
                    <div id="real-time-metrics">Chargement...</div>
                </div>
                <div class="metric-card">
                    <h4>🔥 Performance</h4>
                    <canvas id="performance-chart" width="200" height="100"></canvas>
                </div>
            </div>
            
            <div class="test-section">
                <h3>🚀 Test Multi-Language Processing</h3>
                <textarea id="test-data" rows="4" placeholder="Entrez les données à traiter...">Test de l'architecture ILN avancée avec Rust pour la sécurité, Go pour la concurrence, et Python pour l'orchestration intelligente.</textarea>
                
                <div class="benchmark-grid">
                    <div>
                        <label>Mode de traitement :</label>
                        <select id="processing-mode">
                            <option value="balanced">🎯 Balanced (Toutes essences)</option>
                            <option value="secure">🦀 Secure (Priorité Rust)</option>
                            <option value="fast">🐹 Fast (Priorité Go)</option>
                            <option value="reactive">⚡ Reactive (Événementiel)</option>
                            <option value="benchmark">🏁 Benchmark (Test complet)</option>
                        </select>
                    </div>
                    
                    <div>
                        <label>Workers parallèles :</label>
                        <select id="workers">
                            <option value="2">2 Workers</option>
                            <option value="4" selected>4 Workers</option>
                            <option value="8">8 Workers</option>
                            <option value="16">16 Workers</option>
                        </select>
                    </div>
                </div>
                
                <button onclick="runAdvancedTest()">🚀 Lancer Test Avancé</button>
                <button onclick="runBenchmarkSuite()">🏁 Suite de Benchmarks</button>
                <button onclick="startRealtimeMonitoring()">📊 Monitoring Temps Réel</button>
            </div>
            
            <div class="results" id="results">
                Cliquez sur "Lancer Test Avancé" pour commencer les tests multi-langages...
            </div>
        </div>

        <script>
            let performanceChart;
            let monitoringInterval;
            
            // Initialisation
            document.addEventListener('DOMContentLoaded', function() {
                loadCapabilities();
                initPerformanceChart();
                loadMetrics();
            });
            
            async function loadCapabilities() {
                try {
                    const response = await fetch('/capabilities');
                    const caps = await response.json();
                    
                    let html = '';
                    for (const [capability, available] of Object.entries(caps.capabilities)) {
                        const className = available ? 'available' : 'fallback';
                        const status = available ? '✅' : '⚠️';
                        html += `<span class="capability-indicator ${className}">${status} ${capability.toUpperCase()}</span>`;
                    }
                    
                    document.getElementById('capability-indicators').innerHTML = html;
                    
                } catch (error) {
                    console.error('Error loading capabilities:', error);
                }
            }
            
            async function loadMetrics() {
                try {
                    const response = await fetch('/metrics');
                    const metrics = await response.json();
                    
                    document.getElementById('real-time-metrics').innerHTML = `
                        <strong>Memory:</strong> ${metrics.memory_usage_mb} MB<br>
                        <strong>CPU:</strong> ${metrics.cpu_percent}%<br>
                        <strong>Threads:</strong> ${metrics.threads}<br>
                        <strong>Requests:</strong> ${metrics.requests_processed}
                    `;
                    
                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }
            
            function initPerformanceChart() {
                const ctx = document.getElementById('performance-chart').getContext('2d');
                performanceChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['Rust', 'Go', 'Python', 'Combined'],
                        datasets: [{
                            label: 'Processing Time (ms)',
                            data: [0, 0, 0, 0],
                            borderColor: '#4ECDC4',
                            backgroundColor: 'rgba(78, 205, 196, 0.2)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            }
            
            async function runAdvancedTest() {
                const data = document.getElementById('test-data').value;
                const mode = document.getElementById('processing-mode').value;
                const workers = document.getElementById('workers').value;
                
                document.getElementById('results').innerHTML = '🔄 Processing with multiple language engines...';
                
                try {
                    const response = await fetch('/process-advanced', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            data: data,
                            processing_mode: mode,
                            workers: parseInt(workers),
                            benchmark: mode === 'benchmark'
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Update performance chart
                    performanceChart.data.datasets[0].data = [
                        result.security_result.processing_time_ms,
                        result.parallel_result.processing_time_ms,
                        result.reactive_result.processing_time_ms,
                        result.total_processing_time * 1000
                    ];
                    performanceChart.update();
                    
                    // Display detailed results
                    document.getElementById('results').innerHTML = `
🎯 RÉSULTATS ILN AVANCÉS
${'='.repeat(50)}

📊 MÉTRIQUES GLOBALES:
   Status: ${result.status}
   Mode: ${result.processing_mode}
   Temps total: ${result.total_processing_time.toFixed(3)}s
   Capacités utilisées: ${result.capabilities_used.join(', ')}

🦀 SÉCURITÉ RUST:
   Engine: ${result.security_result.engine}
   Hash: ${result.security_result.secure_hash}
   Temps: ${result.security_result.processing_time_ms}ms

🐹 PARALLÉLISME GO:
   Engine: ${result.parallel_result.engine}
   Workers: ${result.parallel_result.worker_count}
   Temps: ${result.parallel_result.processing_time_ms}ms

⚡ RÉACTIVITÉ JS-STYLE:
   Engine: ${result.reactive_result.engine}
   Score: ${result.reactive_result.reactivity_score}
   Event ID: ${result.reactive_result.event_id}

🖥️ MÉTRIQUES SYSTÈME:
   Memory: ${result.system_metrics.memory_usage_mb} MB
   CPU: ${result.system_metrics.cpu_percent}%
   Threads: ${result.system_metrics.threads}
                    `;
                    
                } catch (error) {
                    document.getElementById('results').innerHTML = `❌ Error: ${error.message}`;
                }
            }
            
            async function runBenchmarkSuite() {
                document.getElementById('results').innerHTML = '🏁 Running comprehensive benchmark suite...';
                
                const tests = [
                    {name: 'Secure Processing', mode: 'secure'},
                    {name: 'Fast Parallel', mode: 'fast'},
                    {name: 'Reactive Events', mode: 'reactive'},
                    {name: 'Balanced Load', mode: 'balanced'}
                ];
                
                let benchmarkResults = '🏁 BENCHMARK SUITE RESULTS\n' + '='.repeat(50) + '\n\n';
                
                for (const test of tests) {
                    try {
                        const response = await fetch('/process-advanced', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                data: 'Benchmark test data for ' + test.name,
                                processing_mode: test.mode,
                                workers: 4,
                                benchmark: true
                            })
                        });
                        
                        const result = await response.json();
                        
                        benchmarkResults += `📋 ${test.name.toUpperCase()}\n`;
                        benchmarkResults += `   Total Time: ${(result.total_processing_time * 1000).toFixed(2)}ms\n`;
                        benchmarkResults += `   Rust: ${result.security_result.processing_time_ms}ms (${result.security_result.engine})\n`;
                        benchmarkResults += `   Go: ${result.parallel_result.processing_time_ms}ms (${result.parallel_result.engine})\n`;
                        benchmarkResults += `   JS-style: ${result.reactive_result.processing_time_ms}ms (${result.reactive_result.engine})\n`;
                        benchmarkResults += `   Memory: ${result.system_metrics.memory_usage_mb} MB\n\n`;
                        
                    } catch (error) {
                        benchmarkResults += `❌ ${test.name}: Error - ${error.message}\n\n`;
                    }
                }
                
                document.getElementById('results').innerHTML = benchmarkResults;
            }
            
            function startRealtimeMonitoring() {
                if (monitoringInterval) {
                    clearInterval(monitoringInterval);
                    monitoringInterval = null;
                    return;
                }
                
                monitoringInterval = setInterval(async () => {
                    try {
                        await loadMetrics();
                    } catch (error) {
                        console.error('Monitoring error:', error);
                    }
                }, 2000);
            }
        </script>
    </body>
    </html>
    """)

@app.get("/capabilities")
async def get_capabilities():
    """Retourne les capacités détectées du système"""
    return {
        "capabilities": iln_engine.capabilities,
        "architecture": "Progressive Multi-Language",
        "fallback_strategy": "Intelligent degradation",
        "container_type": "Docker optimized"
    }

@app.get("/metrics")
async def get_metrics():
    """Métriques système en temps réel"""
    return iln_engine.get_system_metrics()

@app.post("/process-advanced", response_model=ILNProcessingResult)
async def process_advanced(request: ILNProcessingRequest):
    """Traitement avancé utilisant toutes les essences ILN disponibles"""
    start_time = time.time()
    
    # Incrémenter le compteur de requêtes
    iln_engine.performance_metrics["requests_processed"] += 1
    
    # Traitement selon le mode
    if request.processing_mode == "secure":
        # Priorité sécurité Rust
        security_result = iln_engine.own_secure(request.data, "secure")
        parallel_result = iln_engine.chan_parallel(request.data, 2)  # Minimal
        reactive_result = iln_engine.event_reactive(request.data, "secure_event")
        capabilities_used = ["rust", "python"]
        
    elif request.processing_mode == "fast":
        # Priorité performance Go  
        security_result = iln_engine.own_secure(request.data, "fast")
        parallel_result = iln_engine.chan_parallel(request.data, request.workers)
        reactive_result = iln_engine.event_reactive(request.data, "fast_event")
        capabilities_used = ["go", "python"]
        
    elif request.processing_mode == "reactive":
        # Priorité réactivité événementielle
        security_result = iln_engine.own_secure(request.data, "reactive")
        parallel_result = iln_engine.chan_parallel(request.data, 2)
        reactive_result = iln_engine.event_reactive(request.data, "reactive_event")
        capabilities_used = ["javascript", "python"]
        
    elif request.processing_mode == "benchmark":
        # Test complet de tous les engines
        security_result = iln_engine.own_secure(request.data, "benchmark")
        parallel_result = iln_engine.chan_parallel(request.data, request.workers)
        reactive_result = iln_engine.event_reactive(request.data, "benchmark_event")
        capabilities_used = ["rust", "go", "javascript", "python"]
        
    else:  # balanced
        # Utilisation équilibrée de toutes les essences
        security_result = iln_engine.own_secure(request.data, "balanced")
        parallel_result = iln_engine.chan_parallel(request.data, request.workers)
        reactive_result = iln_engine.event_reactive(request.data, "balanced_event")
        capabilities_used = ["rust", "go", "javascript", "python"]
    
    total_time = time.time() - start_time
    
    # Mise à jour des métriques
    iln_engine.performance_metrics["average_response_time"] = (
        (iln_engine.performance_metrics["average_response_time"] * 
         (iln_engine.performance_metrics["requests_processed"] - 1) + total_time) /
        iln_engine.performance_metrics["requests_processed"]
    )
    
    return ILNProcessingResult(
        status="success",
        original_data=request.data[:100] + "..." if len(request.data) > 100 else request.data,
        security_result=security_result,
        parallel_result=parallel_result,
        reactive_result=reactive_result,
        processing_mode=request.processing_mode,
        total_processing_time=total_time,
        system_metrics=iln_engine.get_system_metrics(),
        capabilities_used=capabilities_used,
        timestamp=datetime.now()
    )

@app.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket):
    """WebSocket pour monitoring temps réel"""
    await websocket.accept()
    
    try:
        while True:
            metrics = iln_engine.get_system_metrics()
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print("Monitoring WebSocket disconnected")

@app.get("/health")
async def health_check():
    """Health check avancé avec détails système"""
    return {
        "status": "healthy",
        "architecture": "ILN Advanced Multi-Language",
        "capabilities": iln_engine.capabilities,
        "performance": iln_engine.performance_metrics,
        "system_metrics": iln_engine.get_system_metrics(),
        "docker_optimized": True
    }

@app.get("/stress-test/{iterations}")
async def stress_test(iterations: int):
    """Test de stress pour mesurer les performances sous charge"""
    if iterations > 100:
        raise HTTPException(status_code=400, detail="Max 100 iterations pour éviter la surcharge")
    
    results = []
    test_data = "Stress test data " * 50  # ~1KB de données
    
    start_time = time.time()
    
    for i in range(iterations):
        iteration_start = time.time()
        
        # Test de toutes les essences
        security = iln_engine.own_secure(f"{test_data}_{i}")
        parallel = iln_engine.chan_parallel(f"{test_data}_{i}", 4)
        reactive = iln_engine.event_reactive(f"{test_data}_{i}")
        
        iteration_time = time.time() - iteration_start
        results.append({
            "iteration": i + 1,
            "time": iteration_time,
            "security_engine": security["engine"],
            "parallel_engine": parallel["engine"],
            "reactive_engine": reactive["engine"]
        })
    
    total_time = time.time() - start_time
    
    return {
        "status": "completed",
        "iterations": iterations,
        "total_time": total_time,
        "average_time_per_iteration": total_time / iterations,
        "requests_per_second": iterations / total_time,
        "capabilities": iln_engine.capabilities,
        "final_metrics": iln_engine.get_system_metrics(),
        "sample_results": results[:5]  # Premiers 5 résultats comme échantillon
    }

if __name__ == "__main__":
    print("🌌 Starting ILN Advanced Multi-Language Engine")
    print("🧪 Progressive architecture with intelligent fallbacks")
    print("🦀 Rust + 🐹 Go + 🐍 Python integration")
    
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )