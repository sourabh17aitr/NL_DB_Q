import logging
import subprocess
import os


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def run_streamlit():
    streamlit_file = os.path.join(os.path.dirname(__file__), "src", "ui", "app.py")
    subprocess.run(["streamlit", "run", streamlit_file])



if __name__ == "__main__":
    setup_logging()
    proc = run_streamlit()
    