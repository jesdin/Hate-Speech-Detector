import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import text , sequence
import numpy as np
import pyrebase
import os
import sys
from flask import Flask, render_template, url_for, redirect, request
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

# new_model.summary()
#function for creating new user
def create_user(username , data):
    try:
        db.child("usertable").child(str(username)).set(data)
        return (f"User {usernaame} created Successfully")
    except Exception as e:
        return ('SOMETHING WENT WRONG IN CREATING USER!!!!')

#home_page
@app.route("/")
def home():
    return redirect(url_for('login'))

#login_page
@app.route("/login" , methods = ['GET' , 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db.child('usertable').child(username).get().val() is not None:
            user_password = db.child('usertable').child(str(username)).child("password").get().val()
            if user_password == password:
                return redirect(url_for("detection"))
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
                "password": password
            }
            create_user(username , data)
            return redirect(url_for('login'))
    return render_template('register.html')

#detection_page for hatespeech
@app.route("/detection" , methods = ['GET','POST'])
def detection():
    if request.method == 'POST':
        text = request.form['text']
        print(text)
        tokenizer.fit_on_texts(text)
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
        if(true_count > 1):
            result = True
        else:
            result = False
        return render_template('detection.html')
    return render_template('detection.html')

if __name__ == "__main__":
    app.run(threaded=True, port=5000)