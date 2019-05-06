from flask import Flask
from proj import get_model

application = Flask(__name__)


@application.route("/api/v1/model", methods=["GET"])
def get_model():  # Ignore PyDocStyleBear
    model = get_model()
    return model.predict([])


if __name__ == "__main__":
    application.run(port=8080)
