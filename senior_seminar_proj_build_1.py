# -*- coding: utf-8 -*-
"""Senior_Seminar_Proj_Build_1

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16JYuprd96HbpAEWxX3m1FXE4DSrC_s4J

###Imports
"""

import tensorflow as tf
from tensorflow.python.ops.gen_logging_ops import Print
from tensorflow import keras
from keras.layers import (Dense, Conv2D, Conv2DTranspose, Dropout, Input,
                          MaxPooling2D, concatenate, UpSampling2D)
from keras.models import (Sequential, Model, load_model)
from keras import backend
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import random
import glob
import PIL
import re
import os

# prints current library version
print("tf version: "+tf.__version__)
print("np version: "+np.__version__)
print("cv2 version: "+cv.__version__)

# detect and utilise Colab's TPU

try:
  tpu = tf.distribute.cluster_resolver.TPUClusterResolver()  # TPU detection
  print('Running on TPU ', tpu.cluster_spec().as_dict()['worker'])
except ValueError:
  raise BaseException('ERROR: Not connected to a TPU runtime; please see the previous cell in this notebook for instructions!')

tf.config.experimental_connect_to_cluster(tpu)
tf.tpu.experimental.initialize_tpu_system(tpu)
tpu_strategy = tf.distribute.TPUStrategy(tpu)

"""Data"""

# natural sort algorithm to keep images paired with the correct ground truth
def nat_sort(list: list[str]) :
  def alphaKey(key) :
    return [int(s) if s.isdigit() else s.lower() for s in re.split("([0-9]+)", key)]
  return sorted(list, key=alphaKey)


# paths to folders of iamges and their ground truths
# dataset 1 contains people, dataset 2 contains animals
# unused dataset commented out to improve performance
dataset1_path_train_images =       "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/archive (1)/dataset-splitM/Training/images"
dataset1_path_train_Ground_Truth = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/archive (1)/dataset-splitM/Training/GT"

#dataset2_path_train_images = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/Animals data/COD10K-v2/Train/Images/Image"
#dataset2_path_train_Ground_Truth = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/Animals data/COD10K-v2/Train/GT_Objects/GT_Object"


dataset1_path_test_images = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/archive (1)/dataset-splitM/Testing/images"
dataset1_path_test_Ground_Truth = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/archive (1)/dataset-splitM/Testing/GT"

#dataset2_path_test_images = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/Animals data/COD10K-v2/Test/Images/Image"
#dataset2_path_test_Ground_Truth = "/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/Animals data/COD10K-v2/Test/GT_Objects/GT_Object"


# lists of paths to images and gts natural sorted to ensure indices lead to corect image gt pairs later
# dataset 1 contains people, dataset 2 contains animals
Train_im_paths1 = np.array(nat_sort(glob.glob(f"{dataset1_path_train_images}/*.jpg")))
Train_GT_paths1 = np.array(nat_sort(glob.glob(f"{dataset1_path_train_Ground_Truth}/*.jpg")))

#Train_im_paths2 = np.array(nat_sort(glob.glob(f"{dataset2_path_train_images}/*.jpg")))
#Train_GT_paths2 = np.array(nat_sort(glob.glob(f"{dataset2_path_train_Ground_Truth}/*.png")))


test_im_paths1  = np.array(nat_sort(glob.glob(f"{dataset1_path_test_images}/*.jpg")))
test_GT_paths1  = np.array(nat_sort(glob.glob(f"{dataset1_path_test_Ground_Truth}/*.png")))

#test_im_paths2  = np.array(nat_sort(glob.glob(f"{dataset2_path_test_images}/*.jpg")))
#test_GT_paths2  = np.array(nat_sort(glob.glob(f"{dataset2_path_test_Ground_Truth}/*.png")))


# function : takes in folder paths, and a maximum value.
# then scans for files ending in .jpg or .png and loads them into numpy arrays
# thirdly it preprocesses the Ground truths
# process continues until an arbuitrary maximum number of files is reached and terminates
def Load_pair(im_path, GT_path, max) :
  tru_images = []
  tru_GTs = []
  count1 = 0
  count2 = 0
  for fname in im_path :
    if count1 >= max :
      break
    if fname.endswith('.jpg') or fname.endswith('.png') :
      count1 += 1
      image = cv.imread(fname)
      image = cv.resize(image, (256,256))
      tru_images.append(image)
      print(f"\rImage Count: {count1}/{count2}/{max}", end = "")
  for fname in GT_path :
    if count2 >= max :
      break
    if fname.endswith('.jpg') or fname.endswith('.png') :
      count2 += 1
      GT = cv.imread(fname)
      GT = cv.resize(GT, (256,256))
      GT = cv.normalize(GT, None, 0, 1, cv.NORM_MINMAX, dtype=cv.CV_32F)
      tru_GTs.append(GT)
      print(f"\rImage/GT Count: {count1}/{count2}/{max}", end = "")
  print(" | Load Complete")
  return np.array(tru_images), np.array(tru_GTs)

