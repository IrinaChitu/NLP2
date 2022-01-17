import argparse
import csv
import os
import random as rnd
import re
import sys
from string import punctuation

import nltk
import numpy as np
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from tqdm import tqdm
from unidecode import unidecode



"""
WORD PROCESSING

- data cleanup -- any unusual characters (accents, asian letters, unusual punctuation etc) are "decoded" using unidecode 
- pos-tagging of the song content (title + lyrics)
- each word is lemmatized (only adjectives, nouns, adverbs and verbs -- other pos are kept as-is)

* same process for the words in the lexicon
* 
"""

def nltk_setup():
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')


def tag_mapping(tag):
    '''
    receives a tag obtained with nltk.pos_tag (trained with treebank corpus)
    returns the pos mapping which can be used by wordnet (lemmatizer)
    '''
    if tag.startswith('J'):   #adjectives
      return wn.ADJ
    elif tag.startswith('N'): #nouns
      return wn.NOUN
    elif tag.startswith('R'): #adverbs
      return wn.ADV
    elif tag.startswith('V'): #verbs
      return wn.VERB
    return None



########################################################################################################################
################################################## LEXICON PROCESSING ##################################################
########################################################################################################################


# valid_emotions = ['fear', 'anger', 'anticipation', 'trust', 'surprise', 'sadness', 'disgust', 'joy']
def clean_emotion(emotion):
    if emotion == 'anticip':
        return 'anticipation'
    return emotion


def clean_lexicon_phrase(phrase):
    content = unidecode(phrase)
    content = content.replace('_x000D_', ' ')
    content = re.sub('[0-9]*', '', content)
    for sign in punctuation:
        content = content.replace(sign, ' ')
    content = ' '.join(content.split())
    content = content.lower()
    return content.split()


def lemmatize_phrase(lemmatizer, phrase_words):
    pos_tagged_phrase = nltk.pos_tag(phrase_words)
    new_phrase = []
    for word, pos in pos_tagged_phrase:
        tag = tag_mapping(pos)
        if tag is None:
            new_phrase.append(word)
            continue
        new_phrase.append(lemmatizer.lemmatize(word, tag))
    return new_phrase




class Emotion_Lexicon():
    '''
    - this lexicon features only single words, not phrases;
    - the data is organised in a dictionary with words as keys and lists of their associated emotions as values
    '''
    def __init__(self, valid_emotions = ['fear', 'anger', 'anticipation', 'trust', 'surprise', 'sadness', 'disgust', 'joy'], lemmatization = True):
        nltk_setup()
        self.lemmatizer = WordNetLemmatizer()
        self.lexic = {}
        self.valid_emotions = valid_emotions
        self.lemmatization = lemmatization

    def add_association(self, phrase, emotion):
        emotion = clean_emotion(emotion)
        assert emotion in self.valid_emotions, 'Encountered an invalid emotion -- {}'.format(emotion)
        phrase_words = clean_lexicon_phrase(phrase)
        if self.lemmatization:
            phrase_words = lemmatize_phrase(self.lemmatizer, phrase_words)
        phrase_len = len(phrase_words)
        phrase = ' '.join(phrase_words)
        if phrase_len not in self.lexic.keys():
            self.lexic[phrase_len] = {}
            self.lexic[phrase_len][phrase] = [emotion]
        elif phrase not in self.lexic[phrase_len]:
            self.lexic[phrase_len][phrase] = [emotion]
        elif emotion not in self.lexic[phrase_len][phrase]:
            self.lexic[phrase_len][phrase].append(emotion)
    
    def get_word_association(self, phrase):
        phrase_len = len(phrase.split())
        if phrase not in self.lexic[phrase_len]:
            return None
        return self.lexic[phrase_len][phrase]

    def get_vocabulary(self):
        vocab = {}
        for phrase_len in self.lexic.keys():
            vocab[phrase_len] = list(self.lexic[phrase_len].keys())
        return vocab

    def get_possible_phrase_lengths(self):
        phrase_lengths = sorted(list(self.lexic.keys()), reverse = True)
        return phrase_lengths

    def __len__(self):
        lexicon_entries = 0
        for phrase_len in self.lexic.keys():
            lexicon_entries += len(self.lexic[phrase_len])
        return lexicon_entries

    def export_processed_lexicon_to_file(self, processed_lexicon_fpath):
        with open(processed_lexicon_fpath, 'w') as f:
            for phrase_len in self.get_possible_phrase_lengths():
                for word, associations in self.lexic[phrase_len].items():
                    f.write(str(phrase_len) + ' -- ' + word + ' -- ' + ', '.join(associations) + '\n')

    def import_processed_lexicon_from_file(self, processed_lexicon_fpath):
        with open(processed_lexicon_fpath) as f:
            lexicon_entries = f.read().splitlines()
        for entry in lexicon_entries:
            phrase_length, word, associations = entry.split(' -- ')
            phrase_length = int(phrase_length)
            if phrase_length not in self.lexic:
                self.lexic[phrase_length] = {}
            if word not in self.lexic[phrase_length]:
                self.lexic[phrase_length][word] = []
            for assoc in associations.split(', '):
                self.lexic[phrase_length][word].append(assoc)



