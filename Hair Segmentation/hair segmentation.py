# -*- coding: utf-8 -*-
"""WorkingA_3ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Wv4rNfUqtnD1unhKAAWbRSUdVDcxEyGb

# Assignment 3
"""

import tensorflow as tf
import os
from google.colab import drive

tf.compat.v1.enable_eager_execution()

"""# Mount the Google Drive"""

# Commented out IPython magic to ensure Python compatibility.
# mount the drive
drive.mount('/gdrive')
# %cd /gdrive

# Go to the assignment folder in the drive and make it current location
# %cd /gdrive/My Drive/Assignment 3
print('\n\nFiles in the Assignment 3 Data folder:')
!ls

"""# Load images, then parse the images"""

IMAGE_PATH = 'images/images/'
# create list of PATHS
image_paths_full = [os.path.join(IMAGE_PATH, x) for x in os.listdir(IMAGE_PATH) if x.endswith('.jpg')]

DATASET_FULL_SIZE = len(image_paths_full)
print(image_paths_full)
print(DATASET_FULL_SIZE)

from sklearn.model_selection import train_test_split
train_valid_image_paths, test_image_paths = train_test_split(image_paths_full, test_size=0.15, random_state=42)

train_image_paths, valid_image_paths = train_test_split(image_paths_full, test_size=0.15, random_state=42)

TRAIN_DATASET_SIZE = len(train_image_paths)
VALID_DATASET_SIZE = len(valid_image_paths)
TEST_DATASET_SIZE = len(test_image_paths)

print(TRAIN_DATASET_SIZE)
print(VALID_DATASET_SIZE)
print(TEST_DATASET_SIZE)

import numpy as np

AUTOTUNE = tf.data.experimental.AUTOTUNE
IMG_SIZE = 128
np.random.seed(0)

# parse_data function helps to get each image and the corresponding mask,
#                              performs decoding, resizing, rescaling, and other data transformations
# for more data transformations: https://github.com/HasnainRaz/SemSegPipeline/blob/master/dataloader.py

def parse_data(image_path):
  image_content = tf.io.read_file(image_path)
 
  mask_path = tf.strings.regex_replace(image_path, "images", "masks")
  mask_path = tf.strings.regex_replace(mask_path, "jpg", "jpg")
  mask_content = tf.io.read_file(mask_path)
  
  image = tf.image.decode_jpeg(image_content, channels=3)
  mask = tf.image.decode_jpeg(mask_content, channels=1)
  
  image = tf.image.resize(image, (IMG_SIZE, IMG_SIZE))
  image = tf.cast(image, tf.float32) / 255.0

  mask = tf.image.resize(mask, (IMG_SIZE, IMG_SIZE))
  mask = tf.cast(mask, tf.float32) /255.0
  
  # The pixels in the given segmentation mask are labeled either {1, 2, 3}. 
  # So we subtract 1 from the segmentation mask, resulting in labels that are : {0, 1, 2}.
  # mask -= 1 
  #mask = tf.image.convert_image_dtype(mask, tf.uint8)
  
  image = tf.convert_to_tensor(image)
  mask = tf.convert_to_tensor(mask)

  return image, mask

# Use Dataset.map to apply a function to each element of the dataset
train_dataset_imgpaths = tf.data.Dataset.from_tensor_slices((train_image_paths))
train_dataset = train_dataset_imgpaths.map(parse_data, num_parallel_calls=AUTOTUNE)

valid_dataset_imgpaths = tf.data.Dataset.from_tensor_slices((valid_image_paths))
valid_dataset = valid_dataset_imgpaths.map(parse_data, num_parallel_calls=AUTOTUNE)

test_dataset_imgpaths = tf.data.Dataset.from_tensor_slices((test_image_paths))
test_dataset = test_dataset_imgpaths.map(parse_data, num_parallel_calls=AUTOTUNE)

print(train_dataset)

BATCH_SIZE = 32
BUFFER_SIZE = 1000

train_dataset_batch = train_dataset.cache().shuffle(BUFFER_SIZE).repeat().batch(BATCH_SIZE)
train_dataset_batch = train_dataset_batch.prefetch(buffer_size=AUTOTUNE)

valid_dataset_batch = valid_dataset.cache().repeat().batch(BATCH_SIZE)
valid_dataset_batch = valid_dataset_batch.prefetch(buffer_size=AUTOTUNE)

test_dataset_batch = test_dataset.cache().repeat().batch(BATCH_SIZE)
test_dataset_batch = test_dataset_batch.prefetch(buffer_size=AUTOTUNE)

"""# Importing Testing Images for prediction"""

TESTING_PATH = 'testing_images/'
test_paths_full = [os.path.join(TESTING_PATH,x) for x in os.listdir(TESTING_PATH) if x.endswith('.jpg')]

TESTING_FULL_SIZE = len(test_paths_full)
print(test_paths_full)
print(TESTING_FULL_SIZE)

