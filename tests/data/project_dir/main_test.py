from flask import Flask
from proj import get_model

application = Flask(__name__)


@application.route("/api/v1/model", methods=["GET"])  # noqa: F811
def get_model_prediction():  # noqa: F811
    model = get_model()
    return model.predict([])


if __name__ == "__main__":
    application.run(port=8080)