def load_emolex_at_word_level(emolex_word_file, emotion_lexicon, positivity_lexicon = None):
    with open(emolex_word_file) as f:
        all_word_entries = f.read().splitlines()

    for entry in tqdm(all_word_entries, desc = 'processing lexicon entries (word)', ncols = 100):
        word, association, score = entry.split('\t')
        if int(score) == 0:
            continue # if the value is 0, there is no association at the current row
        if re.fullmatch('[a-zA-Z]*', word) is None:
            # print(word)
            continue
        if association in ['positive', 'negative']:
            # positivity_lexicon.add_association(word, association)
            pass
        else:
            emotion_lexicon.add_association(word, association)
    

def load_emolex_at_sense_level(emolex_sense_file, emotion_lexicon, positivity_lexicon = None):
    with open(emolex_sense_file) as f:
        all_sense_entries = f.read().splitlines()
    
    for entry in tqdm(all_sense_entries, desc = 'processing lexicon entries (sense)', ncols = 100):
        sense, association, score = entry.split('\t')
        if int(score) == 0:
            continue # if the value is 0, there is no association at the current row
        base_word, synonyms = sense.split('--')
        # words = [base_word] + synonyms.split(', ')
        words = [base_word]
        for word in words:
            # if re.fullmatch('[a-zA-Z]*', word) is None:
            #     # print(word)
            #     continue
            if association in ['positive', 'negative']:
                # positivity_lexicon.add_association(word, association)
                pass
            else:
                emotion_lexicon.add_association(word, association)


def build_emotion_lexicon(emolex_files_dir = './emotion_analysis/lexicon_processing/nrc_emolex_v0.92', show_progress = False, lemmatization = True):

    emolex_word_file = os.path.join(emolex_files_dir, 'NRC-Emotion-Lexicon-Wordlevel-v0.92.txt')
    emolex_sense_file = os.path.join(emolex_files_dir, 'NRC-Emotion-Lexicon-Senselevel-v0.92.txt')

    assert os.path.exists(emolex_word_file), 'The emolex directory does not contain the lexicon at word level -- {}'.format(os.path.basename(emolex_word_file))
    assert os.path.exists(emolex_sense_file), 'The emolex directory does not contain the lexicon at sense level -- {}'.format(os.path.basename(emolex_sense_file))
        
    lexicon = Emotion_Lexicon(lemmatization = lemmatization)

    processed_lexicon_fpath = os.path.join(emolex_files_dir, 'Processed-EmoLex.txt')
    if not os.path.exists(processed_lexicon_fpath):
        load_emolex_at_word_level(emolex_word_file, lexicon)
        if show_progress:
            print('the lexicon size after processing at word level:', len(lexicon))
        load_emolex_at_sense_level(emolex_sense_file, lexicon)
        if show_progress:
            print('the lexicon size after processing at sense level:', len(lexicon))
        lexicon.export_processed_lexicon_to_file(processed_lexicon_fpath)
    else:
        lexicon.import_processed_lexicon_from_file(processed_lexicon_fpath)
        
        

    return lexicon