def parse_test_data(image_path):
  image_content = tf.io.read_file(image_path)
  test_image = tf.image.decode_jpeg(image_content, channels= 3)
  test_image = tf.image.resize(test_image, (IMG_SIZE, IMG_SIZE))
  test_image = tf.cast(test_image, tf.float32) / 255.0
  test_image = tf.convert_to_tensor(test_image)
  return test_image

test_data = tf.data.Dataset.from_tensor_slices((test_paths_full))
testing_content = test_data.map(parse_test_data, num_parallel_calls=AUTOTUNE)

testing_dataset_batch = testing_content.cache().batch(BATCH_SIZE)
testing_dataset_batch = testing_dataset_batch.prefetch(buffer_size=AUTOTUNE)

# print(testing_content)

print(testing_content)

"""# Display a sample image from training data

"""

import matplotlib.pyplot as plt

# np.random.seed()
def display(display_list):
  plt.figure(figsize=(10, 10))

  title = ['Input Image', 'True Mask', 'Predicted Mask']

  for i in range(len(display_list)):
    plt.subplot(1, len(display_list), i+1)
    plt.title(title[i])
    plt.imshow(tf.keras.preprocessing.image.array_to_img(display_list[i]))
  plt.show()

for image, mask in train_dataset.take(1):
  sample_image, sample_mask = image, mask
  print('Sample Images')
  display([sample_image, sample_mask])
print(sample_mask.shape)
print(sample_image.shape)

"""# Create a U-net Model"""

from tensorflow.keras.layers import Input
from tensorflow.keras.layers import Conv2D, Conv2DTranspose
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import concatenate
from tensorflow.keras.models import Model

# Build U-Net model
s = Input((IMG_SIZE, IMG_SIZE, 3))

c1 = Conv2D(16, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (s)
c1 = Dropout(0.1) (c1)
# c1 = Conv2D(16, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c1)
p1 = MaxPooling2D((2, 2)) (c1)

c2 = Conv2D(32, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (p1)
c2 = Dropout(0.1) (c2)
c2 = Conv2D(32, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c2)
p2 = MaxPooling2D((2, 2)) (c2)

c3 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (p2)
c3 = Dropout(0.2) (c3)
c3 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c3)
c3 = Dropout(0.2) (c3)
c3 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c3)
c3 = Dropout(0.2) (c3)
c3 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c3)
p3 = MaxPooling2D((2, 2)) (c3)

c4 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (p3)
c4 = Dropout(0.2) (c4)
# c4 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c4)
# c4 = Dropout(0.2) (c4)
# c4 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c4)
c4 = Dropout(0.2) (c4)
c4 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c4)
p4 = MaxPooling2D(pool_size=(2, 2)) (c4)

c5 = Conv2D(256, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (p4)
c5 = Dropout(0.3) (c5)
c5 = Conv2D(256, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c5)
# c5 = Dropout(0.3) (c5)
# c5 = Conv2D(256, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c5)
# c5 = Dropout(0.3) (c5)
# c5 = Conv2D(256, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c5)

u6 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same') (c5)
u6 = concatenate([u6, c4])
c6 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (u6)
c6 = Dropout(0.2) (c6)
# c6 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c6)
# c6 = Dropout(0.2) (c6)
# c6 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c6)
c6 = Dropout(0.2) (c6)
c6 = Conv2D(128, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c6)

u7 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same') (c6)
u7 = concatenate([u7, c3])
c7 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (u7)
c7 = Dropout(0.2) (c7)
c7 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c7)
c7 = Dropout(0.2) (c7)
c7 = Conv2D(64, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c7)

