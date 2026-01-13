import logging
import subprocess
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agents.vector_store import build_schema_vector_store


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def run_ui_streamlit():
    streamlit_file = os.path.join(os.path.dirname(__file__), "src", "ui", "dashboard.py")
    subprocess.run(["streamlit", "run", streamlit_file])


if __name__ == "__main__":
    #setup_logging()
    build_schema_vector_store()
    proc = run_ui_streamlit()
    