########################################################################################################################
#################################################### SONG PROCESSING ###################################################
########################################################################################################################


class Song():
    def __init__(self, csv_row, header = None):
        self.lemmatizer = WordNetLemmatizer()
        self.data = {}
        for attribute, value in zip(header, csv_row):
            self.data[attribute] = value
    
    def __str__(self):
        return str(self.data)
    
    def process_content(self, lemmatization = True):
        content = self.data['song'] + '. ' + self.data['lyrics']
        content = unidecode(content)
        content = content.replace('_x000D_', ' ')
        content = re.sub('[0-9]*', '', content)
        for sign in punctuation:
            content = content.replace(sign, ' ')
        content = ' '.join(content.split())
        content = content.lower()
        content_words = content.split()
        if lemmatization:
            self.content = lemmatize_phrase(self.lemmatizer, content_words)
        else:
            self.content = content.split()
    


class Lyrics_Dataset():
    def __init__(self, csv_file = './data/dataset.csv'):
        header, data = self.read_csv(csv_file)
        self.songs = []
        for row in data:
            song = Song(row, header)
            self.songs.append(song)

    def read_csv(self, csv_file):
        all_rows = []
        with open(csv_file) as csv_f:
            csv_r = csv.reader(csv_f)
            has_header = True
            for row in csv_r:
                if has_header:
                    header = row
                    has_header = False
                    continue
                all_rows.append(row)
        return header, all_rows

    def __getitem__(self, idx):
        return self.songs[idx]
    
    def __len__(self):
        return len(self.songs)

    def get_song(self, artist, title):
        artist_found = False
        songs_of_this_artist = []
        for song in self.songs:
            if song.data['artist'] == artist:
                artist_found = True
                if song.data['song'] == title:
                    return song
                songs_of_this_artist.append(song.data['song'])
        if not artist_found:
            print('was not able to find the given artist --', artist)
            return None
        print('found the artist {}, but was not able to find the given song title -- {}'.format(artist, title))
        print('showing {} songs belonging to {} from the dataset...'.format(len(songs_of_this_artist), artist))
        for song in songs_of_this_artist:
            print('\t', song)
        return None

    def get_all_songs_of_an_artist(self, artist):
        artist_found = False
        songs_of_this_artist = []
        for song in self.songs:
            if song.data['artist'] == artist:
                artist_found = True
                songs_of_this_artist.append(song)
        if not artist_found:
            print('was not able to find the given artist --', artist)
        return songs_of_this_artist

    def get_all_artists(self):
        artists = []
        for song in self.songs:
            artists.append(song.data['artist'])
        artists = [artist for artist in list(set(artists)) if artist != '']
        artists.sort()
        return artists





########################################################################################################################
################################################### EMOTION ANALYSIS  ##################################################
########################################################################################################################


LEMMATIZATION = True


