#!/bin/bash

# Configuration for local n8n isolated to the current folder
export N8N_USER_FOLDER="$(pwd)/.n8n"
export N8N_CUSTOM_EXTENSIONS="$(pwd)/custom_nodes"
export N8N_PORT=5678

# Allow n8n Code nodes to use Node.js built-in modules (like child_process)
export NODE_FUNCTION_ALLOW_BUILTIN=*

# Ensure OLLAMA can be reached from n8n (if using local Ollama model)
# If Ollama is running on localhost:11434, n8n running locally can reach it directly.
export OLLAMA_HOST="http://localhost:11434"

echo "=========================================="
echo "🚀 Starting n8n locally for Agent5001"
echo "📁 Data folder: $N8N_USER_FOLDER"
echo "🌐 UI Available at: http://localhost:$N8N_PORT"
echo "=========================================="

npx n8n@latest
