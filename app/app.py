from flask import Flask, request
from model.emotion_analysis import (
    analyze_new_lyrics,
    analyze_existing_song,
    analyze_artist,
)

app = Flask(__name__)


@app.route("/sentiment", methods=["POST"])
def predict():
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


if __name__ == "__main__":
    app.run(debug=False)
