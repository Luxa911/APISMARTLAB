import logging
import sys

from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
db = SQLAlchemy(app)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    birth_date = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)

# Функция для генерации кода подтверждения
def generate_confirmation_code(length=4):
  digits = string.digits
  return ''.join(random.choice(digits) for i in range(length))

# Функция для отправки email
def send_email(recipient, subject, body):
    sender_email = 'smartlaboratory2@mail.ru' # Замените на ваш email
    sender_password = 'rNyePmdY6EmpyXQVDN2D' # Замените на ваш пароль

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    try:
     server = smtplib.SMTP('smtp.mail.ru', 587) # Замените на ваш SMTP сервер
     server.starttls()
     server.login(sender_email, sender_password)
     server.sendmail(sender_email, recipient, message.as_string())
     server.quit()
     return True
    except Exception as e:
        print("Error sending email:",e);
        return False

@app.route('/api/sendCode', methods=['POST'])
def api_send_confirmation_code():

 data = request.get_json()

 recipient = data.get('email')

 if not recipient:
   return jsonify({"error": "Email is required"}), 400

 confirmation_code = generate_confirmation_code()
 subject = "Your confirmation code"
 body = f"Your confirmation code is: {confirmation_code}"

 try:
   if send_email(recipient, subject, body):
      return jsonify({"message": "Confirmation code sent successfully", "code": confirmation_code}), 200
   else:
    return jsonify({"error": "Failed code not sent successfully"}), 500
 except Exception as e:
   return jsonify({"error": str(e)}), 500

@app.route('/api/create_patient', methods=['POST'])
def create_patient():
    data = request.get_json()

    app.logger.info('Data received: %s', data)

    data['first_name'] = data.pop('firstName',None)
    data['last_name'] = data.pop('lastName',None)
    data['middle_name'] = data.pop('middleName',None)
    data['birth_date'] = data.pop('birthDate',None)
    data['gender'] = data.pop('gender',None)

    required_fields = ['first_name', 'last_name', 'middle_name', 'birth_date', 'gender']
    for field in required_fields:
        if field not in data:
            app.logger.error('Missing field: %s', field)
            return jsonify({"error": f"Missing required field: {field}"}), 400

    first_name = data['first_name']
    last_name = data['last_name']
    middle_name = data['middle_name']
    birth_date = data['birth_date'].strip()
    gender = data['gender']

    if not birth_date:
        app.logger.error('Birth date is required')
        return jsonify({"error": "Birth date is required"}), 400

    try:
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    except ValueError:
        app.logger.error('Invalid birth date format: %s', birth_date)
        return jsonify({"error": "Invalid date format. Expected format: YYYY-MM-DD"}),400

    if gender not in ['Мужской', 'Женский']:
        app.logger.error("Invalid gender: %s", gender)
        return jsonify({"error": "Invalid gender. Allowed values: Male, Female"}),400

    if not all([first_name, last_name, middle_name, birth_date, gender]):
        return jsonify({"error": "All fields are required"}), 400

    patient = Patient(first_name=first_name, last_name=last_name, middle_name=middle_name, birth_date=birth_date, gender=gender)

    try:
        db.session.add(patient)
        db.session.commit()
        app.logger.info("Patient has been created")
        return jsonify({"message": "Patient created successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error("Error creating patient: %s", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news():
    news = {
        'title': 'Чек-ап для мужчин',
        'description': '9 исследований',
        'price': '8000 ₽',
        'image_url': 'http://10.0.2.2:5000/api/news.png'
    }
    return jsonify(news)

if __name__ == '__main__':
    with app.app_context():
     db.create_all()
    app.run(debug=True, host='0.0.0.0')