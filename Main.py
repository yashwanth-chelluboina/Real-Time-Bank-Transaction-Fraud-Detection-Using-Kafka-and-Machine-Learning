from flask import Flask, render_template, request, redirect, url_for, session,send_from_directory
#loading required python classes and packages
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer, TopicPartition
from confluent_kafka import Producer
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score

app = Flask(__name__)
app.secret_key = 'welcome'

dataset = pd.read_csv("Dataset/BankingTransactionDataSet1.csv")
#dataset cleaning and processing by converting non-numeric values to numeric values
label_encoder = []
columns = dataset.columns
types = dataset.dtypes.values
for j in range(len(types)):
    name = types[j]
    if name == 'object': #finding column with object type
        le = LabelEncoder()
        dataset[columns[j]] = pd.Series(le.fit_transform(dataset[columns[j]].astype(str)))#encode all str columns to numeric
        label_encoder.append([columns[j], le])
dataset.fillna(dataset.mean(), inplace = True)#replace missing values with meaan if exists

#extracting training features and target label
Y = dataset['is_fraud'].ravel()
dataset.drop(['is_fraud'], axis = 1,inplace=True)
X = dataset.values
scaler = StandardScaler()
X = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.3)

#training Randon Forest 
rf = RandomForestClassifier()
rf.fit(X, Y)

def predictFraud(output):
    cols = ['transaction_id','sender_account_id','recipient_account_id','amount','payment_mode','timestamp','sender_location',
            'recipient_location','device_fingerprint','transaction_frequency']
    conf = {'bootstrap.servers': 'localhost:9092', 'group.id': 'sensor_stream_processor', 'auto.offset.reset': 'earliest'}
    consumer = Consumer(conf)
    # Subscribe to the BankTransaction
    consumer.subscribe(['BankTransaction'])
    # consume to stream data and process to cassandra
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            #break
            continue
        elif msg.error():
            # Handle any errors that occurred while polling for messages
            raise KafkaException(msg.error())
        else:
            msgs =  msg.value().decode('utf-8')
            print(msgs)
            if msgs == "exit":
                break
            else:
                data = msgs.split("#")
                values = []
                values.append([data[0], data[1], data[2], float(data[3]), data[4], data[5], data[6], data[7], data[8], int(data[9])])
                values = pd.DataFrame(values, columns=cols)
                temp = pd.DataFrame(values, columns=cols)
                for i in range(len(label_encoder)):
                    le = label_encoder[i]
                    values[le[0]] = pd.Series(le[1].transform(values[le[0]].astype(str)))#encode all str columns to numeric
                values = values.values
                values = scaler.transform(values)
                predict = rf.predict(values)[0]
                if predict == 0:
                    predict = "<font size=3 color=green>Normal</font>"
                else:
                    predict = "<font size=3 color=red>Fraud</font>"
                temp = temp.values
                for i in range(len(temp)):
                    output += '<tr>'
                    for j in range(len(temp[i])):
                        output += '<td><font size="3" color="black">'+str(temp[i,j])+'</td>'
                    output += '<td>'+predict+'</td>'      
                    output += '</tr>'
    return output                    

@app.route('/Consume', methods=['GET', 'POST'])
def Consume():
    if request.method == 'GET':
        output1='<table border=1 align=center width=100%><tr>'
        columns = ['transaction_id','sender_account_id','recipient_account_id','amount','payment_mode','timestamp','sender_location',
                'recipient_location','device_fingerprint','transaction_frequency']
        for i in range(len(columns)):
            output1 += '<th><font size="3" color="black">'+columns[i]+'</th>'
        output1 += '<th><font size="3" color="black">Predicted Status</th></tr>'
        output = ""
        output += predictFraud(output)
        output += "</table><br/><br/><br/><br/>"      
        return render_template('AdminScreen.html', data=output1+output)

#kafka producer to send stream
def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')    

@app.route('/Produce', methods=['GET', 'POST'])
def Produce():
    #creating producer
    p = Producer({'bootstrap.servers': 'localhost:9092'})
    #loading dataset
    dataset = pd.read_csv("Dataset/BankingTransactionDataSet1.csv")
    dataset = dataset.values
    #producer publishing dataset topics to bank transaction
    for i in range(len(dataset)):
        data = ""
        for j in range(len(dataset[i])):
            data += str(dataset[i,j])+"#"
        if len(data) > 0:
            data = data[0:len(data)-1]
        p.produce('BankTransaction', data, callback=delivery_report)
        p.flush()
    p.produce('BankTransaction', "exit", callback=delivery_report)
    p.flush()
    output = "<font size=3 color=blue>Kafka producer publish total records = "+str(dataset.shape[0])+"</font>"
    return render_template('AdminScreen.html', data=output)

@app.route('/AdminLogin', methods=['GET', 'POST'])
def AdminLogin():
    return render_template('AdminLogin.html', data='')

@app.route('/AdminLoginAction', methods=['GET', 'POST'])
def AdminLoginAction():
    if request.method == 'POST' and 't1' in request.form and 't2' in request.form:
        user = request.form['t1']
        password = request.form['t2']
        if user == "admin" and password == "admin":
            return render_template('AdminScreen.html', msg="Welcome "+user)
        else:
            return render_template('AdminLogin.html', msg="Invalid login details")

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', data='')

@app.route('/Logout')
def Logout():
    return render_template('index.html', data='')

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
