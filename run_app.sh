#!/bin/bash
unset PYTHONPATH
export PYTHONNOUSERSITE=True

# Activate the virtual environment
source .venv/bin/activate

cd flask_app

# Run the Flask app
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py --port=5050
