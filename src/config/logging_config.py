import logging
import sys

def configure_logging(
    level=logging.DEBUG,
    log_to_file=False,
    logfile="app.log"
):
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_to_file:
        handlers.append(logging.FileHandler(logfile))

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(process)d | %(name)s | %(levelname)s | %(message)s",
        handlers=handlers,
        force=True,   # 🔥 overrides Streamlit / libs
    )
