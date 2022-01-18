from flask import Flask, request
from model.emotion_analysis import (
    analyze_new_lyrics,
    analyze_existing_song,
    analyze_artist,
)
import pickle
import pandas as pd
from model.preprocessing import normalization

app = Flask(__name__)


@app.route("/sentiment", methods=["POST"])
def sentiment():
    if "lyrics" in request.form.keys():
        lyrics = request.form["lyrics"]
        sentiments = analyze_new_lyrics(
            lyrics,
            lexicon_processing_dir="emotion_analysis/lexicon_processing/nrc_emolex_v0.92",
        )
    elif "artist" in request.form.keys() and "song" in request.form.keys():
        artist = request.form["artist"]
        song = request.form["song"]
        sentiments = analyze_existing_song(
            artist,
            song,
            lexicon_processing_dir="emotion_analysis/lexicon_processing/nrc_emolex_v0.92",
        )
    elif "artist" in request.form.keys():
        artist = request.form["artist"]
        sentiments = analyze_artist(
            artist,
            lexicon_processing_dir="emotion_analysis/lexicon_processing/nrc_emolex_v0.92",
            dataset_csv="data/dataset.csv",
        )
    else:
        print("Invalid command")
        return None

    msg = ""
    for key, value in sentiments.items():
        msg += f"Sentiment [{key}] -> {value['percentage']}%\n"
        if "word_occur" in value.keys():
            msg += f"Word occurences: {value['word_occur']}\n"
        msg += "\n"
    return msg


@app.route("/predict", methods=["POST"])
def predict():
    if "lyrics" in request.form.keys():
        lyrics = normalization(request.form["lyrics"])
        features = tfidf_vect.transform([lyrics])
        features = pd.DataFrame(
            features.todense(), columns=tfidf_vect.get_feature_names_out()
        )
        predict = model.predict(features)
        return predict[0]
    else:
        print("Invalid command")
        return None


if __name__ == "__main__":
    global model, tfidf_vect

    with open("./app/model/random-forest.pkl", "rb") as file:
        model = pickle.load(file)

    with open("./app/model/tfidf.pkl", "rb") as file:
        tfidf_vect = pickle.load(file)

    app.run(debug=True)
