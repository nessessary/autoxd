'''Trains a simple deep NN on the MNIST dataset.

Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop
from keras.models import model_from_json
from autoxd.cnn_boll.load_img import load_data
from autoxd import myredis

def get_data():
    return myredis.gen_data(__file__, get_data, lambda: load_data(method='data'))

def run():
    
    batch_size = 128
    num_classes = 81
    epochs = 20
    
    
    # the data, split between train and test sets
    #(x_train, y_train), (x_test, y_test) = mnist.load_data()
    (x_train, y_train), (x_test, y_test) = get_data()
    data_len = x_train.shape[-2]*x_train.shape[-1]
    
    x_train = x_train.reshape(x_train.shape[0], data_len)
    x_test = x_test.reshape(x_test.shape[0], data_len)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255
    print(x_train.shape[0], 'train samples')
    print(x_test.shape[0], 'test samples')
    
    # convert class vectors to binary class matrices
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)
    
    model = Sequential()
    model.add(Dense(512, activation='relu', input_shape=(data_len,)))
    model.add(Dropout(0.2))
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(num_classes, activation='softmax'))
    
    model.summary()
    
    model.compile(loss='categorical_crossentropy',
                  optimizer=RMSprop(),
                  metrics=['accuracy'])
    
    history = model.fit(x_train, y_train,
                        batch_size=batch_size,
                        epochs=epochs,
                        verbose=1,
                        validation_data=(x_test, y_test))
    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])
    
    #json_string = model.to_json()
    #key = 'model.json'
    #myredis.set_obj(key, json_string)
    #model.save_weights('model_weight.h5')

if __name__ == "__main__":
    
    run()