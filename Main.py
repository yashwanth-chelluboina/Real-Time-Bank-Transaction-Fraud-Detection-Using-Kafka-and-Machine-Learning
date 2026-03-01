import uuid
import time
import csv
import io
import base64
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, jsonify
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = 'welcome'

# ================= LOAD & PREPARE DATA =================
dataset = pd.read_csv("Dataset/BankingTransactionDataSet1.csv")

label_encoder = []
columns = dataset.columns
types = dataset.dtypes.values

for j in range(len(types)):
    if types[j] == 'object':
        le = LabelEncoder()
        dataset[columns[j]] = le.fit_transform(dataset[columns[j]].astype(str))
        label_encoder.append([columns[j], le])

numeric_cols = dataset.select_dtypes(include=['number']).columns
dataset[numeric_cols] = dataset[numeric_cols].fillna(dataset[numeric_cols].mean())

Y = dataset['is_fraud'].to_numpy()
dataset.drop(['is_fraud'], axis=1, inplace=True)
dataset = dataset.select_dtypes(include=['number'])
X = dataset.values

scaler = StandardScaler()
X = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.3)

rf = RandomForestClassifier()
rf.fit(X, Y)

# ================= KAFKA CONSUMER (OUTPUT INTEGRATION) =================
def predictFraud(output):
    cols = ['transaction_id','sender_account_id','recipient_account_id','amount',
            'payment_mode','timestamp','sender_location',
            'recipient_location','device_fingerprint','transaction_frequency']

    conf = {'bootstrap.servers': 'localhost:9092',
            'group.id': f'sensor_group_{uuid.uuid4()}', 
            'auto.offset.reset': 'earliest'}

    consumer = Consumer(conf)
    consumer.subscribe(['BankTransaction'])

    empty_polls = 0
    row_count = 0
    html_rows = ""
    normal_count = 0
    fraud_count = 0

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                empty_polls += 1
                if empty_polls >= 10: # 🔴 FIX: Increased to 10 seconds!
                    print("Finished reading stream. Rendering Dashboard...")
                    break
                continue
            elif msg.error():
                continue

            empty_polls = 0 
            msgs = msg.value().decode('utf-8')

            if msgs == "exit":
                break

            data = msgs.split("#")
            
            # 🔴 FIX: If the data has 11 columns (from the CSV), safely ignore the 11th label column!
            if len(data) >= 10:
                data = data[:10] # Keep only the first 10 columns for the ML prediction
            else:
                print(f"Skipping malformed data: {len(data)} columns")
                continue

            values = [[data[0], data[1], data[2], float(data[3]),
                       data[4], data[5], data[6], data[7],
                       data[8], int(data[9])]]

            values = pd.DataFrame(values, columns=cols)
            temp = values.copy()

            for le_col in label_encoder:
                col_name, encoder = le_col
                if col_name in values.columns:
                    try:
                        values[col_name] = encoder.transform(values[col_name].astype(str))
                    except ValueError:
                        values[col_name] = 0 

            values = values.select_dtypes(include=['number']).values
            values = scaler.transform(values)

            predict = rf.predict(values)[0]

            if predict == 0:
                predict_html = "<font size=3 color=#10b981>Normal</font>"
                normal_count += 1
            else:
                predict_html = "<font size=3 color=#f43f5e>Fraud</font>"
                fraud_count += 1

            temp = temp.values

            if row_count < 100:
                for i in range(len(temp)):
                    html_rows += '<tr>'
                    for j in range(len(temp[i])):
                        html_rows += '<td>' + str(temp[i][j]) + '</td>'
                    html_rows += '<td>' + predict_html + '</td>'
                    html_rows += '</tr>'
            
            row_count += 1
            
    except Exception as e:
        print(f"Error processing message: {str(e)}")
    finally:
        consumer.close() 

    if row_count > 100:
        html_rows += f"<tr><td colspan='11' style='text-align:center; padding: 20px; color:#0ea5e9; font-weight:bold;'>... plus {row_count - 100} more transactions processed safely in the background ...</td></tr>"

    return output + html_rows, normal_count, fraud_count

def delivery_report(err, msg):
    pass 

# ================= ROUTES =================
@app.route('/Consume', methods=['GET', 'POST'])
def Consume():
    if request.method == 'GET':
        output1 = '<div class="table-container"><table border=1 align=center width=100%><tr>'
        columns = ['transaction_id','sender_account_id','recipient_account_id','amount',
                   'payment_mode','timestamp','sender_location',
                   'recipient_location','device_fingerprint','transaction_frequency']

        for col in columns:
            output1 += '<th>' + col + '</th>'
        output1 += '<th>Predicted Status</th></tr>'

        html_data, normal_count, fraud_count = predictFraud("")
        
        plt.figure(figsize=(8, 5))
        bars = plt.bar(['Normal', 'Fraud'], [normal_count, fraud_count], color=['#10b981', '#f43f5e'])
        
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + (max([normal_count, fraud_count])*0.02), int(yval), ha='center', va='bottom', color='white', fontweight='bold')

        plt.title('Live Machine Learning Analytics', color='white', pad=20, fontsize=14)
        plt.gca().set_facecolor('#0f172a') 
        plt.gcf().patch.set_facecolor('#0f172a')
        plt.tick_params(colors='white')
        plt.ylabel('Number of Transactions', color='white')

        for spine in plt.gca().spines.values():
            spine.set_edgecolor('gray')

        img_io = io.BytesIO()
        plt.savefig(img_io, format='png', bbox_inches='tight', transparent=True)
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        plt.close()

        return render_template('AdminScreen.html', data=output1 + html_data + "</table></div><br/><br/>", img=img_base64)

