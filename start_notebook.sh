#!/bin/bash
# Start Jupyter Lab in the correct environment

echo "🚀 Starting Jupyter Lab..."
echo "📦 Using environment: nvidia_impact_env"
echo ""

# Activate conda environment and start Jupyter
conda activate nvidia_impact_env && jupyter lab

