from flask import Flask, jsonify
import math
import re

from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


def load_vocab():
    vocab = {}
    with open("vocab.txt", "r", encoding="utf-8") as f:
        vocab_terms = f.readlines()
    with open("idf-values.txt", "r", encoding="utf-8") as f:
        idf_values = f.readlines()
    for (term, idf_value) in zip(vocab_terms, idf_values):
        vocab[term.rstrip()] = int(idf_value.rstrip())
    return vocab


def load_document():
    with open("document.txt", "r", encoding="utf-8") as f:
        documents = f.readlines()
    return documents


def load_inverted_index():
    inverted_index = {}
    with open('inverted-index.txt', 'r', encoding='latin-1') as f:
        inverted_index_terms = f.readlines()
    for row_num in range(0, len(inverted_index_terms), 2):
        term = inverted_index_terms[row_num].strip()
        documents = inverted_index_terms[row_num+1].strip().split()
        inverted_index[term] = documents
    return inverted_index


def load_link_of_qs():
    with open("lc_problems.txt", "r", encoding="utf-8") as f:
        links = f.readlines()
    return links


vocab = load_vocab()            # vocab : idf_values
document = load_document()
inverted_index = load_inverted_index()
Qlink = load_link_of_qs()


def get_tf_dict(term):
    tf_dict = {}
    if term in inverted_index:
        for doc in inverted_index[term]:
            if doc not in tf_dict:
                tf_dict[doc] = 1
            else:
                tf_dict[doc] += 1

    for doc in tf_dict:
        # dividing the freq of the word in doc with the total no of words in doc indexed document
        try:
            tf_dict[doc] /= len(document[int(doc)])
        except (ZeroDivisionError, ValueError, IndexError) as e:
            print(e)
            print(doc)

    return tf_dict


def get_idf_value(term):
    return math.log((1 + len(document)) / (1 + vocab[term]))


def calc_docs_sorted_order(q_terms):
    # will store the doc which can be our ans: sum of tf-idf value of that doc for all the query terms
    potential_docs = {}
    ans = []
    for term in q_terms:
        if (term not in vocab):
            continue

        tf_vals_by_docs = get_tf_dict(term)
        idf_value = get_idf_value(term)

        for doc in tf_vals_by_docs:
            if doc not in potential_docs:
                potential_docs[doc] = tf_vals_by_docs[doc]*idf_value
            else:
                potential_docs[doc] += tf_vals_by_docs[doc]*idf_value

        # print(potential_docs)
        # divide the scores of each doc with no of query terms
        for doc in potential_docs:
            potential_docs[doc] /= len(q_terms)

        # sort in dec order acc to values calculated
        potential_docs = dict(
            sorted(potential_docs.items(), key=lambda item: item[1], reverse=True))

        # if no doc found
        if (len(potential_docs) == 0):
            print("No matching question found. Please search with more relevant terms.")

        for doc_index in potential_docs:
            ans.append({"Question Link": Qlink[int(
                doc_index) - 1][:-2], "Score": potential_docs[doc_index]})
    return ans


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
# query = input('Enter your query: ')
# q_terms = [term.lower() for term in query.strip().split()]

# print(q_terms)
# print(calc_docs_sorted_order(q_terms)[0])
# print(len(calc_docs_sorted_order(q_terms)))


class SearchForm(FlaskForm):
    search = StringField('Enter your search term')
    submit = SubmitField('Search')


@app.route("/<query>")
def return_links(query):
    q_terms = [term.lower() for term in query.strip().split()]
    return jsonify(calc_docs_sorted_order(q_terms)[:20:])


@app.route("/", methods=['GET', 'POST'])
def home():
    form = SearchForm()
    results = []
    if form.validate_on_submit():
        query = form.search.data
        q_terms = [term.lower() for term in query.strip().split()]
        results = calc_docs_sorted_order(q_terms)[:20:]
    return render_template('index.html', form=form, results=results)
