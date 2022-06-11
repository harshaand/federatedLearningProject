# -*- coding: utf-8 -*-
"""federatedproject.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QgA69CoVihuFGg24FxYhZ3LjxEPJ2mD3
"""

#Installing all libraries to virtual environment
!pip install openml scikit-learn 
!pip install utils
!pip install tensorflow
!pip install keras
!pip install scikitplot

#Importing csv dataset from PC
from google.colab import drive, files
drive.mount('/content/drive')
uploaded = files.upload()

#Importing all modules used in the code
import utils 
import random
import cv2
import os
import itertools  
from imutils import paths
import numpy as np
from numpy import mean
from numpy import std
import pandas as pd
import matplotlib.pyplot  as plt
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn import datasets
from sklearn.metrics import accuracy_score
from sklearn.impute import SimpleImputer
from sklearn.model_selection import RepeatedKFold
#from sklearn.utils import shuffle
#from sklearn.model_selection import RepeatedKFold
from sklearn.metrics import confusion_matrix
from sklearn.metrics import multilabel_confusion_matrix
from sklearn.metrics import  auc
import tensorflow as tf
import keras as k
from keras.models import Sequential
from keras.layers import Dense
from keras.models import Sequential
#from keras.layers import Activation
from keras.layers import Flatten
from keras.layers import Dense
from tensorflow.keras.optimizers import SGD
from keras import backend as K
import seaborn as sns
import keras.metrics

"""### ***data for diss***"""

#Reading csv file and storing into pandas dataframe
df = pd.read_csv(r'train_ver6(1).csv', na_values=['#NAME?'] , encoding='latin-1')
df = df.drop(columns=[ 'id', 'ult_fec_cli_1t', 'spouse', 'province_code'])
df = df.dropna()
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy='constant', fill_value=1)
imputer.fit_transform(df)
df = pd.DataFrame(data=imputer.transform(df), columns=df.columns)

nan_value = float("NaN")
df.replace("", nan_value, inplace=True)
df.dropna(inplace=True)

df

target_labels  = ['ind_ahor_fin_ult1' ,'ind_aval_fin_ult1' ,'ind_cco_fin_ult1' ,'ind_cder_fin_ult1' ,'ind_cno_fin_ult1'
               ,'ind_ctju_fin_ult1' ,'ind_ctma_fin_ult1' ,'ind_ctop_fin_ult1' ,'ind_ctpp_fin_ult1' ,'ind_deco_fin_ult1'
               ,'ind_deme_fin_ult1' ,'ind_dela_fin_ult1' ,'ind_ecue_fin_ult1' ,'ind_fond_fin_ult1' ,'ind_hip_fin_ult1'
               ,'ind_plan_fin_ult1' ,'ind_pres_fin_ult1' ,'ind_reca_fin_ult1' ,'ind_tjcr_fin_ult1' ,'ind_valo_fin_ult1'
               ,'ind_viv_fin_ult1' ,'ind_nomina_ult1' ,'ind_nom_pens_ult1' ,'ind_recibo_ult1']
labels = df[target_labels]

features = df.drop(columns=target_labels)
features = features.drop(columns= ['employee_status', 'country_residence', 'cust_new','indrel_1mes', 'residence_index','indrel_1mes', 'indfall','tipodom'])
features.count()

"""###***Data preprocessing***"""

numerical_labels = ['age', 'cust_seniority', 'gross_income']
#Normalizing numerical columns
from sklearn import preprocessing
temp = features[numerical_labels] #returns a numpy array
min_max_scaler = preprocessing.MinMaxScaler()
features_scaled = min_max_scaler.fit_transform(temp)
features[numerical_labels] = pd.DataFrame(features_scaled)

#One hot encoding (dummy variables) catagorical features in dataset
catagorical_labels = ['gender',  'cust_relation_start_of_month', 'cust_active',                     
                'foreigner_index',  'segmentation', 'input_channel', 'province_name' ]
def dummy_df(df, catagorical_features):
  for i in catagorical_features:
    dummies = pd.get_dummies(df[i], prefix=i, dummy_na=False)
    df = df.drop(i, 1)
    df = pd.concat([df, dummies], axis=1)
  return df
features = dummy_df(features, catagorical_labels)

#Shuffling data then splitting dataset into training and testing samples
features = shuffle(features)
labels = shuffle(labels)
X_train, X_test, y_train, y_test = train_test_split(features, labels, train_size=0.80, random_state = 1)
X_train

#Converting data types to make data parsable
X_train , y_train = X_train.values, y_train.values 
X_train = np.asarray(X_train).astype('float32')
y_train = np.asarray(y_train).astype('float32')

X_test , y_test = X_test.values, y_test.values 
X_test = np.asarray(X_test).astype('float32')
y_test = np.asarray(y_test).astype('float32')

"""### ***Model creation***"""

#Defining neural network model for centralized learning and federated learning
class Model:
    @staticmethod
    def build(n_inputs, n_ouputs):
      model = Sequential()
      model.add(Dense(300, input_dim=n_inputs, 
                      activation='relu'))
      model.add(Dense(300, activation='relu'))
      model.add(Dense(n_ouputs, activation='sigmoid'))
      model.compile(loss='binary_crossentropy', optimizer='SGD')
      return model

def evaluate_model(X_test, y_test,  model, round_no,
                   accuracy_list, recall_list, precision_list, f1_list, loss_list):
  '''
      Function to calculate, print and store evaluation metrics of a model
      returns:
            -predictions: all predictions without rounding
      args: 
            -X_test, y_test: testing data
            - model: the training model
            -round_no: epoch number (centralized learning) or 
             round number(federated learning)
            -accuracy_list, recall_list, precision_list, f1_list, loss_list:
             all lists to store the models over epochs/rounds
 
  '''
  bce = tf.keras.losses.BinaryCrossentropy(from_logits=True)
  y_pred = model.predict(X_test)
  y_pred_rounded = np.around(y_pred)

  loss = bce(y_test, y_pred_rounded)
  loss_list.append(loss)
  #Confusion matrices for all labels
  confusion_matrices = multilabel_confusion_matrix(y_test, y_pred_rounded)
  #Summing all the matrices to get aggregated confusion matrix 
  sum_matrix = np.array(([0,0],[0,0]))
  for matrix in confusion_matrices:
    sum_matrix += matrix
  tp = sum_matrix[1][1]
  tn = sum_matrix[0][0]
  fn = sum_matrix[1][0]
  fp = sum_matrix[0][1]
  accuracy = (tp + tn)/(tp + fp + tn + fn)
  accuracy_list.append(accuracy)

  recall = tp / (tp + fn)
  recall_list.append(recall)

  precision = tp / (tp + fp)
  precision_list.append(precision)

  f1 = (2 * precision * recall)/ (precision + recall)
  f1_list.append(f1)

  print('''\n {} | accuracy: {:.3%} | recall: {}| precision: {:.3%} | f1: {}
  | loss: {:.3%}'''.format(round_no, accuracy, recall, precision, f1, loss))
  return y_pred

"""##**Federated learning**

#FL data processing
"""

def create_clients(X, y, num_clients=10, initial='client'):
    ''' 
        Function to create clients and assign sections of training dataset to them
        return: 
            a dictionary with clients' names as keys and their 
            their data shards as values
        args: 
            X: All features used for training
            y:All labels used for training
            num_client: number of fedrated clients
            initials: the clients'name prefix, e.g, client_1, client_2
            
    '''

    #Create a list of client names
    client_names = ['{}_{}'.format(initial, i+1) for i in range(num_clients)]

    #Grouping features and their corresponding labels together
    data = np.array(list(zip(X,y)))
    random.shuffle(data)

    #Splitting data ("shard": section of data assinged to a user)
    size = len(X)//num_clients
    shards = [data[i:i + size] for i in range(0, size*num_clients, size)]

    #Number of clients must equal number of shards
    assert(len(shards) == len(client_names))

    return {client_names[i] : shards[i] for i in range(len(client_names))}

def batch_data(data_shard):
    '''
        Converts a client's shard into a usable datatype
        args:
             shard: A section of data assinged to a user
        return:
             Arrays of features (X) and labels (y)'''
    X, y = zip(*data_shard)
    X = np.asarray(X)
    y = np.asarray(y)
    return X, y

#Creating new clients and assinging shards
clients = create_clients(X_train, y_train, num_clients=10, initial='clients')

clients_batched = dict()
for (client_name, data) in clients.items():
    clients_batched[client_name] = batch_data(data)

"""#FedAvg functions"""

def weight_scaling_factor(clients_train_data, client_name):
  '''
      Function to calculate a clients scaling factor for their weights
      returns: 
            -the scalar value
      args: 
            -dictionary all data used for training (clients_batched)
            -client's name                                   
 '''                                   
  client_names = list(clients_train_data.keys())
  client_features = clients_train_data[client_name][0]
  client_datapoints_count = len(client_features)

  global_datapoints_count = 0
  for client_name in client_names:
    client_features = clients_batched[client_name][0]
    client_batch_size = len(client_features)
    global_datapoints_count = global_datapoints_count + client_batch_size

    
  return client_datapoints_count/client_datapoints_count


def scale_model_weights_fedavg(weight, scalar):
  '''
      Function for scaling client's model weights by their scaling factor
      returns: 
            -client's model weights scaled
      args: 
            -client's model weights
            -clients scaling factor   
  '''

  weight_scaled = []
  steps = len(weight)
  for i in range(steps):
    weight_scaled.append((scalar * weight[i]))
  return weight_scaled
  
def scale_model_weights_qfedavg(weight, scalar, loss, q):
  '''
      Function for scaling client's model weights by their scaling factor
      returns implenting q - fedavg: 
            -client's model weights scaled
      args: 
            -client's model weights
            -clients scaling factor
            -client's loss
            -q value   
  '''
  q += 1
  weight_scaled = []
  steps = len(weight)
  for i in range(steps):
    weight_scaled.append(((scalar * weight[i])/ q)* pow(loss,q))
  return weight_scaled



def sum_scaled_weights(scaled_weight_list):
  '''
      Function to average all clients' weights.
      returns:
            -averaged weights
      args: 
            -list of all clients' weights
 
  '''
  avg_grad = list()
  #Calculating the average gradient accross all client weights
  for grad_list in zip(*scaled_weight_list):
    layer_mean = tf.math.reduce_sum(grad_list, axis=0)
    avg_grad.append(layer_mean)
  return avg_grad

"""###***Model deployment***

#Federated learning
"""

#Lists to store evaluation metrics of each round of learning 
accuracy_list_federated = []
recall_list_federated = []
precision_list_federated = []
f1_list_federated = []
rounds_list = []
loss_list_federated = []

#Model Hyper paramaters
lr = 0.01 
rounds = 9
loss='binary_crossentropy'
optimizer = SGD(lr=lr, 
                decay=lr / rounds, 
                #momentum=0.9
               )    
#Initialize global model
Model_federated = Model()
global_model = Model_federated.build(X_train.shape[1], y_train.shape[1])

#Global training loop
for round in range(rounds):
    rounds_list.append(round + 1)

    # Inital weights for clients
    global_weights = global_model.get_weights()
    
    #Initial list to collect local model weights after scalling
    scaled_local_weight_list = list()

    #Randomize client data - using keys
    client_names= list(clients_batched.keys())
    random.shuffle(client_names)
    
    #loop through each client and create new local model
    for client in client_names:

        smlp_local = Model()
        local_model = smlp_local.build(X_train.shape[1], y_train.shape[1])

        
        #set local model weight to the weight of the global model
        local_model.set_weights(global_weights)
        
        local_model.fit(clients_batched[client][0],clients_batched[client][1], 
                        epochs=5, verbose=0)
        

        bce = tf.keras.losses.BinaryCrossentropy(from_logits=True)
        y_pred = local_model.predict(X_test)
        y_pred_rounded = np.around(y_pred)
        local_loss = bce(y_test, y_pred_rounded)

        #scale the model weights and add to list
        scaling_factor = weight_scaling_factor(clients_batched, client)
        #scaled_weights = scale_model_weights_fedavg(local_model.get_weights(), 
                                             #scaling_factor)
        scaled_weights = scale_model_weights_qfedavg(local_model.get_weights(), 
                                            scaling_factor, local_loss, 1)
        scaled_local_weight_list.append(scaled_weights)

        #clear session to free memory after each communication round
        K.clear_session()
        
    #Calculate average weights of all clients
    average_weights = sum_scaled_weights(scaled_local_weight_list)
    
    #update global model 
    global_model.set_weights(average_weights)
    test_batched = X_test, y_test
    #Evaluate global model and print out metrics after each communications round
    y_pred_federated = evaluate_model(X_test, y_test, global_model, round + 1,
                                      accuracy_list_federated, 
                                      recall_list_federated,
                                      precision_list_federated,f1_list_federated, 
                                      loss_list_federated)

"""#Centralized learning"""

#Callback function that'll be called when evaluate performance of the model every epoch
class evaluate_model_callback(keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
       evaluate_model(X_test, y_test,  model, epoch + 1, accuracy_list_centralized, 
                      recall_list_centralized, precision_list_centralized, 
                      f1_list_centralized, loss_list_centralized)
       epoch_list.append(epoch + 1)

#Lists to store evaluation metrics of each round of learning 
accuracy_list_centralized = []
recall_list_centralized = []
precision_list_centralized = []
f1_list_centralized = []
loss_list_centralized = []
epoch_list = []

#Model hyper parameters
lr = 10
comms_round = 10
loss='binary_crossentropy'
metrics = ['accuracy']
optimizer = SGD()  
#Building and running the model
Model_centralized = Model()
model = Model_centralized.build(X_train.shape[1], y_train.shape[1]) 
model.fit(X_train, y_train, epochs=45, callbacks=[evaluate_model_callback()])

"""###***Model evaluation visualisation***

Run all cells chronologically
"""

'Functions to plot evaluation metrics of both models'
rounds_list2 = [i * 5 for i in rounds_list]
def plot_accuracy():
  plt.figure(1)
  plt.figure(figsize = (12, 12))
  plt.xlim((1,len(epoch_list) ))
  plt.ylim(((0, 1.1)))
  plt.plot(epoch_list, accuracy_list_centralized, label='Centralised learning')
  plt.plot(rounds_list2, accuracy_list_federated, label='Federated Learning')
  plt.xlabel('Epochs/federated rounds')
  plt.ylabel('Accuracy rate')
  plt.title('Accuracy rates', pad = 25, fontsize = 30)
  plt.legend(loc='best')
  plt.show

def plot_recall():
  plt.figure(1)
  plt.figure(figsize = (12, 12))
  plt.xlim((1,len(epoch_list) ))
  plt.ylim(((0, 1.1)))
  plt.plot(epoch_list, recall_list_centralized, label='Centralised learning')
  plt.plot(rounds_list2, recall_list_federated, label='Federated Learning')
  plt.xlabel('Epochs/federated rounds')
  plt.ylabel('Recall rate')
  plt.title('Recall rates', pad = 25, fontsize = 30)
  plt.legend(loc='best')
  plt.show()
def plot_f1():
  plt.figure(1)
  plt.figure(figsize = (12, 12))
  plt.xlim((1,len(epoch_list) ))
  plt.ylim(((0, 1.1)))
  plt.plot(epoch_list, f1_list_centralized, label='Centralised learning')
  plt.plot(rounds_list2, f1_list_federated, label='Federated Learning')
  plt.xlabel('Epochs/federated rounds')
  plt.ylabel('F1 rate')
  plt.title('F1 rates', pad = 25, fontsize = 30)
  plt.legend(loc='best')
  plt.show()
def plot_precision():
  plt.figure(1)
  plt.figure(figsize = (12, 12))
  plt.xlim((1,len(epoch_list) ))
  plt.ylim(((0, 1.1)))
  plt.plot(epoch_list, precision_list_centralized, label='Centralised learning')
  plt.plot(rounds_list2, precision_list_federated, label='Federated Learning')
  plt.xlabel('Epochs/federated rounds')
  plt.ylabel('Precision rate')
  plt.title('Precision rates', pad = 25, fontsize = 30)
  plt.legend(loc='best')
  plt.show()
def plot_loss():
  plt.figure(1)
  plt.figure(figsize = (12, 12))
  plt.xlim((1,len(epoch_list) ))
  plt.ylim(((0, 1.1)))
  plt.plot(epoch_list, loss_list_centralized, label='Centralised learning')
  plt.plot(rounds_list2, loss_list_federated, label='Federated Learning')
  plt.xlabel('Epochs/federated rounds')
  plt.ylabel('Loss rate')
  plt.title('Loss rates', pad = 25, fontsize = 30)
  plt.legend(loc='best')
  plt.show()

plot_accuracy()
plot_precision()
plot_recall()
plot_f1()
plot_loss()

y_pred_centralized = evaluate_model(X_test, y_test,  model, 1, accuracy_list_centralized, 
                      recall_list_centralized, precision_list_centralized, 
                      f1_list_centralized, loss_list_centralized)

from sklearn.metrics import roc_curve
from sklearn.metrics import auc
'Function to plot ROC and AUC of both models'
def roc_auc_plot(y_test, y_pred_federated, y_pred_centralized):
  
  plt.figure(1)
  plt.figure(figsize = (12, 12))
  y_test = y_test.ravel()
  y_pred_federated = y_pred_federated.ravel()
  y_pred_centralized = y_pred_centralized.ravel()

  #Federated learning ROC and AUC
  
  fpr_federated, tpr_federated, thresholds_federated = roc_curve(y_test, y_pred_federated)
  auc_federated = auc(fpr_federated, tpr_federated)
  #Centralized learning ROC and AUC
  
  fpr_centralized, tpr_centralized, thresholds_centralized = roc_curve(y_test, y_pred_centralized)
  auc_centralized = auc(fpr_centralized, tpr_centralized)
  #Plot
  plt.figure(figsize = (12, 12))
  plt.plot([0, 1], [0, 1], 'k--')
  plt.plot(fpr_federated, tpr_federated, label='Federated Learning (area = {:.3f})'.format(auc_federated))
  plt.plot(fpr_centralized, tpr_centralized, label='Centralised learning (area = {:.3f})'.format(auc_centralized))
  plt.xlabel('False positive rate')
  plt.ylabel('True positive rate')
  plt.title('ROC curves')
  plt.legend(loc='best')
  plt.show()

roc_auc_plot(y_test, y_pred_federated, y_pred_centralized)

'Function to plot confusion matrix of aggregated truths and predictions'
def plot_aggregate_cm(y_test, y_pred):
  #Calculate aggregate confusion matrix
  y_pred = np.around(y_pred)
  y_test = np.asarray(y_test).astype(int)
  y_pred = np.asarray(y_pred).astype(int)
  confusion_matrices = multilabel_confusion_matrix(y_test, y_pred)
  sum_matrix = np.array(([0,0],[0,0]))
  for matrix in confusion_matrices:
    sum_matrix += matrix
  sum_matrix

  #Plot matrix
  plt.figure(figsize = (10, 10))
  sns.set(font_scale=2)
  group_names = ['True Neg','False Pos','False Neg','True Pos']
  group_counts = ['{0:0.0f}'.format(value) for value in
                  sum_matrix.flatten()]
  group_percentages = ['{0:.2%}'.format(value) for value in
                      sum_matrix.flatten()/np.sum(sum_matrix)]
  plot_labels = [f'{v1}\n{v2}\n{v3}' for v1, v2, v3 in
            zip(group_names,group_counts,group_percentages)]        
  plot_labels = np.asarray(plot_labels).reshape(2,2)
  plt.title('Aggregated Predictions Confusion Matrix', fontsize=30, pad=30)
  sns.heatmap(sum_matrix,annot=plot_labels, fmt='')

plot_aggregate_cm(y_test, y_pred_centralized)
plot_aggregate_cm(y_test, y_pred_federated)

def plot_cms(y_test, y_pred):
  y_test = np.asarray(y_test).astype(int)
  y_pred = np.around(y_pred_centralized)
  y_pred = np.asarray(y_pred).astype(int)
  confusion_matrices = multilabel_confusion_matrix(y_test, y_pred)
  fig, axs = plt.subplots(5,5, figsize=(50, 50))
  fig.subplots_adjust(hspace = .3, wspace=0.1)
  axs = axs.ravel()
  for i in range(24):
    cm = confusion_matrices[i]
    #Plot matrix
    sns.set(font_scale=2)
    group_names = ['True Neg','False Pos','False Neg','True Pos']
    group_counts = ['{0:0.0f}'.format(value) for value in
                    cm.flatten()]
    group_percentages = ['{0:.2%}'.format(value) for value in
                        cm.flatten()/np.sum(cm)]
    plot_labels = [f'{v1}\n{v2}\n{v3}' for v1, v2, v3 in
              zip(group_names,group_counts,group_percentages)]        
    plot_labels = np.asarray(plot_labels).reshape(2,2)
    axs[i].set_title(target_labels[i], pad = 25)
    sns.heatmap(cm, ax=axs[i],annot=plot_labels, fmt='')

plot_cms(y_test, y_pred_centralized)

plot_cms(y_test, y_pred_federated)