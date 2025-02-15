import tensorflow as tf
from tensorflow.keras import layers

class sampling(layers.Layer):
    """Uses (z_mean, z_log_var) to sample z, the vector encoding the variables."""
    def call(self, inputs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon

class Encoder(layers.Layer):
    """Maps PD variables to a triplet (z_mean, z_log_var, z)."""
    def __init__(self,               
               intermediate_dim=50,
               input_dim=20,
               half_input=10,
               latent_dim=5,                                             
               name='encoder',
               **kwargs):
        super(Encoder, self).__init__(name=name, **kwargs)                       
        self.encoder_layer1 = layers.Dense(intermediate_dim)        
        self.encoder_active_layer1 = layers.LeakyReLU(name="encoder_leakyrelu_1")
        self.encoder_layer2 = layers.Dense(input_dim)
        self.encoder_active_layer2 = layers.LeakyReLU(name="encoder_activ_layer_2")
        self.encoder_layer3 = layers.Dense(input_dim)
        self.encoder_active_layer3 = layers.LeakyReLU(name="encoder_activ_layer_3")    
        self.encoder_layer4 = layers.Dense(input_dim)
        self.encoder_active_layer4 = layers.LeakyReLU(name="encoder_activ_layer_4")    
        self.encoder_layer5 = layers.Dense(half_input) 
        self.encoder_active_layer5 = layers.LeakyReLU(name="encoder_activ_layer_5")
        self.dense_mean = layers.Dense(latent_dim)
        self.dense_log_var = layers.Dense(latent_dim)
        self.sampling = sampling()

    def call(self, inputs):
        xl1 = self.encoder_layer1(inputs)
        xl1_active = self.encoder_active_layer1(xl1)        
        xl2 = self.encoder_layer2(xl1_active)        
        xl2_active = self.encoder_active_layer2(xl2)
        xl3 = self.encoder_layer3(xl2_active)        
        xl3_active = self.encoder_active_layer3(xl3)
        xl4=self.encoder_layer4(xl3_active)
        xl4_active=self.encoder_active_layer4(xl4)
        xl5=self.encoder_layer5(xl4_active)        
        xl5_active=self.encoder_active_layer5(xl5)
        z_mean = self.dense_mean(xl5_active)
        z_log_var = self.dense_log_var(xl5_active)
        z = self.sampling((z_mean, z_log_var))
        return z_mean, z_log_var, z


class Decoder(layers.Layer):
    """Converts z, the encoded vector, back into a readable list of variables."""

    def __init__(self,
           half_input=10,
           input_dim=20,
           intermediate_dim=50,
           original_dim=14,
           name='decoder',
               **kwargs):
        super(Decoder, self).__init__(name=name, **kwargs)
        self.decoder_layer1 = layers.Dense(half_input)        
        self.decoder_active_layer1 = layers.LeakyReLU(name="decoder_leakyrelu_1")
        self.decoder_layer2 = layers.Dense(input_dim)                
        self.decoder_active_layer2 = layers.LeakyReLU(name="decoder_leakyrelu_2")    
        self.decoder_layer3 = layers.Dense(input_dim)
        self.decoder_active_layer3 = layers.LeakyReLU(name="decoder_leakyrelu_3")
        self.decoder_layer4 = layers.Dense(input_dim)
        self.decoder_active_layer4 = layers.LeakyReLU(name="decoder_leakyrelu_4")
        self.decoder_layer5 = layers.Dense(intermediate_dim)
        self.decoder_active_layer5 = layers.LeakyReLU(name="decoder_leakyrelu_5")        
        self.dense_output = layers.Dense(original_dim)
        self.decoder_active_output = layers.LeakyReLU(name="decoder_leakyrelu_output")

    def call(self, inputs):
        layer1 = self.decoder_layer1(inputs)        
        active_layer1= self.decoder_active_layer1(layer1)
        layer2=self.decoder_layer2(active_layer1)        
        active_layer2=self.decoder_active_layer2(layer2)
        layer3=self.decoder_layer3(active_layer2)    
        active_layer3=self.decoder_active_layer3(layer3)
        layer4=self.decoder_layer4(active_layer3)        
        active_layer4=self.decoder_active_layer4(layer4)
        layer5=self.decoder_layer5(active_layer4)        
        active_layer5=self.decoder_active_layer5(layer5)
        output =self.dense_output(active_layer5)
        return self.decoder_active_output(output)

class VariationalAutoEncoder(tf.keras.Model):
    """Combines the encoder and decoder into an end-to-end model for training."""

    def __init__(self,
               original_dim,               
               intermediate_dim=50,
               input_dim=20,
               half_input=10,
               latent_dim=5,
               name='autoencoder',
               **kwargs):
        super(VariationalAutoEncoder, self).__init__(name=name, **kwargs)
        self.original_dim = original_dim
        self.encoder = Encoder(
               intermediate_dim=intermediate_dim,
               input_dim=input_dim,
               half_input=half_input,
               latent_dim=latent_dim)
        self.decoder = Decoder(
           half_input=half_input,
           input_dim=input_dim,
           intermediate_dim=intermediate_dim,
           original_dim=original_dim)                        
    def call(self, inputs):
        # self._set_inputs(inputs)
        z_mean, z_log_var, z = self.encoder(inputs)
        reconstructed = self.decoder(z)
        # Add KL divergence regularization loss.
        kl_loss = - 0.5 * tf.reduce_mean(
            z_log_var - tf.square(z_mean) - tf.exp(z_log_var) + 1)
        kl_loss= kl_loss/1000000.
        self.add_loss(kl_loss)
        return reconstructed

class LatentSpace(tf.keras.Model):
    """Combines the encoder and decoder into an end-to-end model for training."""
    def __init__(self,
               intermediate_dim=50,
               input_dim=20,
               half_input=10,
               latent_dim=5,  
               name='latentspace',
               **kwargs):
        super(LatentSpace, self).__init__(name=name, **kwargs)        
        self.encoder = Encoder(
               intermediate_dim=intermediate_dim,
               input_dim=input_dim,
               half_input=half_input,
               latent_dim=latent_dim)

    def call(self, inputs):
        # self._set_inputs(inputs)
        z_mean, z_log_var, z = self.encoder(inputs)
        return z