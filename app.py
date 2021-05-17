import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import text , sequence
import numpy as np
import pyrebase
import string
import pickle
from flask import Flask, render_template, url_for, redirect, request, session
app = Flask(__name__)
config = {
    "apiKey": "AIzaSyAR4JirIoyLSyFevIjpeKT8w2TYrs7Fv88",
    "authDomain": "hate-speech-detection-c30b7.firebaseapp.com",
    "databaseURL": "https://hate-speech-detection-c30b7-default-rtdb.firebaseio.com",
    "projectId": "hate-speech-detection-c30b7",
    "storageBucket": "hate-speech-detection-c30b7.appspot.com",
    "messagingSenderId": "384678667028",
    "appId": "1:384678667028:web:efd828ff6043fc14dc9801",
    "measurementId": "G-08P28GDFE3"
}
app.config["SECRET_KEY"] = "ursecretkey"

print(tf.__version__)
model_path = '/home/prajwal/nlp_project/hate-speech-detection/model/hate_speech_model.h5'
new_model = load_model('./model/hate_speech_model.h5')
print('NLP MODEL LOADED SUCCESSFULLY!!')

#initializing the database
firebase = pyrebase.initialize_app(config)
db = firebase.database()

#defining the network parameters
max_features = 20000
maxlen = 100

#creating tokenizer
tokenizer = text.Tokenizer(num_words=max_features)
with open('./model/tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)

# new_model.summary()
#function for creating new user
def create_user(username , data):
    try:
        db.child("usertable").child(str(username)).set(data)
        return (f"User {usernaame} created Successfully")
    except Exception as e:
        return ('SOMETHING WENT WRONG IN CREATING USER!!!!')

def fetch_data(user):
    user_data = db.child("usertable").child(str(user)).get()
    for i in user_data.each():
        if(i.key() == 'sentiments'):
            ss = i.val()
    del ss[0]
    ss.reverse()
    return ss

def update_database(user , sentence , result):
    try:
        user_data = db.child("usertable").child(str(user)).get()
        for i in user_data.each():
            if(i.key() == 'sentiments'):
                i.val().append([sentence, result])
                val = i.val()
        db.child("usertable").child(user).update({"sentiments": val})
        return True
    except Exception as e:
        return("Something Went Wrong !!")

#home_page
@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/landing")
def landing():
    if 'username' not in session:
        return render_template('register.html')
    else:
        recently_added = fetch_data(session['username'])
        print(type(recently_added))
        print(recently_added)
        return render_template('detection.html' , recently_added = recently_added , len_recently_added = len(recently_added))

#login_page
@app.route("/login" , methods = ['GET' , 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db.child('usertable').child(username).get().val() is not None:
            user_password = db.child('usertable').child(str(username)).child("password").get().val()
            if user_password == password:
                session['username'] = request.form['username']
                return redirect(url_for("landing"))
            else:
                print('Password is wrong!!')
                return render_template('Login.html' , error_password = True)
    return render_template('Login.html')

#register_page for user
@app.route("/register", methods = ['GET' , 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        #checking if user already exists in database
        if db.child('usertable').child(username).get().val() is not None :
            print('USER ALREADY EXSIST...')
            return render_template('register.html' , error = True)
        else:
            data = {
                "email": email,
                "username":username,
                "password": password,
                "sentiments":[('Sentences', 'Hate')]
            }
            create_user(username , data)
            return redirect(url_for('login'))
    else:
        return render_template('register.html')

#detection_page for hatespeech
@app.route("/detection" , methods = ['GET','POST'])
def detection():
    #detecting the hate-speech
    if "username" in session:
        text = request.form['text']
        text = text.translate(str.maketrans('', '', string.punctuation))
        print(text)
        tokenized_sentence = tokenizer.texts_to_sequences(text)
        x = sequence.pad_sequences(tokenized_sentence , maxlen = maxlen)
        print(type(x))
        print(x.shape)
        prediction = new_model.predict(x)
        print(prediction.shape)
        prediction = (prediction > 0.5)
        true_count = 0
        for i in prediction:
            if i == [True]:
                true_count += 1
        print(f'TRUE COUNT {true_count}')
        print(np.any(prediction))
        result = False
        if(true_count > 1):
            result = True
        else:
            result = False
        
        #filing the table with the searched texts.
        update_database(session['username'] , str(text) , str(result))
        recently_added = fetch_data(session['username'])
        return render_template('detection.html' , result = result , recently_added = recently_added , len_recently_added = len(recently_added))
    else:
        render_template('register.html')

if __name__ == "__main__":
    app.run(debug = True)