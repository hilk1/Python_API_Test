from flask import Flask, render_template,jsonify, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor
from time import strftime
import requests
import asyncio
import uuid
import time
from tqdm import tqdm

API_KEY = None
CITY_ID = []

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
 
##CONFIGURE TABLE
class ApiPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ID = db.Column(db.String(250), nullable=False)
    city_ID = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    temperature = db.Column(db.String(250), nullable=False)
    humidity = db.Column(db.String(250), nullable=False)

db.create_all()

##WTForm
class CreatePostForm(FlaskForm):
    api_key = StringField("Enter your API Key", validators=[DataRequired()])
    city_id = TextField("City ID", validators=[DataRequired()])
    submit = SubmitField("Submit")
    
class CreateGetForm(FlaskForm):
    user_id = StringField("Enter your User ID", validators=[DataRequired()])
    get_json_file = SubmitField("Get")


async def post(user_id, CITY_ID):
    global API_KEY
    user_id = user_id      
    all_resquest_data = []    
    count = 0  
    invalid_city_ids = []
    for id in tqdm(CITY_ID):      
        try:
            response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?id={id}&appid={API_KEY}&units=metric')           
            all_resquest_data.append( {
                'user_id': str(user_id),
                'city_id': id,
                'Request_time': strftime("%Y/%m/%d %H:%M:%S"),
                'temperature': response.json()['main']['temp'],
                'humidity': response.json()['main']['humidity']
            })
            
            new_post = ApiPost(
                user_ID = str(user_id),
                city_ID = id,
                date = strftime("%Y/%m/%d %H:%M:%S"),
                temperature = response.json()['main']['temp'],
                humidity = response.json()['main']['humidity'],
            )
            
            count+=1
            if count == 60:
               time.sleep(60) 
        except:
            invalid_city_ids.append(id)
        
        db.session.add(new_post)
        db.session.commit()  
    
    return all_resquest_data, invalid_city_ids


@app.route('/', methods=["GET", "POST"])
def posts():
    global API_KEY
    form = CreatePostForm()
    if form.validate_on_submit():
        API_KEY = form.api_key.data
        CITY_ID = form.city_id.data.split(',')
        CITY_ID = [x.replace(" ", "") for x in CITY_ID]
        user_ID = uuid.uuid4()
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(post(user_id=user_ID, CITY_ID=CITY_ID))
            
        return render_template("statut.html", ID = user_ID)
                
    return render_template("index.html", form=form)



@app.route("/get-data", methods=["GET", "POST"])
def get_data():
    form = CreateGetForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        all_data =[]       
        weather_data = db.session.query(ApiPost).filter_by(user_ID=user_id).all()     
        if weather_data:
            for data in weather_data:
                all_data.append({
                    'user_id': data.user_ID ,
                    'city_id': data.city_ID ,
                    'Request_time': data.date ,
                    'temperature': data.temperature ,
                    'humidity': data.humidity 
                    })
                
            return jsonify(data=all_data)
        else:
            return jsonify(error = "No data found for this User ID.")
    return render_template("get-data.html", form = form)

@app.route("/download-data", methods=["GET"])
def download_data():   
    user_id = request.args.get('user_id')
    all_data =[]       
    weather_data = db.session.query(ApiPost).filter_by(user_ID=user_id).all()     
    if weather_data:
        for data in weather_data:
            all_data.append({
                'user_id': data.user_ID ,
                'city_id': data.city_ID ,
                'Request_time': data.date ,
                'temperature': data.temperature ,
                'humidity': data.humidity 
                })
            
        return jsonify(data=all_data)
    else:
        return jsonify(error = "No data found!")
    

     
if __name__ == "__main__":
    app.run()