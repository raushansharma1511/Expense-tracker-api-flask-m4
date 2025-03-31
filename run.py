from app import create_app
import logging


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["FLASK_DEBUG"])
    # app.run(host="0.0.0.0", port=9000, debug=True)