print(f"training length: {len(Train_im_paths1)}")
print(f"testing length: {len(test_im_paths1)}")



# runs the above methods and prints the shape of the first element of the lists
# to ensure that they are correct

train_im, train_GT = Load_pair(Train_im_paths1, Train_GT_paths1, 640)
print(f"Training IM Shape : {train_im[0].shape}")
print(f"Training GT Shape : {train_GT[0].shape}")
print()
test_im, test_gt = Load_pair(test_im_paths1, test_GT_paths1, 330)
print(f"Validation IM Shape : {test_im[0].shape}")
print(f"Validation GT Shape : {test_gt[0].shape}")

"""##Sanity Check"""

#generate a random number within the range of the training set
image_number = random.randint(0, len(train_im))

# prints the greatest value within the GT
# this serves to validate that the normalization procedure was a success
print(np.amax(train_GT[image_number]))

# generates a GT image pair and verifies that things are being read correctly
# also validates that the order of images and GTs match.
plt.figure(figsize=(8,4))
plt.subplot(121)
plt.imshow(np.reshape(train_im[image_number], (256, 256, 3)), cmap='gray')
plt.subplot(122)
plt.imshow(np.reshape(train_GT[image_number], (256, 256, 3)), cmap='gray')
plt.show

"""Model 1"""

backend.clear_session()


# defines the model 3 X base X 3 dimensions
def U_Net(input_shape=(256,256,3)):
  # input | layer 0
  inputs = Input(input_shape)

  # encode 1 | layer 1
  convolution1_1 = Conv2D(64, 3, activation='relu', padding='same')(inputs)
  convolution1_1 = Conv2D(64, 3, activation='relu', padding='same')(convolution1_1)
  pooling1_1 = MaxPooling2D(pool_size=(2,2))(convolution1_1)

  # encode 2 | layer 2
  convolution1_2 = Conv2D(128, 3, activation='relu', padding='same')(pooling1_1)
  convolution1_2 = Conv2D(128, 3, activation='relu', padding='same')(convolution1_2)
  pooling1_2 = MaxPooling2D(pool_size=(2,2))(convolution1_2)

  # encode 3 |  layer 3
  convolution1_3 = Conv2D(256, 3, activation='relu', padding='same')(pooling1_2)
  convolution1_3 = Conv2D(256, 3, activation='relu', padding='same')(convolution1_3)
  pooling1_3 = MaxPooling2D(pool_size=(2,2))(convolution1_3)

  # base | layer 5
  base1 = Conv2D(512, 3 , activation = 'relu', padding = 'same')(pooling1_3)
  base1 = Conv2D(512, 3 , activation = 'relu', padding = 'same')(base1)

  # decode 1 | layer 6
  upsample1_4 = UpSampling2D(size=(2,2))(base1)
  convolution1_4 = Conv2D(256, 2, activation='relu', padding='same')(upsample1_4)
  merge1_4 = concatenate([convolution1_3, convolution1_4], axis =3)
  convolution1_4 = Conv2D(256, 3, activation='relu', padding='same')(merge1_4)
  convolution1_4 = Conv2D(256, 3, activation='relu', padding='same')(convolution1_4)

  # decode 2 | layer 7
  upsample1_5 = UpSampling2D(size=(2,2))(convolution1_4)
  convolution1_5 = Conv2D(128, 2, activation='relu', padding='same')(upsample1_5)
  merge1_5 = concatenate([convolution1_2, convolution1_5], axis =3)
  convolution1_5 = Conv2D(128, 3, activation='relu', padding='same')(merge1_5)
  convolution1_5 = Conv2D(128, 3, activation='relu', padding='same')(convolution1_5)

  # decode 3 | layer 8
  upsample1_6 = UpSampling2D(size=(2,2))(convolution1_5)
  convolution1_6 = Conv2D(64, 2, activation='relu', padding='same')(upsample1_6)
  merge1_6 = concatenate([convolution1_1, convolution1_6], axis =3)
  convolution1_6 = Conv2D(64, 3, activation='relu', padding='same')(merge1_6)
  convolution1_6 = Conv2D(64, 3, activation='relu', padding='same')(convolution1_6)




  # output | layer 10
  outputs = Conv2D(3, 1, padding='same', activation='softmax')(convolution1_6)

  # model defined
  U_Net_Model = Model(inputs=inputs, outputs=outputs, name='U-Net')

  return U_Net_Model

