import spacy

# Load your CPU-trained test model
nlp = spacy.load("backend/models/ner_test/model-last")

# Example text (you can replace this with any resume text)
text = """
John Doe is a software engineer with 5 years of experience in Python, 
Machine Learning, and AWS. He also knows JavaScript and has worked on NLP projects.
"""

# Process the text
doc = nlp(text)

# Print extracted entities
print("Detected entities:")
for ent in doc.ents:
    print(f"{ent.text} -> {ent.label_}")
