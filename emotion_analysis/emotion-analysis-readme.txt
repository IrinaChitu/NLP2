main methods (all declared in emotion_analysis/emotion_analysis.py)


1. analysis of lyrics only
   - call:
        def analyze_new_lyrics(
            lyrics, 
            lexicon_processing_dir = 'emotion_analysis/lexicon_processing/nrc_emolex_v0.92'
        )
   - result:
        dict {
            emotion: {
                percentage: ... --> the dict is sorted by this value (decreasing)
                word_occur: ... -> list of words and their number or occurrences
            }
        }


2. analysis of a song from the dataset (identified by artist and song title)
   - call:
        def analyze_existing_song(
            artist,
            song_title, 
            lexicon_processing_dir = 'emotion_analysis/lexicon_processing/nrc_emolex_v0.92',
            dataset_csv =  'data/dataset.csv'
            )
    - result:
        same as 1.


3. analysis of an artist from the dataset
   - call:
        def analyze_artist(
            artist, 
            lexicon_processing_dir = 'emotion_analysis/lexicon_processing/nrc_emolex_v0.92',
            dataset_csv =  'data/dataset.csv'
            )
    - result:
        dict {
            emotion: {
                percentage: ... --> the dict is sorted by this value (decreasing)
            }
        }