# calls the tpu for processes involving the model
with tpu_strategy.scope():
  input_shape = (256,256,3)
  generator1 = U_Net(input_shape)

  optimizer = tf.keras.optimizers.Adam(learning_rate=0.0001)

  loss_function = tf.keras.losses.BinaryCrossentropy(from_logits=False)

  generator1.compile(optimizer=optimizer, loss=loss_function, metrics=['accuracy'])
  generator1.summary()

"""Model 1 Summary"""

# displays model diagram confirms correct architecture
tf.keras.utils.plot_model(generator1, show_shapes=True, show_layer_names=True)

"""Model 2"""

backend.clear_session()

def U_Net(input_shape=(256,256,3)):
  # input | layer 0
  inputs = Input(input_shape)

  # encode 1 | layer 1
  convolution2_1 = Conv2D(64, 3, activation='relu', padding='same')(inputs)
  convolution2_1 = Conv2D(64, 3, activation='relu', padding='same')(convolution2_1)
  pooling2_1 = MaxPooling2D(pool_size=(2,2))(convolution2_1)

  # encode 2 | layer 2
  convolution2_2 = Conv2D(128, 3, activation='relu', padding='same')(pooling2_1)
  convolution2_2 = Conv2D(128, 3, activation='relu', padding='same')(convolution2_2)
  pooling2_2 = MaxPooling2D(pool_size=(2,2))(convolution2_2)

  # encode 3 |  layer 3
  convolution2_3 = Conv2D(256, 3, activation='relu', padding='same')(pooling2_2)
  convolution2_3 = Conv2D(256, 3, activation='relu', padding='same')(convolution2_3)
  pooling2_3 = MaxPooling2D(pool_size=(2,2))(convolution2_3)

  # encode 4 | layer 4
  convolution2_4 = Conv2D(512, 3, activation='relu', padding='same')(pooling2_3)
  convolution2_4 = Conv2D(512, 3, activation='relu', padding='same')(convolution2_4)
  pooling2_4 = MaxPooling2D(pool_size=(2,2))(convolution2_4)

  # base | layer 5
  base2 = Conv2D(1024, 3 , activation = 'relu', padding = 'same')(pooling2_4)
  base2 = Conv2D(1024, 3 , activation = 'relu', padding = 'same')(base2)

  # decode 1 | layer 6
  upsample2_5 = UpSampling2D(size=(2,2))(base2)
  convolution2_5 = Conv2D(512, 2, activation='relu', padding='same')(upsample2_5)
  merge2_5 = concatenate([convolution2_4, convolution2_5], axis =3)
  convolution2_5 = Conv2D(512, 3, activation='relu', padding='same')(merge2_5)
  convolution2_5 = Conv2D(512, 3, activation='relu', padding='same')(convolution2_5)

  # decode 2 | layer 7
  upsample2_6 = UpSampling2D(size=(2,2))(convolution2_5)
  convolution2_6 = Conv2D(256, 2, activation='relu', padding='same')(upsample2_6)
  merge2_6 = concatenate([convolution2_3, convolution2_6], axis =3)
  convolution2_6 = Conv2D(256, 3, activation='relu', padding='same')(merge2_6)
  convolution2_6 = Conv2D(256, 3, activation='relu', padding='same')(convolution2_6)

  # decode 3 | layer 8
  upsample2_7 = UpSampling2D(size=(2,2))(convolution2_6)
  convolution2_7 = Conv2D(128, 2, activation='relu', padding='same')(upsample2_7)
  merge2_7 = concatenate([convolution2_2, convolution2_7], axis =3)
  convolution2_7 = Conv2D(128, 3, activation='relu', padding='same')(merge2_7)
  convolution2_7 = Conv2D(128, 3, activation='relu', padding='same')(convolution2_7)

  # decode 4 | layer 9
  upsample2_8 = UpSampling2D(size=(2,2))(convolution2_7)
  convolution2_8 = Conv2D(64, 2, activation='relu', padding='same')(upsample2_8)
  merge2_8 = concatenate([convolution2_1, convolution2_8], axis =3)
  convolution2_8 = Conv2D(64, 3, activation='relu', padding='same')(merge2_8)
  convolution2_8 = Conv2D(64, 3, activation='relu', padding='same')(convolution2_8)


  # output | layer 10
  outputs = Conv2D(3, 1, padding='same', activation='softmax')(convolution2_8)

  # model defined
  U_Net_Model = Model(inputs=inputs, outputs=outputs, name='U-Net')

  return U_Net_Model


with tpu_strategy.scope():
  input_shape = (256,256,3)
  generator2 = U_Net(input_shape)

  optimizer = tf.keras.optimizers.Adam(learning_rate=0.0001)

  loss_function = tf.keras.losses.BinaryCrossentropy(from_logits=False)

  generator2.compile(optimizer=optimizer, loss=loss_function, metrics=['accuracy'])
  generator2.summary()