class Emo_Analysis():
    def __init__(self):
        self.emolex = build_emotion_lexicon(lemmatization = LEMMATIZATION)
        self.lyrics_ds = Lyrics_Dataset()

    def analyze_song(self, artist = None, song_title = None, song = None, random = False, return_percentages = True, show_progress = True):
        if not random:
            assert (artist is not None and song_title is not None) or song is not None, 'Either provide an artist and a song title or directly provide a song object!'
            if song is None:
                song = self.lyrics_ds.get_song(artist, song_title)
        else:
            song = rnd.choice(self.lyrics_ds.songs)
        assert song is not None, 'The given artist ({}) or song title ({}) does not exist!'.format(artist, song_title)
        if show_progress:
            print('analyzing "{}", by {}'.format(song.data['song'], song.data['artist']))
            print('processing song content...')
        song.process_content(lemmatization = LEMMATIZATION)
        song_content = song.content
        # print(song_content)
        self.build_fresh_distribution()
        # consider all the possible phrase lengths within the lexicon
        # for a given seq_idx, start looking for sequences of bigger size and then gradually look for smaller ones if no matches are found
        # that means only considering the biggest possible phrase starting at the given seq_idx; don't count 'happy' if 'not happy' was found before it!
        # when a phrase is found, seq_idx = min(seq_idx + phrase_length, len(content)) --> be careful at the end, so you don't get out of bounds
        seq_idx = 0 # the position within the content at which the phrase should start
        while seq_idx < len(song_content):
            found_phrase = False
            for phrase_len in self.emolex.get_possible_phrase_lengths(): # the possible phrase lengths are already given in descending order
                song_phrase = ' '.join(song_content[seq_idx : seq_idx + phrase_len])
                if song_phrase in self.unsuccessful_phrases:
                    continue
                phrase_association = self.emolex.get_word_association(song_phrase)
                if phrase_association is not None:
                    found_phrase = True
                    for emotion in phrase_association:
                        current_score, current_phrases = self.emotion_stats[emotion]
                        self.emotion_stats[emotion] = (current_score + 1, current_phrases + [song_phrase])
                    break
                self.unsuccessful_phrases.add(song_phrase)
            if found_phrase:
                seq_idx += len(song_phrase)
            else:
                seq_idx += 1
        # for key, value in self.emotion_stats.items():
        #     print(key, '->', value[0], '->', '; '.join(value[1])) 
        if not return_percentages:
            return self.emotion_stats
        assoc_num = np.sum([p[0] for p in list(self.emotion_stats.values())])
        for key in self.emotion_stats.keys():
            current_val = self.emotion_stats[key]
            if current_val[0] > 0:
                self.emotion_stats[key] = (current_val[0] / assoc_num, current_val[1])
            else:
                self.emotion_stats[key] = (0, [])
        return self.emotion_stats

    def analyze_artist(self, artist, return_percentages = True, show_progress = True):
        if show_progress:
            print('analyzing the artist {}'.format(artist))
        songs = self.lyrics_ds.get_all_songs_of_an_artist(artist)
        assert len(songs) > 0, 'There were no songs found for the given artist ({})!'.format(artist)
        overall_emotion_stats = {}
        for emotion in self.emolex.valid_emotions:
            overall_emotion_stats[emotion] = 0
        if show_progress:
            song_iterator = tqdm(songs, desc = 'processing artist\'s songs', ncols = 100)
        else:
            song_iterator = songs
        for song in song_iterator:
            current_emotion_stats = self.analyze_song(song = song, return_percentages = False, show_progress = False)
            for emotion in self.emolex.valid_emotions:
                overall_emotion_stats[emotion] += current_emotion_stats[emotion][0]
        if not return_percentages:
            return overall_emotion_stats
        assoc_num = np.sum(list(overall_emotion_stats.values()))
        for key in overall_emotion_stats.keys():
            current_val = overall_emotion_stats[key]
            if current_val > 0:
                overall_emotion_stats[key] = current_val / assoc_num
            else:
                overall_emotion_stats[key] = 0
        return overall_emotion_stats

    def build_fresh_distribution(self):
        self.emotion_stats = {}
        for emotion in self.emolex.valid_emotions:
            self.emotion_stats[emotion] = (0, [])
        self.unsuccessful_phrases = set()




