from flask import *
import pandas as pd
import os
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from keras.models import load_model 
from sklearn.preprocessing import MinMaxScaler
import numpy as np
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
DIR = 'static/data/'
bitcoin_time_series = pd.read_csv(DIR + "cmc_plus_gold_fixed.csv", parse_dates = ['date'])
gtrend_time_series = pd.read_csv(DIR + "daily_gtrend_data_cmc.csv", parse_dates = ['date'])
dataset = bitcoin_time_series.copy()
dataset['gtrend'] = gtrend_time_series['bitcoin']
train_dates = dataset['date']

del gtrend_time_series


dataset = dataset.drop('date', axis = 1)
dataset = dataset.drop('index', axis = 1)
scaler = MinMaxScaler().fit(dataset)
dataset_scaled = scaler.transform(dataset)



@app.route('/')
def index():
    
    loss_adam = pd.read_csv('static/data/loss_history.csv')
    loss_sgd = pd.read_csv('static/data/loss_history_sgd.csv')
    label_loss_sgd = loss_sgd['index'].values
    value_loss_sgd = loss_sgd['loss'].values
    value_val_sgd = loss_sgd['val_loss'].values
    label_loss_adam = loss_adam['index'].values
    value_loss_adam = loss_adam['loss'].values
    value_val_adam = loss_adam['val_loss'].values
    return render_template('home.html', 
                            value_loss_sgd=value_loss_sgd, 
                            label_loss_sgd=label_loss_sgd, 
                            label_loss_adam=label_loss_adam, 
                            value_loss_adam=value_loss_adam,
                            value_val_sgd=value_val_sgd,
                            value_val_adam=value_val_adam
                            )

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        n_past = 7
        n_days_for_prediction = int(request.get_json())
        us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())

        
        predict_period_dates = pd.date_range(list(train_dates)[-n_past], periods=n_days_for_prediction, freq=us_bd).tolist()
        print(predict_period_dates)

        model = load_model('static/data/my_model_with_gtrend_gold.h5')

        trainX, trainY = sliding_window()

        prediction = model.predict(trainX[-n_days_for_prediction:])

        prediction_copies = np.repeat(prediction, dataset_scaled.shape[1], axis=-1)
        y_pred_future = scaler.inverse_transform(prediction_copies)[:,0]

        forecast_dates = []
        for time_i in predict_period_dates:
            forecast_dates.append(time_i.date())
            
        df_forecast = pd.DataFrame({'Date':np.array(forecast_dates), 'Open':y_pred_future})
        df_forecast['Date']=pd.to_datetime(df_forecast['Date'])


        original = bitcoin_time_series[['date', 'open']]
        original['date']=pd.to_datetime(original['date'])
        original = original.loc[original['date'] >= '2021-8-1']


        result = pd.concat([original, df_forecast], axis=1)

        return result.to_json()
    else:
        return 'Ops Something went wrong'

@app.route('/testpredict')
def testpredict():
    n_past = 7
    n_days_for_prediction = 30
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())

    
    predict_period_dates = pd.date_range(list(train_dates)[-n_past], periods=n_days_for_prediction, freq=us_bd).tolist()
    print(predict_period_dates)

    model = load_model('static/data/my_model_with_gtrend_gold.h5')

    trainX, trainY = sliding_window()
    print(trainX.shape)

    prediction = model.predict(trainX[-n_days_for_prediction:])

    prediction_copies = np.repeat(prediction, dataset_scaled.shape[1], axis=-1)
    y_pred_future = scaler.inverse_transform(prediction_copies)[:,0]

    forecast_dates = []
    for time_i in predict_period_dates:
        forecast_dates.append(time_i.date())
        
    df_forecast = pd.DataFrame({'Date':np.array(forecast_dates), 'Open':y_pred_future})
    df_forecast['Date']=pd.to_datetime(df_forecast['Date'])


    original = bitcoin_time_series[['date', 'open']]
    original['date']=pd.to_datetime(original['date'])
    original = original.loc[original['date'] >= '2021-8-1']

    result = pd.concat([original, df_forecast], axis=1)

    return result.to_json()

    
def sliding_window():
    trainX = []
    trainY = []
    n_future = 1
    n_past = 30

    for i in range(n_past, len(dataset) - n_future +1):
        trainX.append(dataset_scaled[i - n_past:i, 0:dataset_scaled.shape[1]])
        trainY.append(dataset_scaled[i + n_future - 1:i + n_future, 0])

    return np.array(trainX), np.array(trainY)

if __name__ == "__main__":
    app.run(debug=True)