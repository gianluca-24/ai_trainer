# Create directories
mkdir -p app/core
mkdir -p app/services
mkdir -p app/ui

# Create __init__.py files
touch app/__init__.py
touch app/core/__init__.py
touch app/services/__init__.py
touch app/ui/__init__.py

# Create Python module files
touch app/core/pose_tracker.py
touch app/services/stream_processor.py
touch app/ui/streamlit_ui.py

# Create project-level files
touch main.py
touch requirements.txt
touch README.md