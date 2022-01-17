from flask import Flask, request

app = Flask(__name__)


@app.route("/predict", methods=["POST"])
def predict():
    print(request.form)
    return request.form


if __name__ == "__main__":
    app.run(debug=False)
