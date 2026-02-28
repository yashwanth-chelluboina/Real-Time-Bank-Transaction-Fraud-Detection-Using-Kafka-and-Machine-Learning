# Real-Time Bank Transaction Fraud Detection Using Kafka and Machine Learning

## 📌 Project Overview

This project implements a real-time fraud detection system for bank transactions using Apache Kafka and Machine Learning. Transactions are streamed through Kafka producers and consumers, processed instantly, and analyzed using a trained ML model to detect fraudulent activities in real time.

The system is designed to simulate a scalable, production-level streaming pipeline.

---

## 🎯 Problem Statement

Traditional fraud detection systems rely on batch processing, which delays fraud identification. This project demonstrates a real-time streaming approach where transactions are evaluated instantly to reduce financial risk and improve response time.

---

## 🏗 System Architecture

1. Transaction Producer sends transaction data to Kafka topic.
2. Kafka Broker manages streaming pipeline.
3. Consumer reads real-time transactions.
4. ML Model evaluates transaction as Fraud / Not Fraud.
5. Result is displayed in web interface.

---

## 🛠 Tech Stack

- Python
- Apache Kafka
- Scikit-learn
- Pandas
- Flask
- HTML/CSS
- Jupyter Notebook

---

## ⚙️ Software Requirements

- Python 3.8+
- Java 8 or 11
- Apache Kafka 2.8.1 (Stable for Windows)
- Pip

---

## 📥 Kafka Setup (Windows)

1. Download Apache Kafka 2.8.1 from official website:
   https://kafka.apache.org/downloads

2. Extract Kafka folder.

3. Start Zookeeper: bin\windows\zookeeper-server-start.bat config\zookeeper.properties

4. Start Kafka Server: bin\windows\kafka-server-start.bat config\server.properties

---

## 📦 Project Setup

1. Clone the repository:
git clone https://github.com/yashwanth-chelluboina/Real-Time-Bank-Transaction-Fraud-Detection-Using-Kafka-and-Machine-Learning.git

2. Navigate to project folder:


cd Real-Time-Bank-Transaction-Fraud-Detection-Using-Kafka-and-Machine-Learning


3. Create virtual environment:


python -m venv env


4. Activate environment:


env\Scripts\activate


5. Install dependencies:


pip install -r requirements.txt


---

## ▶️ Running the Project

1. Start Kafka and Zookeeper.
2. Run Producer.
3. Run Consumer.
4. Start Flask application:


python Main.py


5. Open browser:

http://127.0.0.1:5000


---

## 📊 Model Details

- Supervised Machine Learning Model
- Feature engineering applied
- Model trained on labeled transaction dataset
- Outputs probability-based fraud classification

---

## 📈 Features

- Real-time streaming pipeline
- Kafka-based distributed messaging
- ML-based fraud prediction
- Web interface for result visualization
- Scalable architecture

---

## 🔮 Future Improvements

- Docker containerization
- Deployment on cloud (AWS / Azure)
- Real bank API integration
- Deep learning model enhancement
- Real-time dashboard analytics

---

## 👨‍💻 Author

Yashwanth Chelluboina  
B.Tech Student

---

## 📜 License

This project is for academic and learning purposes.
