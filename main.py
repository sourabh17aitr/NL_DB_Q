import logging
import subprocess
import os
import sys

from posthog import project_root

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def run_streamlit():
    streamlit_file = os.path.join(os.path.dirname(__file__), "src", "ui", "streamlit_app.py")
    subprocess.run(["streamlit", "run", streamlit_file])



if __name__ == "__main__":
    setup_logging()
    # start application
    run_streamlit()
