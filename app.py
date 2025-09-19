#!/usr/bin/env python3
"""
ILN Simple Application
Architecture : app.py (logique) + Dockerfile (dépendances)
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests

# Configuration
app = FastAPI(
    title="ILN Simple Demo",
    description="Architecture simplifiée : Dockerfile gère les dépendances",
    version="1.0.0"
)

# Modèles
class ProcessRequest(BaseModel):
    text: str
    mode: str = "simple"

class ProcessResponse(BaseModel):
    original_text: str
    processed_text: str
    word_count: int
    mode: str
    timestamp: str
    architecture: str

# Routes
@app.get("/")
async def home():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ILN Simple Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            input, textarea, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
        </style>
    </head>
    <body>
        <h1>ILN Simple Demo</h1>
        <p><strong>Architecture:</strong> app.py + Dockerfile (sans requirements.txt)</p>
        
        <div class="container">
            <h3>Test de Traitement</h3>
            <textarea id="text" placeholder="Entrez votre texte ici..." rows="4">Ceci est un test de l'architecture ILN simplifiée avec Docker qui gère toutes les dépendances.</textarea>
            
            <select id="mode">
                <option value="simple">Simple</option>
                <option value="advanced">Advanced</option>
            </select>
            
            <button onclick="processText()">Traiter</button>
        </div>
        
        <div class="container">
            <h3>Résultat</h3>
            <div id="result" style="background: white; padding: 15px; border-radius: 4px; min-height: 100px;">
                Cliquez sur "Traiter" pour voir le résultat...
            </div>
        </div>

        <script>
            async function processText() {
                const text = document.getElementById('text').value;
                const mode = document.getElementById('mode').value;
                
                document.getElementById('result').innerHTML = 'Traitement en cours...';
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: text, mode: mode})
                    });
                    
                    const result = await response.json();
                    
                    document.getElementById('result').innerHTML = `
                        <h4>Résultat du traitement</h4>
                        <p><strong>Mode:</strong> ${result.mode}</p>
                        <p><strong>Texte original:</strong> ${result.original_text}</p>
                        <p><strong>Texte traité:</strong> ${result.processed_text}</p>
                        <p><strong>Nombre de mots:</strong> ${result.word_count}</p>
                        <p><strong>Architecture:</strong> ${result.architecture}</p>
                        <p><strong>Timestamp:</strong> ${result.timestamp}</p>
                    `;
                    
                } catch (error) {
                    document.getElementById('result').innerHTML = `Erreur: ${error.message}`;
                }
            }
        </script>
    </body>
    </html>
    """)

@app.post("/process", response_model=ProcessResponse)
async def process_text(request: ProcessRequest):
    """Traite le texte selon le mode choisi"""
    
    if request.mode == "simple":
        processed_text = request.text.upper()
    elif request.mode == "advanced":
        # Simulation d'un traitement plus complexe
        words = request.text.split()
        processed_text = " ".join([f"{word}({len(word)})" for word in words])
    else:
        raise HTTPException(status_code=400, detail="Mode invalide")
    
    return ProcessResponse(
        original_text=request.text[:100] + "..." if len(request.text) > 100 else request.text,
        processed_text=processed_text[:100] + "..." if len(processed_text) > 100 else processed_text,
        word_count=len(request.text.split()),
        mode=request.mode,
        timestamp=datetime.now().isoformat(),
        architecture="app.py + Dockerfile (sans requirements.txt)"
    )

@app.get("/health")
async def health_check():
    """Health check simple"""
    return {
        "status": "healthy",
        "architecture": "ILN Simple",
        "files": ["app.py", "Dockerfile"],
        "dependencies_managed_by": "Docker",
        "requirements_txt": "Not needed!"
    }

@app.get("/api-test")
async def api_test():
    """Test des capacités réseau"""
    try:
        # Test d'appel API externe
        response = requests.get("https://httpbin.org/json", timeout=5)
        return {
            "status": "success",
            "message": "Les dépendances réseau fonctionnent",
            "external_api_response": response.json(),
            "proof": "requests library works perfectly"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Démarrage de l'application ILN Simple sur le port {port}")
    print("Architecture: app.py (logique) + Dockerfile (dépendances)")
    uvicorn.run("app:app", host="0.0.0.0", port=port)