u8 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same') (c7)
u8 = concatenate([u8, c2])
c8 = Conv2D(32, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (u8)
c8 = Dropout(0.1) (c8)
c8 = Conv2D(32, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c8)

u9 = Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same') (c8)
u9 = concatenate([u9, c1], axis=3)
c9 = Conv2D(16, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (u9)
c9 = Dropout(0.1) (c9)
# c9 = Conv2D(16, (5, 5), activation='elu', kernel_initializer='he_normal', padding='same') (c9)

outputs = Conv2D(3, (1, 1), activation='sigmoid') (c9)

model = Model(inputs=[s], outputs=[outputs])

# model.summary()

model.compile(optimizer='RMSprop', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

from IPython.display import clear_output

class DisplayCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs=None):
    clear_output(wait=True)
    show_predictions()
    print ('\nSample Prediction after epoch {}\n'.format(epoch+1))

def create_mask(pred_mask):
  return pred_mask[0]

def show_predictions(dataset=None, num=2):
  if dataset:
    for image, mask in dataset.take(num):
      pred_mask = model.predict(image)
      display([image[0], mask[0], create_mask(pred_mask)])
  else:
    display([sample_image, sample_mask,
             create_mask(model.predict(sample_image[tf.newaxis, ...]))])

"""# Model Prediction """

EPOCHS = 35
VAL_SUBSPLITS = 5
STEPS_PER_EPOCH = TRAIN_DATASET_SIZE//BATCH_SIZE
VALIDATION_STEPS = VALID_DATASET_SIZE//BATCH_SIZE//VAL_SUBSPLITS

model_history = model.fit(train_dataset_batch, epochs=EPOCHS,
                          steps_per_epoch=STEPS_PER_EPOCH,
                          validation_steps=VALIDATION_STEPS,
                          validation_data=valid_dataset_batch,
                          callbacks=[DisplayCallback()])

loss = model_history.history['loss']
val_loss = model_history.history['val_loss']

epochs = range(EPOCHS)

plt.figure()
plt.plot(epochs, loss, 'r', label='Training loss')
plt.plot(epochs, val_loss, 'bo', label='Validation loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss Value')
plt.ylim([0, 5])
plt.legend()
plt.show()

show_predictions(test_dataset_batch, 5)

"""# Testing Image Prediction

"""

results = model.predict(testing_dataset_batch)

print(results.shape)

results = tf.image.resize(results, (250, 250))
results = tf.image.rgb_to_grayscale(results)
for i in range (3):  
  plt.imshow(tf.keras.preprocessing.image.array_to_img(results[i]))
  plt.show()

"""# Preparing folder to save predicted testing images masks

"""

# Making sure the google drive pred_mask folder is empty before new data is written to ONLY keep files that is needed. 
import os, shutil
def empty_folder():
  folder = 'pred_mask/'
  for filename in os.listdir(folder):
      file_path = os.path.join(folder, filename)
      try:
          if os.path.isfile(file_path) or os.path.islink(file_path):
              os.unlink(file_path)
          elif os.path.isdir(file_path):
              shutil.rmtree(file_path)
      except Exception as e:
          print('Failed to delete %s. Reason: %s' % (file_path, e))

  print('Delete Complete')

"""# Save the images to pred_mask folder"""

test_paths_full = tf.strings.substr(test_paths_full, 24,-5)
test_paths_full = tf.strings.regex_replace(test_paths_full,'.jpg','')

# Empty the google drive folder of any past masks and random masks/images
empty_folder()

# Saving the images to the pred_mask folder in google drive
for i in range(len(results)):
  tf.keras.preprocessing.image.save_img('./pred_mask/{}'.format(test_paths_full[i]),results[i], file_format='jpeg')
  # tf.io.write_file('pred_mask/',results)

# Renaming the files to get rid of the "b'" before the file names. Since Tf.strings modification returns it with b' before a string. 
import time
from tqdm.auto import tqdm

print('waiting for sleep timer...')
for i in tqdm(range(60)):
  time.sleep(.1)

print('Re-naming files')
collection = "pred_mask/"
for i, filename in tqdm(enumerate(os.listdir(collection))):
  time.sleep(.1)
  newName = filename[2:-1]
  # print(newName)
  # print(collection + 'test_mask_' + newName + '.jpg')
  os.rename(collection + filename, collection + 'test_mask_' + newName+ '.jpg')

"""# Creating a csv file based on the mask"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
from skimage.transform import resize
from skimage.io import imread
import sys
# %matplotlib inline

# encoding function
# based on the implementation: https://www.kaggle.com/rakhlin/fast-run-length-encoding-python/code
def rle_encoding(x):
  '''x: numpy array of shape (height, width), 1 - mask, 0 - background
  Returns run length as list
  '''
  dots = np.where(x.T.flatten()==1)[0] # .T sets Fortran order down-then-right
  run_lengths = []
  prev = -2
  for b in dots:
    if (b>prev+1): run_lengths.extend((b+1, 1))
    run_lengths[-1] += 1
    prev = b
  return run_lengths

from tqdm.auto import tqdm
import datetime

# (* update) the input_path using your folder path
input_path = 'pred_mask/'

# get a sorted list of all mask filenames in the folder
masks = [f for f in os.listdir(input_path) if f.endswith('.jpg')]
masks = sorted(masks, key=lambda s:int(s.split('_')[2].split('.')[0]))

# encode all masks
encodings = []
for i, file in tqdm(enumerate(masks), total=len(masks)):
  mask = imread(os.path.join(input_path, file))
  #img_size =10
  #mask = resize(mask, (img_size, img_size), mode='constant', preserve_range=True)
  mask = np.array(mask, dtype=np.uint8)
  mask = np.round(mask/255)
  encodings.append(rle_encoding(mask))

# (** update) the path where to save the submission csv file
sub = pd.DataFrame()
sub['ImageId'] = pd.Series(masks).apply(lambda x: os.path.splitext(x)[0])
sub['EncodedPixels'] = pd.Series(encodings).apply(lambda x: ' '.join(str(y) for y in x))
sub.to_csv(os.path.join('submission/', 'test_mask_preds_'+datetime.datetime.now().strftime("%H%M%S")+'.csv'), index=False)
sys.stdout.flush()