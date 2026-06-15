import logging

def setup_logging(mode="PROD"):
    log_level = logging.DEBUG if mode == "DEV" else logging.INFO

    logging.basicConfig(
        filename="app.log",
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )