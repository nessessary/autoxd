#coding:utf8

"""判断一个"""

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop
from autoxd.cnn_boll.load_img import load_data
from keras.models import model_from_json
from autoxd import myredis
from autoxd.cnn_boll import my_recognition

class enum:
    key = 'model.json'
    h5 = 'model_weight.h5'
def run():
    json_string = myredis.get_obj(enum.key)
    model = model_from_json(json_string)
    model.load_weights(enum.h5)
    (x_train, y_train), (x_test, y_test) = my_recognition.get_data()
    data_len = x_train.shape[-2]*x_train.shape[-1]
    x_train = x_train.reshape(x_train.shape[0], data_len)
    x_test = x_test.reshape(x_test.shape[0], data_len)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255    
    x = x_test[-2:]
    model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(),
              metrics=['accuracy'])

    preds = model.predict(x)
    print(preds)
    #score = model.evaluate(x_test, y_test, verbose=0)
    #print('Test loss:', score[0])
    #print('Test accuracy:', score[1])    
if __name__ == "__main__":
    
    run()