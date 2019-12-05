# NLTK
from pathlib import Path
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet


grammar = """
			NP: {<DT>?<JJ>*<NN|NNS>}
			VP: {<VBD|VBG|VBN|VBP|VBZ>?<TO>?<VB>?}
		"""
parser = nltk.RegexpParser(grammar)
lemmatizer = WordNetLemmatizer()

# Flask Application Definition
from flask import Flask, render_template, request
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)


# Get sigml for each word and store in file.
def get_sigml(gloss_list):
  with open("static/output.sigml", "w") as fo:
    fo.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    fo.write("<sigml>\n")
    for (key, value) in gloss_list:
      file_name = "sigml/"+str.lower(key)+".sigml"
      if Path(file_name).is_file():
        with app.open_resource(file_name, "r") as fi:
            lines = fi.readlines()
            for line in lines:
              fo.write(line)
    fo.write("</sigml>")
    fo.close()

app.jinja_env.globals.update(get_sigml=get_sigml)


@app.route('/')
def student():
   return render_template('student.html')

@app.route('/result',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      result = request.form   
      sentence = result["Sentence"]
      
      # Tokenizes the input sentence into words.
      tokens = word_tokenize(sentence)
      # Tags the words with their respective POS.
      tagged = nltk.pos_tag(tokens)
      
      # Parts of Speech in FSL
      fsl_pos = ["CC","CD","JJ","NN", "NNS","PRP","VB","VBD","VBG","VBN","VBP","VBZ"]
      filtered = []

      # Omit other PoS not in FSL
      for x in tagged:
      	if x[1] in fsl_pos:
      		if(str.upper(x[0]) in ["AM", "IS", "ARE", "WILL", "SHALL", "BE", "HAVE", "HAS"]):
      			pass
      		else:
      			filtered.append(x)

      # Chunks the tagged words to describe source grammar structure.
      parsed = parser.parse(tagged)
      source_grammar = ""
      temp = ""
      for x in parsed:
      	if type(x) is nltk.Tree:
      		if x.label() == "VP" and temp == "VP":
      			pass
      		else:
      			temp = x.label()
      			source_grammar += x.label()+" "
      	else:
      		if x[1] == "PRP":
      			source_grammar += "PRP "

      # Lemmatize all words in translation.
      lemmatized = [ (str.upper(lemmatizer.lemmatize(key,get_wordnet_pos(key))),value) for (key, value) in filtered ] 

      # Get animation data.
      get_sigml(lemmatized)

      return render_template("result.html",
      		sentence = sentence,
      		tokens = tokens,
      		tagged = tagged,
      		parsed = parsed,
      		source_grammar = source_grammar,
      		filtered = filtered,
      		lemmatized = lemmatized)

if __name__ == '__main__':
   app.run(debug = True)