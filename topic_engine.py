import re
import sys
import json
import nltk
import operator
import argparse
import numpy as np
import pandas as pd
from gensim import corpora
from bs4 import BeautifulSoup
from nltk.stem.porter import *
from collections import defaultdict
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from gensim.models import TfidfModel, LdaMulticore
from gensim.models.coherencemodel import CoherenceModel
from nltk.stem import WordNetLemmatizer, SnowballStemmer

nltk.download('wordnet')

class Topic_Engine(object):
    """
    Instantiate Topic_Engine.

    Parameters:
    -----------------------

    Returns:
    -----------------------
    """

    def __init__(self, filename):
        self.filename = filename
        self.json = json.load(self.filename)
        self.run_assertions()
        self.data = pd.read_csv(self.json['data'], encoding='latin1')
        self.corpus = self.preprocess(self.data[self.json['docs']])
        self.dictionary, self.corpuses = self.set_dictionary(self.corpus)
        self.models = defaultdict(dict)
        self.best_model = None
        self.audit = None


    def run_assertions(self):
        assert self.json['num_topics'] == tuple and len(self.json['num_topics']) == 3, 'Update num_topics, e.g. 1,6,2'
        assert self.json['num_passes'] == tuple and len(self.json['num_passes']) == 3, 'Update num_passes, e.g. 2,8,4'
        assert type(self.json['corpus_type']) == list, 'Corpus_type must be a list "[ ]"'

    def preprocess(self, data):
        """
        Return lemmatized, stemmed and tokenized text from corpus.

        Assumed data size == one document. # check syntax on in function assertions.

        Parameters:
        ----------
        self.data - pandas dataframe
        self.json['docs'] -- 'text' field in self.data

        Returns:
        -------
        numpy array: corpus of tokens per document
        """

        def html_ascii(doc):
            """Clean HTML out of text and remove all non alphanumerics."""

            ndoc = BeautifulSoup(doc, "html.parser").text
            ndoc = re.sub('[^a-zA-Z]+', ' ', ndoc.lower())
            return ndoc

        def lemmatize_stemming(text):
            """Return text - Stemmed and Lemmatized (Verbs)."""

            stemmer = SnowballStemmer("english")
            return stemmer.stem(WordNetLemmatizer().lemmatize(text, pos='v'))

        def tokenize(text):
            """Tokenize all text greater than 3 characters and remove stopwords."""

            tokens = []
            for token in simple_preprocess(text):
                if token not in STOPWORDS and len(token) >= self.json['min_token_length']:
                    tokens.append(lemmatize_stemming(text))
            return tokens

        docs_srs = data
        assert type(docs_srs) == pd.Series(), 'Data not in pandas Series.'

        cleaned_docs = docs_srs.apply(html_ascii)
        return cleaned_docs.apply(tokenize).values

    def set_dictionary(self, corpus): #want to edit **args of .filter_extremes() with self.json.
        """
        Build dictionary and bag of words corpus.

        Parameters:
        ----------
        _tokens : preprocessed tokens

        Returns:
        -------
        dictionary : Gensim dictionary w/ extremes filtered
        """
        corpuses = defaultdict(dict())
        dictionary = corpora.Dictionary(corpus)
        dictionary.filter_extremes()
        corpuses['BOW_corpus'] = [dictionary.doc2bow(i) for i in corpus]
        tfidf_model = TfidfModel(corpus)
        corpuses['tfidf_corpus'] = tfidf_model[corpus]
        return dictionary, corpuses

    def get_coherence_values(self):
        """
        Compute c_v coherence for various number of topics

        Parameters:
        ----------
        dictionary : Gensim dictionary
        corpus : Gensim corpus
        texts : List of input texts
        limit : Max num of topics

        Returns:
        -------
        model_list : List of LDA topic models
        coherence_values : Coherence values corresponding to the LDA model with respective number of topics
        """
        for i in range(*self.json['num_topics']): # i = topic number
            for j in range(*self.json['num_passes']):  # j = pass number
                for corpus_type in self.corpuses['corpus_type']:
                    sys.stdout.write('\r Building model: topic # {} - pass # {} - {} corpus'.format(i, j, corpus_type))
                    model = LdaMulticore(corpus=corpus_type, id2word=self.dictionary, num_topics=i, passes=j)
                    self.models['model'][(i, j)] = model
                    self.models['c_v'][(i, j)] = CoherenceModel(model=model, texts=corpus_type,
                                                                dictionary=self.dictionary, coherence='c_v')

    def get_max_cv_model(self):
        max_model = max(self.models['c_v'].items(), key=operator.itemgetter(1))[0]
        self.best_model = {max_model: self.models['models'][max_model]}

    def set_engine(self):
        self.get_coherence_values()
        self.get_max_cv_model()

    def get_audit(self): # to flesh out
        file_dir = '/'.join(self.filename.split('/')[:-1])
        file = file_dir + '/topic_engine_audit_trail.txt'

    def run_test(self, input_corpus, input_model, doc):
        model = input_model
        corpus = input_corpus
        if doc is None:
            doc = np.random.randint(len(corpus), size=5)
            for idx, score in sorted(model[corpus[doc]], key=lambda tup: -1 * tup[1]):
                print("\nScore: {}\t \nTopic: {}".format(score, model.print_topic(idx, 10)))
        if type(doc) == str:
            tokens = self.preprocess(doc)
            for idx, score in sorted(model[tokens], key=lambda tup: -1 * tup[1]):
                print("\nScore: {}\t \nTopic: {}".format(score, model.print_topic(idx, 10)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Topic Modeling.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--file', type=str, action='store',
                        help='Filename ')
    parser.add_argument('--test_doc', type=str, action='store', default=None,
                        help='Enter sample document.')
    args = parser.parse_args()

    engine = Topic_Engine(args.file)
    engine.set_engine()
    engine.run_test(engine.corpuses['tfidf_corpus'], list(engine.best_model.values())[0], args.test_doc)
    engine.get_audit()