@app.route('/Produce', methods=['GET', 'POST'])
def Produce():
    p = Producer({'bootstrap.servers': 'localhost:9092'})
    dataset = pd.read_csv("Dataset/BankingTransactionDataSet1.csv")
    dataset_vals = dataset.values

    for row in dataset_vals:
        # 🔴 FIX: Drop the 11th column (is_fraud) before sending to the live stream
        features = row[:10] 
        data = "#".join(str(x) for x in features)
        try:
            p.produce('BankTransaction', data, callback=delivery_report)
            p.poll(0)
        except BufferError:
            p.poll(1)
            p.produce('BankTransaction', data, callback=delivery_report)

    p.produce('BankTransaction', "exit", callback=delivery_report)
    p.flush()

    output = "<font size=3 color=#0ea5e9>Kafka producer publish total records = " + str(dataset.shape[0]) + "</font>"
    return render_template('AdminScreen.html', data=output)

@app.route('/data_entry', methods=['GET'])
def data_entry():
    return render_template('DataEntry.html', msg='')

# --- 🔴 MANUAL DATA ENTRY (WITH TARGET LABEL) ---
@app.route('/AddDataAction', methods=['POST'])
def AddDataAction():
    try:
        form_data = request.json
        t_id = form_data['transaction_id']
        sender = form_data['sender_account_id']
        recipient = form_data['recipient_account_id']
        amount = form_data['amount']
        pmode = form_data['payment_mode']
        tstamp = form_data['timestamp']
        sloc = form_data['sender_location']
        rloc = form_data['recipient_location']
        dfinger = form_data['device_fingerprint']
        tfreq = form_data['transaction_frequency']
        is_fraud = int(form_data['is_fraud']) # Takes 0 or 1 from the form
        
        kafka_payload = f"{t_id}#{sender}#{recipient}#{amount}#{pmode}#{tstamp}#{sloc}#{rloc}#{dfinger}#{tfreq}"
        
        p = Producer({'bootstrap.servers': 'localhost:9092'})
        p.produce('BankTransaction', kafka_payload, callback=delivery_report)
        p.flush()
        
        new_csv_row = [t_id, sender, recipient, amount, pmode, tstamp, sloc, rloc, dfinger, tfreq, is_fraud]
        with open('Dataset/BankingTransactionDataSet1.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(new_csv_row)
        
        return jsonify({"status": "success", "message": "Transaction pushed to stream & saved to Dataset!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 🔴 NEW FAKE BANK API GENERATOR ---
@app.route('/api/fetch_bank_api', methods=['POST'])
def fetch_bank_api():
    try:
        num_transactions = 15 # Generates 15 random transactions per click
        
        locations = ['Gujarat', 'Rajasthan', 'Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'New York', 'London']
        modes = ['UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wire Transfer']
        
        p = Producer({'bootstrap.servers': 'localhost:9092'})
        
        new_rows = []
        for _ in range(num_transactions):
            t_id = f"T{random.randint(10000, 99999)}"
            sender = f"SBIN{random.randint(1000, 9999)}"
            recipient = f"AXIS{random.randint(1000, 9999)}"
            amount = round(random.uniform(50.0, 300000.0), 2)
            pmode = random.choice(modes)
            tstamp = time.strftime("%d-%m-%Y %H:%M")
            sloc = random.choice(locations)
            rloc = random.choice(locations)
            dfinger = f"DF{random.randint(100, 999)}"
            tfreq = random.randint(1, 15)
            
            # Realistically mix Normal (90%) and Fraud (10%)
            is_fraud = 1 if random.random() < 0.1 else 0
            
            # Push to stream
            kafka_payload = f"{t_id}#{sender}#{recipient}#{amount}#{pmode}#{tstamp}#{sloc}#{rloc}#{dfinger}#{tfreq}"
            p.produce('BankTransaction', kafka_payload, callback=delivery_report)
            
            # Prep for dataset saving
            new_rows.append([t_id, sender, recipient, amount, pmode, tstamp, sloc, rloc, dfinger, tfreq, is_fraud])
        
        p.flush()
        
        # Save to CSV in one batch
        with open('Dataset/BankingTransactionDataSet1.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(new_rows)
            
        return jsonify({"status": "success", "message": f"Successfully connected to Bank API. {num_transactions} transactions streamed & saved!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/AdminLogin', methods=['GET', 'POST'])
def AdminLogin():
    return render_template('AdminLogin.html', data='')

@app.route('/AdminLoginAction', methods=['GET', 'POST'])
def AdminLoginAction():
    if request.method == 'POST':
        user = request.form['t1']
        password = request.form['t2']

        if user == "admin" and password == "admin":
            return render_template('AdminScreen.html', msg="Welcome " + user)
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