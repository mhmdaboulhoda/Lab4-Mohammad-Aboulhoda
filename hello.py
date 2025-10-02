from flask import Flask
from flask import Flask, render_template
from classes import Person, Student, Instructor, Course
from GUIbase.datastore import save_json, load_json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
    


