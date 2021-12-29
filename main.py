from flask import *
import pandas as pd
import os
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from keras.models import load_model 
from sklearn.preprocessing import MinMaxScaler
from flask_ngrok import run_with_ngrok
import numpy as np
app = Flask(__name__)
run_with_ngrok(app)

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
    
    loss_adam = pd.read_csv('static/data/loss_ogru/loss_history.csv')
    loss_adam_h = pd.read_csv('static/data/loss_ogru/loss_history_H.csv')
    loss_adam_hg = pd.read_csv('static/data/loss_ogru/loss_history_HG.csv')
    loss_adam_htrend = pd.read_csv('static/data/loss_ogru/loss_history_HTrend.csv')
    loss_sgd = pd.read_csv('static/data/loss_ogru/loss_history_sgd.csv')
    loss_sgd_h = pd.read_csv('static/data/loss_ogru/loss_history_sgd_H.csv')
    loss_sgd_hg = pd.read_csv('static/data/loss_ogru/loss_history_sgd_HG.csv')
    loss_sgd_htrend = pd.read_csv('static/data/loss_ogru/loss_history_sgd_HTrend.csv')
    
    label_loss_sgd = loss_sgd['index'].values
    value_loss_sgd = loss_sgd['loss'].values
    value_val_sgd_h = loss_sgd_h['val_loss'].values
    value_val_sgd_hg = loss_sgd_hg['val_loss'].values
    value_val_sgd_htrend = loss_sgd_htrend['val_loss'].values
    mean_val_sgd = loss_sgd['val_loss'].mean()
    mean_val_sgd_h = loss_sgd_h['val_loss'].mean()
    mean_val_sgd_htrend = loss_sgd_htrend['val_loss'].mean()
    mean_val_sgd_hg = loss_sgd_hg['val_loss'].mean()
    value_val_sgd = loss_sgd['val_loss'].values
    label_loss_adam = loss_adam['index'].values
    value_loss_adam = loss_adam['loss'].values
    value_val_adam = loss_adam['val_loss'].values
    value_val_adam_h = loss_adam_h['val_loss'].values
    value_val_adam_hg = loss_adam_hg['val_loss'].values
    value_val_adam_htrend = loss_adam_htrend['val_loss'].values
    mean_val = loss_adam['val_loss'].mean()
    mean_val_h = loss_adam_h['val_loss'].mean()
    mean_val_htrend = loss_adam_htrend['val_loss'].mean()
    mean_val_hg = loss_adam_hg['val_loss'].mean()

    return render_template('home.html', 
                            value_loss_sgd=value_loss_sgd, 
                            label_loss_sgd=label_loss_sgd, 
                            label_loss_adam=label_loss_adam, 
                            value_loss_adam=value_loss_adam,
                            value_val_sgd=value_val_sgd,
                            value_val_adam=value_val_adam,
                            value_val_adam_h=value_val_adam_h,
                            value_val_adam_hg=value_val_adam_hg,
                            value_val_adam_htrend=value_val_adam_htrend,
                            mean_val = mean_val,
                            mean_val_h=mean_val_h,
                            mean_val_htrend=mean_val_htrend,
                            mean_val_hg=mean_val_hg,
                            value_val_sgd_h=value_val_sgd_h,
                            value_val_sgd_hg=value_val_sgd_hg,
                            value_val_sgd_htrend=value_val_sgd_htrend,
                            mean_val_sgd = mean_val_sgd,
                            mean_val_sgd_h=mean_val_sgd_h,
                            mean_val_sgd_htrend=mean_val_sgd_htrend,
                            mean_val_sgd_hg=mean_val_sgd_hg,
                            )

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        n_past = 30
        n_days_for_prediction = int(request.get_json())
        us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())

        
        predict_period_dates = pd.date_range(list(train_dates)[-n_past], periods=n_days_for_prediction, freq=us_bd).tolist()
        print(predict_period_dates)
        # predict_period_dates = list(train_dates[-n_days_for_prediction:])

        model = load_model('static/data/model/my_model_with_gtrend_gold.h5')
        model_sgd = load_model('static/data/model/model_sgd_HGoldTrend.h5')

        trainX, trainY = sliding_window()

        prediction = model.predict(trainX[-n_days_for_prediction:])
        prediction_sgd = model_sgd.predict(trainX[-n_days_for_prediction:])

        prediction_copies = np.repeat(prediction, dataset_scaled.shape[1], axis=-1)
        y_pred_future = scaler.inverse_transform(prediction_copies)[:,0]
        prediction_copies_sgd = np.repeat(prediction_sgd, dataset_scaled.shape[1], axis=-1)
        y_pred_future_sgd = scaler.inverse_transform(prediction_copies_sgd)[:,0]

        forecast_dates = []
        for time_i in predict_period_dates:
            forecast_dates.append(time_i.date())
            
        df_forecast = pd.DataFrame({'ogru_adam':y_pred_future, 'ogru':y_pred_future_sgd})
        df_forecast['Date']=pd.to_datetime(df_forecast['Date'])


        original = bitcoin_time_series[['date', 'open']]
        original['date']=pd.to_datetime(original['date'])
        original = original.loc[original['date'] >= '2021-8-1']
        original_data = bitcoin_time_series[['date', 'open']][-n_days_for_prediction:]
        print(original_data['date'])


        result = pd.concat([original_data, df_forecast], axis=1)

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

    model = load_model('static/data/model/my_model_with_gtrend_gold.h5')

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

@app.route('/get_corr')
def get_corr():
    correlation = dataset.corr()

    return correlation.to_json()
    
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
    # app.run(debug=True)
    app.run()