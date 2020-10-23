#!/usr/bin/env python
# coding: utf-8

from numpy import load
from numpy import zeros
from numpy import ones
from numpy.random import randint
from keras.optimizers import Adam
from keras.initializers import RandomNormal
from keras.models import Model
from keras.models import Input
from keras.layers import Conv2D
from keras.layers import Conv2DTranspose
from keras.layers import LeakyReLU
from keras.layers import Activation
from keras.layers import Concatenate
from keras.layers import Dropout
from keras.layers import BatchNormalization
from keras.layers import LeakyReLU
from matplotlib import pyplot
import random
def define_discriminator(image_shape):
    init = RandomNormal(stddev=0.02)
    in_src_image = Input(shape=image_shape)
    in_target_image = Input(shape=image_shape)
    merged = Concatenate()([in_src_image, in_target_image])
    d = Conv2D(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(merged)
    d = LeakyReLU(alpha=0.2)(d)
    d = Conv2D(128, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(d)
    d = BatchNormalization()(d)
    d = LeakyReLU(alpha=0.2)(d)
    d = Conv2D(256, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(d)
    d = BatchNormalization()(d)
    d = LeakyReLU(alpha=0.2)(d)
    d = Conv2D(512, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(d)
    d = BatchNormalization()(d)
    d = LeakyReLU(alpha=0.2)(d)
    d = Conv2D(512, (4,4), padding='same', kernel_initializer=init)(d)
    d = BatchNormalization()(d)
    d = LeakyReLU(alpha=0.2)(d)
    d = Conv2D(1, (4,4), padding='same', kernel_initializer=init)(d)
    
    patch_out = Activation('sigmoid')(d)
    model = Model([in_src_image, in_target_image], patch_out)
    opt = Adam(lr=0.0002, beta_1=0.5)
    model.compile(loss='binary_crossentropy', optimizer=opt, loss_weights=[0.5])
    return model
def define_encoder_block(layer_in, n_filters, batchnorm=True):
    init = RandomNormal(stddev=0.02)
    
    g = Conv2D(n_filters, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(layer_in)
    if batchnorm:
        g = BatchNormalization()(g, training=True)
    g = LeakyReLU(alpha=0.2)(g)
    return g

# define a decoder block
def decoder_block(layer_in, skip_in, n_filters, dropout=True):
    init = RandomNormal(stddev=0.02)
    g = Conv2DTranspose(n_filters, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(layer_in)
    g = BatchNormalization()(g, training=True)
    if dropout:
        g = Dropout(0.5)(g, training=True)
    g = Concatenate()([g, skip_in])
    g = Activation('relu')(g)
    return g

# define the standalone generator model
def define_generator(image_shape=(512,1024,3)):
    init = RandomNormal(stddev=0.02)
    in_image = Input(shape=image_shape)
    e1 = define_encoder_block(in_image, 64, batchnorm=False)
    e2 = define_encoder_block(e1, 128)
    e3 = define_encoder_block(e2, 256)
    e4 = define_encoder_block(e3, 512)
    e5 = define_encoder_block(e4, 512)
    e6 = define_encoder_block(e5, 512)
    e7 = define_encoder_block(e6, 512)
    b = Conv2D(512, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(e7)
    b = Activation('relu')(b)
    d1 = decoder_block(b, e7, 512)
    d2 = decoder_block(d1, e6, 512)
    d3 = decoder_block(d2, e5, 512)
    d4 = decoder_block(d3, e4, 512, dropout=False)
    d5 = decoder_block(d4, e3, 256, dropout=False)
    d6 = decoder_block(d5, e2, 128, dropout=False)
    d7 = decoder_block(d6, e1, 64, dropout=False)
    # output
    g = Conv2DTranspose(3, (4,4), strides=(2,2), padding='same', kernel_initializer=init)(d7)
    out_image = Activation('tanh')(g)
    
    model = Model(in_image, out_image)
    return model
def define_gan(g_model, d_model, image_shape):
    d_model.trainable = False
    in_src = Input(shape=image_shape)
    gen_out = g_model(in_src)
    dis_out = d_model([in_src, gen_out])
    model = Model(in_src, [dis_out, gen_out])
    opt = Adam(lr=0.0002, beta_1=0.5)
    model.compile(loss=['binary_crossentropy', 'mae'], optimizer=opt, loss_weights=[1,100])
    return model

def generate_real_samples(dataset, n_samples, patch_shape):
    trainA, trainB = dataset
    ix = randint(0, trainA.shape[0], n_samples)
    X1, X2 = trainA[ix], trainB[ix]
    y = ones((n_samples, patch_shape, patch_shape, 1))
    return [X1, X2], y
def generate_fake_samples(g_model, samples, patch_shape):
    X = g_model.predict(samples)
    y = zeros((len(X), patch_shape, patch_shape, 1))
    return X, y
def summarize_performance(step, g_model, dataset, n_samples=3):
    [X_realA, X_realB], _ = generate_real_samples(dataset, n_samples, 1)
    X_fakeB, _ = generate_fake_samples(g_model, X_realA, 1)
    X_realA = (X_realA + 1) / 2.0
    X_realB = (X_realB + 1) / 2.0
    X_fakeB = (X_fakeB + 1) / 2.0
    fig = pyplot.figure(figsize=(30,30))
    for i in range(n_samples):
        pyplot.subplot(3, n_samples, 1 + i)
        pyplot.axis('off')
        pyplot.imshow(X_realA[i])
    #fig = pyplot.figure(figsize=(30,30))
    for i in range(n_samples):
        pyplot.subplot(3, n_samples, 1 + n_samples + i)
        pyplot.axis('off')
        pyplot.imshow(X_fakeB[i])
    #fig = pyplot.figure(figsize=(30,30))
    for i in range(n_samples):
        pyplot.subplot(3, n_samples, 1 + n_samples*2 + i)
        pyplot.axis('off')
        pyplot.imshow(X_realB[i])
    
    # save plot to file
    filename1 = 'plot_%06d.png' % (step+1)
    pyplot.savefig(filename1)
    pyplot.close()
    # save the generator model
    filename2 = 'model_%06d.h5' % (step+1)
    g_model.save(filename2)
    print('>Saved: %s and %s' % (filename1, filename2))
def train(d_model, g_model, gan_model, x_data,y_data, n_epochs=500, n_batch=1):
    n_patch = d_model.output_shape[1]
    trainA = x_data
    trainB = y_data
    bat_per_epo = int(len(trainA) / n_batch)
    n_steps = bat_per_epo * n_epochs
    dataset = [a,b]
    for i in range(n_steps):
        #[X_realA, X_realB], y_real = generate_real_samples(dataset, n_batch, n_patch)
        X_realA = np.zeros((1,512,512,3))
        #X_realA[0] = x_data[i]
        X_realB = np.zeros((1,512,512,3))
        #X_realB[0] = y_data[i]
        for j in range(4): 
            if j==0:
                randomx = random.randint(0,512-64)
                randomy = random.randint(0,512-64)
                cropA = x_data[i][randomx:randomx+64,randomy:randomy+64,:]
                cropA_512 = np.zeros((512,512,3))
                cropA_512[224:224+64,224:224+64] = cropA
                cropB = y_data[i][randomx:randomx+64,randomy:randomy+64,:]
                cropB_512 = np.zeros((512,512,3))
                cropB_512[224:224+64,224:224+64] = cropB
            if j==1:
                randomx = random.randint(0,512-128)
                randomy = random.randint(0,512-128)
                cropA =  x_data[i][randomx:randomx+128,randomy:randomy+128,:]
                cropA_512 = np.zeros((512,512,3))
                cropA_512[192:192+128,192:192+128] = cropA
                cropB = y_data[i][randomx:randomx+128,randomy:randomy+128,:]
                cropB_512 = np.zeros((512,512,3))
                cropB_512[192:192+128,192:192+128]  = cropB
            if j==2 :
                randomx = random.randint(0,512-256)
                randomy = random.randint(0,512-256)
                cropA =  x_data[i][randomx:randomx+256,randomy:randomy+256,:]
                cropA_512 = np.zeros((512,512,3))
                cropA_512[128:128+256,128:128+256] = cropA
                cropB = y_data[i][randomx:randomx+256,randomy:randomy+256,:]
                cropB_512 = np.zeros((512,512,3))
                cropB_512[128:128+256,128:128+256] = cropB
            if j==3:
                cropA_512 = x_data[i]
                cropB_512 = y_data[i]
            
            X_realA[0] = cropA_512
            X_realB[0] = cropB_512
            y_real = np.ones((1,32,32,1))
            X_fakeB, y_fake = generate_fake_samples(g_model, X_realA, n_patch)
            y_fake = np.zeros((1,32,32,1))
            #print(X_realA.shape)
            #print(X_fakeB.shape)
            d_loss1 = d_model.train_on_batch([X_realA, X_fakeB], y_fake)
            d_loss2 = d_model.train_on_batch([X_realA, X_realB], y_real)

            g_loss, _, _ = gan_model.train_on_batch(X_realA, [y_real, X_realB])
        print('>%d, d1[%.3f] d2[%.3f] g[%.3f]' % (i+1, d_loss1, d_loss2, g_loss))
        # summarize model performance
        if (i+1) % (5)==0: #(bat_per_epo * 10) == 0:
            summarize_performance(i, g_model, dataset)