if __name__ == '__main__':

    emotion_stats_dir = './emotion_analysis/emotion_stats'

    per_song_csv = os.path.join(emotion_stats_dir, 'per_song_percentages.csv')
    per_artist_csv = os.path.join(emotion_stats_dir, 'per_artist_percentages.csv')
    lyrics_contrib_words_csv = os.path.join(emotion_stats_dir, 'emotion_words_from_lyrics.csv')
    
    emo_analyzer = Emo_Analysis()

    with open(per_song_csv, 'w') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(['artist', 'song', 'fear', 'anger', 'anticip', 'trust', 'surprise', 'sadness', 'disgust', 'joy'])
    with open(lyrics_contrib_words_csv, 'w') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(['emotion', 'word'])

    for song in tqdm(emo_analyzer.lyrics_ds.songs, ncols = 100, desc = 'analyzing all songs...'):
        stats = emo_analyzer.analyze_song(song = song, show_progress = False)
        fear_score, fear_words = stats['fear']
        anger_score, anger_words = stats['anger']
        anticip_score, anticip_words = stats['anticipation']
        trust_score, trust_words = stats['trust']
        surprise_score, surprise_words = stats['surprise']
        sadness_score, sadness_words = stats['sadness']
        disgust_score, disgust_words = stats['disgust']
        joy_score, joy_words = stats['joy']
        artist = song.data['artist']
        song_title = song.data['song']
        with open(per_song_csv, 'a') as csv_f:
            writer = csv.writer(csv_f)
            writer.writerow([
                artist, song_title, fear_score, anger_score, anticip_score, trust_score, surprise_score, sadness_score, disgust_score, joy_score
            ])
        word_emotion_pairs = []
        word_emotion_pairs += [('fear', w) for w in fear_words]
        word_emotion_pairs += [('anger', w) for w in anger_words]
        word_emotion_pairs += [('anticip', w) for w in anticip_words]
        word_emotion_pairs += [('trust', w) for w in trust_words]
        word_emotion_pairs += [('surprise', w) for w in surprise_words]
        word_emotion_pairs += [('sadness', w) for w in sadness_words]
        word_emotion_pairs += [('disgust', w) for w in disgust_words]
        word_emotion_pairs += [('joy', w) for w in joy_words]
        for emotion, word in word_emotion_pairs:
            with open(lyrics_contrib_words_csv, 'a') as csv_f:
                writer = csv.writer(csv_f)
                writer.writerow([emotion, word])


    with open(per_artist_csv, 'w') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(['artist', 'fear', 'anger', 'anticip', 'trust', 'surprise', 'sadness', 'disgust', 'joy'])

    for artist in tqdm(emo_analyzer.lyrics_ds.get_all_artists(), ncols = 100, desc = 'analyzing all artists...'):
        stats = emo_analyzer.analyze_artist(artist, show_progress = False)
        fear_score = stats['fear']
        anger_score = stats['anger']
        anticip_score = stats['anticipation']
        trust_score = stats['trust']
        surprise_score = stats['surprise']
        sadness_score = stats['sadness']
        disgust_score = stats['disgust']
        joy_score = stats['joy']
        with open(per_artist_csv, 'a') as csv_f:
            writer = csv.writer(csv_f)
            writer.writerow([
                artist, fear_score, anger_score, anticip_score, trust_score, surprise_score, sadness_score, disgust_score, joy_score
            ])


    # examples of analysis results for some artists/songs
    '''
    stats = emo_analyzer.analyze_song(random = True)
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value[0] * 100, 4)) + '%', value[1])
    print()

    stats = emo_analyzer.analyze_song("Barbra Streisand", "Love With All The Trimmings")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value[0] * 100, 4)) + '%', value[1])
    print()

    stats = emo_analyzer.analyze_song("Michael Jackson", "Dirty Diana")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value[0] * 100, 4)) + '%', value[1])
    print()


    stats = emo_analyzer.analyze_artist("Barbra Streisand")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value * 100, 4)) + '%')
    print()


    stats = emo_analyzer.analyze_artist("Metallica")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value * 100, 4)) + '%')
    print()


    stats = emo_analyzer.analyze_artist("Eminem")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value * 100, 4)) + '%')
    print()


    stats = emo_analyzer.analyze_artist("Ed Sheeran")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value * 100, 4)) + '%')
    print()


    stats = emo_analyzer.analyze_artist("Michael Jackson")
    print('visualizing emotion stats...')
    for key, value in stats.items():
        print(key.rjust(15), '->', str(round(value * 100, 4)) + '%')
    print()
    '''


