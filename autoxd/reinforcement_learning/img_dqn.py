#coding:utf8

"""移植dqn_img_closeprice
从图形中找出规律
参考 Tensorflow-for-stock-prediction
"""
from collections import deque
import tensorflow as tf
import random
import numpy as np

# Hyper Parameters for DQN
GAMMA = 0.9 # discount factor for target Q
INITIAL_EPSILON = 0.5 # starting value of epsilon
FINAL_EPSILON = 0.01 # final value of epsilon
REPLAY_SIZE = 10000 # experience replay buffer size
BATCH_SIZE = 32 # size of minibatch

day_len = 15   # 每筆資料的日期天數

def conv2d(x, W,s):
    return tf.nn.conv2d(x, W, strides=[1, s,s,1], padding='SAME')

def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                        strides=[1, 2, 2, 1], padding='SAME')
class DQN():
    # DQN Agent
    def __init__(self):
        # init experience replay
        self.replay_buffer = deque()

        # init some parameters
        self.time_step = 0
        self.epsilon = INITIAL_EPSILON

        #self.state_dim = env.observation_space.shape[0]
        #self.action_dim = env.action_space.n

        self.state_dim = day_len
        self.action_dim = 3

        self._create_Q_network()
        self._create_training_method()

        # Init session
        #global session
        self.sess = tf.InteractiveSession()
        self.sess.run(tf.global_variables_initializer())

    def _create_Q_network(self):
        # network weights
        W_conv1 = self.weight_variable([8,8,4,32])
        b_conv1 = self.bias_variable([32])

        W_conv2 = self.weight_variable([4,4,32,64])
        b_conv2 = self.bias_variable([64])

        W_conv3 = self.weight_variable([3,3,64,64])
        b_conv3 = self.bias_variable([64])

        W_fc1 = self.weight_variable([4096,512])
        b_fc1 = self.bias_variable([512])

        W_fc2 = self.weight_variable([512,self.action_dim])
        b_fc2 = self.bias_variable([self.action_dim])

        # input layer
        self.state_input = tf.placeholder("float",[None,128,128])
        input1=tf.reshape(self.state_input,[-1,128,32,4])  

        # hidden layers
        h_conv1 = tf.nn.relu(conv2d(input1,W_conv1,4) + b_conv1)
        #h_pool1 = self.max_pool_2x2(h_conv1)

        h_conv2 = tf.nn.relu(conv2d(h_conv1,W_conv2,2) + b_conv2)

        h_conv3 = tf.nn.relu(conv2d(h_conv2,W_conv3,1) + b_conv3)
        h_conv3_shape = h_conv3.get_shape().as_list()
        print("dimension:",h_conv3_shape[1]*h_conv3_shape[2]*h_conv3_shape[3])
        h_conv3_flat = tf.reshape(h_conv3,[-1,4096])

        h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat,W_fc1) + b_fc1)

        # Q Value layer
        self.Q_value = tf.matmul(h_fc1,W_fc2) + b_fc2

    def _create_training_method(self):
        self.action_input = tf.placeholder("float",[None,self.action_dim])
        # one hot presentation
        self.y_input = tf.placeholder("float",[None])
        Q_action = tf.reduce_sum(tf.multiply(self.Q_value,self.action_input),reduction_indices = 1)
        self.cost = tf.reduce_mean(tf.square(self.y_input - Q_action))
        self.optimizer =  tf.train.RMSPropOptimizer(0.00025,0.99,0.0,1e-6).minimize(self.cost)

        #tf.scalar_summary("cost", values=self.cost)
        #tf.histogram_summary("cost", values=self.cost)

    def perceive(self,state,action,reward,next_state,done):
        """训练网络"""
        one_hot_action = np.zeros(self.action_dim)
        one_hot_action[action] = 1
        self.replay_buffer.append((state,one_hot_action,reward,next_state,done))

        if len(self.replay_buffer) > REPLAY_SIZE:
            self.replay_buffer.popleft()

        if len(self.replay_buffer) > BATCH_SIZE:
            self._train_Q_network()

    def _train_Q_network(self):
        self.time_step += 1

        # Step 1: obtain random minibatch from replay memory
        minibatch = random.sample(self.replay_buffer,BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        #print(reward_batch)
        next_state_batch = [data[3] for data in minibatch]
        # Step 2: calculate y
        y_batch = []
        Q_value_batch = self.Q_value.eval(feed_dict={self.state_input:next_state_batch})

        for i in range(0,BATCH_SIZE):
            done = minibatch[i][4]
            if done:
                y_batch.append(reward_batch[i])
            else :
                y_batch.append(reward_batch[i] + GAMMA * np.max(Q_value_batch[i]))
        self.optimizer.run(feed_dict={self.y_input:y_batch, self.action_input:action_batch, self.state_input:state_batch})


    def egreedy_action(self,state):
        """根据q值选一个action
        return: action"""
        Q_value = self.Q_value.eval(feed_dict = {
        self.state_input:[state]})[0]
        if random.random() <= self.epsilon:
            return random.randint(0,self.action_dim - 1)
        else:
            return np.argmax(Q_value)

        self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON)/10000


    def action(self,state):
        return np.argmax(self.Q_value.eval(feed_dict = {
        self.state_input:[state]})[0])


    def weight_variable(self,shape):
        initial = tf.truncated_normal(shape)
        return tf.Variable(initial)

    def bias_variable(self,shape):
        initial = tf.constant(0.01, shape = shape)
        return tf.Variable(initial)