"""Model 2 Summary"""

tf.keras.utils.plot_model(generator2, show_shapes=True, show_layer_names=True)

"""#EXECUTION

model 2
"""

epochs = 100
batch = 64

model = U_Net(input_shape=(256,256,3))

run_U_net_model = generator2.fit(train_im, train_GT,
                                 epochs=epochs,
                                 batch_size=batch,
                                 validation_data=(test_im, test_gt))

"""Model 2 data

Loss
"""

# run_U_net_model.save('/content/drive/MyDrive/Computer_Science/CSCI_599/Proj/model_1')

loss = run_U_net_model.history['loss']
val_loss = run_U_net_model.history['val_loss']

epochs = range(1, len(loss) + 1)

plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()


plt.figure(figsize=(12,6))
plt.subplot(1,3,1)
plt.imshow(np.reshape(test_im[190], (256,256, 3)), cmap='gray')
plt.title('Training and Validation Loss')
plt.subplot(1,3,2)
plt.imshow(np.reshape(test_gt[190], (256,256, 3)), cmap='gray')
plt.title('Actual Mask')
plt.subplot(1,3,3)
plt.imshow(PIL.Image.fromarray(predict_threshold[0,:,:,0]), cmap='gray')
plt.title('Predicted Mask')
plt.show

"""Accuracy"""

accuracy = run_U_net_model.history['accuracy']
val_accuracy = run_U_net_model.history['val_accuracy']

plt.plot(epochs, accuracy, 'y', label='Training accuracy')
plt.plot(epochs, val_accuracy, 'r', label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

"""IoU and Test results"""

# IOU
input_num = random.randint(0,len(test_im)-1)

input_image = test_im[190]
input_image = np.expand_dims(input_image, axis=0)
print(input_image.shape)

predict1 = generator2.predict(input_image)
predict_threshold = (predict1 > 0.5)

intersection = np.logical_and(predict_threshold, test_gt)
union = np.logical_or(predict_threshold, test_gt)
iou_score = np.sum(intersection) / np.sum(union)
print(f"image number: {input_num}")
print(f"IoU score: {iou_score*100}")

plt.figure(figsize=(12,6))
plt.subplot(1,3,1)
plt.imshow(np.reshape(test_im[190], (256,256, 3)), cmap='gray')
plt.title('Original Image')
plt.subplot(1,3,2)
plt.imshow(np.reshape(test_gt[190], (256,256, 3)), cmap='gray')
plt.title('Actual Mask')
plt.subplot(1,3,3)
plt.imshow(PIL.Image.fromarray(predict_threshold[0,:,:,0]), cmap='gray')
plt.title('Predicted Mask')
plt.show

"""Model 1 execution"""

epochs = 100
batch = 64

model1 = U_Net(input_shape=(256,256,3))

run_U_net_mode1 = generator1.fit(train_im, train_GT,
                                 epochs=epochs,
                                 batch_size=batch,
                                 validation_data=(test_im, test_gt))

"""Model 1 Data

Loss
"""

loss = run_U_net_mode1.history['loss']
val_loss = run_U_net_mode1.history['val_loss']

epochs = range(1, len(loss) + 1)

plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

"""Accuracy"""

accuracy = run_U_net_mode1.history['accuracy']
val_accuracy = run_U_net_mode1.history['val_accuracy']

plt.plot(epochs, accuracy, 'y', label='Training accuracy')
plt.plot(epochs, val_accuracy, 'r', label='Validation accuracy')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

"""IoU and Test Results"""

# IOU
input_num = random.randint(0,len(test_im))

input_image = test_im[190]
input_image = np.expand_dims(input_image, axis=0)
print(input_image.shape)

predict1 = generator1.predict(input_image)
predict_threshold = (predict1 > 0.5)

intersection = np.logical_and(predict_threshold, test_gt)
union = np.logical_or(predict_threshold, test_gt)
iou_score = np.sum(intersection) / np.sum(union)
print(f"image number: {input_num}")
print(f"IoU score: {iou_score*100}")

plt.figure(figsize=(12,6))
plt.subplot(1,3,1)
plt.imshow(np.reshape(test_im[190], (256,256, 3)), cmap='gray')
plt.title('Original Image')
plt.subplot(1,3,2)
plt.imshow(np.reshape(test_gt[190], (256,256, 3)), cmap='gray')
plt.title('Actual Mask')
plt.subplot(1,3,3)
plt.imshow(PIL.Image.fromarray(predict_threshold[0,:,:,0]), cmap='gray')
plt.title('Predicted Mask')
plt.show