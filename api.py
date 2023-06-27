import base64
import io
from flask_cors import cross_origin
from flask_pymongo import pymongo
from flask import jsonify, request
import matplotlib
from pymongo import MongoClient
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
matplotlib.use('Agg')
# Establish MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['SalesForcast']
collection = db['LoginSignup']
def all_api(endpoints):
    #Signup POST API
    @endpoints.route('/signup', methods=['GET','POST'])
    def signup():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = {
        'username': username,
        'password': password
        }
        find=collection.find_one({'username':username})
        if find:
            return {'success': False, 'error': 'Exiting User'}
        collection.insert_one(user)
        return {'success': True ,'message':'Register Successfully'}
    #Login API
    @endpoints.route('/login', methods=['GET'])
    def login():
        username = request.args.get('username')
        password = request.args.get('password')
        user = collection.find_one({'username': username})
        if user and user['password'] == password:
            return  {'success': True, 'message':'Logged in  Successfully'}
        return {'success': False, 'error': 'Invalid username or password'}
    #File Upload POST
    @endpoints.route('/upload', methods=['GET','POST'])
    def upload():
        file = request.files['file']
        username = request.form['username']
        user = collection.find_one({'username': username})
        collection.update_one({'_id': user['_id']}, {'$set': {'filename': file.filename, 'data': file.read()}})
        return jsonify({'success': True,'message':'File uploaded Successfully'})
    #Prediction GET
    @endpoints.route('/predict', methods=['GET'])
    def predict():
        date = request.args.get('selectedValue')
        number = request.args.get('number')
        username = request.args.get('username')
        user = collection.find_one({'username': username})
        csv_data = io.BytesIO(user['data'])
        # Load CSV file into pandas DataFrame
        sales_data = pd.read_csv(csv_data,encoding='ISO-8859-1', parse_dates=['Order Date'], index_col='Order Date')
        # Resample the data to get monthly sales data
        monthly_sales = sales_data['Sales'].resample('M').sum()
        # Split data into training and testing sets
        train_data, test_data = train_test_split(monthly_sales, test_size=0.2, shuffle=False)
        # Define and fit the SARIMA model
        model = SARIMAX(train_data, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        model_fit = model.fit()
        periods = 12
        if date == 'year':
            periods = int(number) * 12
        elif number is not None:
            periods = int(number)
        # Make predictions for the given months
        future_dates = pd.date_range(start=monthly_sales.index[-1], periods=periods, freq='M')
        future_predictions = model_fit.predict(start=future_dates[0], end=future_dates[-1])
        # Plot the predicted sales values for the next 12 months
        plt.plot(monthly_sales.index, monthly_sales, label='Historical')
        plt.plot(future_dates, future_predictions, label='Forecast')
        plt.xlabel('Month')
        plt.ylabel('Sales')
        plt.title('Historical vs. Forecasted Sales')
        plt.legend()
        # Save the plot to a file-like object
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        # Close the plot
        plt.close()
        buffer.seek(0)
        
       
        # Convert the contents of the file-like object to a base64-encoded string
        image_string = base64.b64encode(buffer.getvalue()).decode()
        return jsonify({'success': True, 'image': image_string})
    return endpoints
