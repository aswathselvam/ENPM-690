import numpy as np
import math
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import time 

class CMAC:
    def __init__(self, x, y, generalization=5, num_weights=35, test_size=0.3):
        self.x=x
        self.y=y
        self.generalization_factor=generalization
        self.min_input = np.min(x)
        self.max_input = np.max(x)
        self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(x, y, test_size=test_size, random_state=2)
        self.weights = np.ones(num_weights)
        self.num_weights = num_weights
        self.association_map = {}

    def plot(self,x,y):
        fig = plt.figure()
        ax1 = fig.add_subplot()
        ax1.plot(self.x, self.y, label=f'y=h(s)')

        idx_list = np.argsort(x)
        sorted_test_x = x[idx_list]
        d_sorted_predicted_y = [y[idx] for idx in idx_list]
        
        ax1.plot(sorted_test_x, d_sorted_predicted_y, 'x-', label='Model Inference')
        ax1.legend(loc='best')
        ax1.set(title=str(self.__class__.__name__), ylabel='Prediction',  xlabel='Input')
        plt.show()

class DiscreteCMAC(CMAC):
    def __init__(self, x, y, generalization, num_weights,test_size):
        CMAC.__init__(self, x, y, generalization, num_weights,test_size)
        self.AssociationMap()
   
    def AssociationMap(self):
        num_association_vectors = self.num_weights - self.generalization_factor
        for i in range(len(self.x)):
            if x[i] < self.min_input:
                association_index = 1
            elif x[i] > self.max_input:
                association_index = num_association_vectors - 1
            else:
                proportion_idx = (num_association_vectors - 2) * ((self.x[i] - self.min_input) / (self.max_input - self.min_input)) + 1
                association_index = proportion_idx
            self.association_map[self.x[i]] = int(math.floor(association_index)) 


    def Predict(self,x):
        self.predicted = []

        if not len(self.association_map)>0:
            self.AssociationMap()

        for i in range(len(x)):
            weight_idx = self.association_map[x[i]]

            # Sum the weights in activated cells
            prediction = np.sum(self.weights[weight_idx : weight_idx + self.generalization_factor])

            self.predicted.append(prediction)

        return self.predicted

    def Train(self, epochs = 100, learning_rate = 0.01):
        
        #reset the model
        self.weights = np.ones(self.num_weights)
        current_epoch = 0

        prev_err = 0
        error = 99999
        converged = False
        while current_epoch <= epochs and not converged:
            prev_err = error

            for i in range(len(self.train_x)):
                weight_index = self.association_map[self.train_x[i]]

                output = np.sum(self.weights[weight_index : weight_index + self.generalization_factor])
                error = self.train_y[i] - output
                correction = (learning_rate * error) / self.generalization_factor
                
                self.weights[weight_index : weight_index + self.generalization_factor] = \
                    [(self.weights[idx] + correction) \
                    for idx in range(weight_index, (weight_index + self.generalization_factor))]

            predictions = self.Predict(self.test_x)
            error = mean_squared_error(self.test_y, predictions)
            val_accuracy=1-error
            
            if val_accuracy<0:
                val_accuracy=0

            if np.abs(prev_err - error) < 0.000001:
                converged = True
                        
            current_epoch = current_epoch + 1
        print(f'Discrete CMAC: \n  Generalization Factor: {self.generalization_factor} \
        \n  Epoch: {current_epoch} \n  Accuracy: {val_accuracy * 100}%')



class ContinuousCMAC(CMAC):
    def __init__(self, x, y, generalization, num_weights,test_size):
        CMAC.__init__(self, x, y, generalization, num_weights,test_size)
        self.AssociationMap()

    def AssociationMap(self):     
        num_association_vectors = self.num_weights - self.generalization_factor

        for i in range(len(self.x)):
            if x[i] < self.min_input:
                association_index = 1
            elif x[i] > self.max_input:
                association_index = num_association_vectors - 1
            else:
                proportion_idx = (num_association_vectors - 2) * ((self.x[i] - self.min_input) / (self.max_input - self.min_input)) + 1
                association_index = proportion_idx

            low_index = int(math.floor(association_index))
            high_index = int(math.ceil(association_index))
            
            if low_index != high_index:
                self.association_map[x[i]] = (low_index, high_index)
            else:
                self.association_map[x[i]] = (low_index, 0)

    def Predict(self, x):
        self.predicted = []
        inputs = np.linspace(self.min_input, self.max_input, self.num_weights + 1 - self.generalization_factor)
        
        if not len(self.association_map)>0:
            self.AssociationMap()

        for i in range(len(x)):
            low_index = self.association_map[x[i]][0]
            high_index = self.association_map[x[i]][1]

            l_shared = np.abs(inputs[low_index] - x[i])
            r_shared = np.abs(inputs[high_index] - x[i])

            l_ratio = r_shared / (l_shared + r_shared)
            r_ratio = l_shared / (l_shared + r_shared)

            prediction = (l_ratio * np.sum(self.weights[low_index : low_index + self.generalization_factor])) + (r_ratio * np.sum(self.weights[high_index : high_index + self.generalization_factor]))

            self.predicted.append(prediction)

        return self.predicted

    def Train(self, epochs = 100, learning_rate = 0.01):
        self.weights = np.ones(self.num_weights)
        current_epoch = 0

        prev_err = 0
        current_err = 0
        inputs = np.linspace(self.min_input, self.max_input)
        converged = False
        while current_epoch <= epochs and not converged:
            prev_err = current_err

            for i in range(len(self.train_x)):
                low_index = self.association_map[self.train_x[i]][0]
                high_index = self.association_map[self.train_x[i]][1]

                l_shared = np.abs(inputs[low_index] - self.train_x[i])
                r_shared = np.abs(inputs[high_index] - self.train_x[i])

                l_ratio = r_shared / (l_shared + r_shared)
                r_ratio = l_shared / (l_shared + r_shared)

                output = (l_ratio * np.sum(self.weights[low_index : low_index + self.generalization_factor])) \
                     + (r_ratio * np.sum(self.weights[high_index : high_index + self.generalization_factor]))

                err = self.train_y[i] - output
                correction = (learning_rate * err) / self.generalization_factor

                self.weights[low_index : low_index + self.generalization_factor] = \
                    [(self.weights[idx] + correction) for idx in range(low_index, low_index + self.generalization_factor)]
                self.weights[high_index : high_index + self.generalization_factor] = \
                    [(self.weights[idx] + correction) for idx in range(high_index, high_index + self.generalization_factor)]

                predictions = self.Predict(self.test_x)
                error = mean_squared_error(self.test_y, predictions)
                val_accuracy=1-error

                # if val_accuracy<0:
                #     val_accuracy=0

                if np.abs(prev_err - current_err) < 0.000001:
                    converged = False
                
                current_epoch = current_epoch + 1
        print(f'Continuous CMAC: \n  Generalization Factor: {self.generalization_factor} \n  Epoch: {current_epoch} \n  Accuracy: {val_accuracy * 100}%')



class DiscreteRecurrentCMAC(CMAC):
    def __init__(self, x, y, generalization, num_weights,test_size):
        CMAC.__init__(self, x, y, generalization, num_weights,test_size)
        self.weights_state=np.ones(self.num_weights)
        self.AssociationMap()
        # print(self.association_map)
   
    def AssociationMap(self):
        num_association_vectors = self.num_weights - self.generalization_factor
        for i in range(len(self.x)):
            if x[i] < self.min_input:
                association_index = 1
            elif x[i] > self.max_input:
                association_index = num_association_vectors - 1
            else:
                proportion_idx = (num_association_vectors - 2) * ((self.x[i] - self.min_input) / (self.max_input - self.min_input)) + 1
                association_index = proportion_idx
            self.association_map[self.x[i]] = int(math.floor(association_index)) 


    def Predict(self,x):
        self.predicted = []

        if not len(self.association_map)>0:
            self.AssociationMap()

        feedback = x[0]
        for t in range(1,10):
            for i in range(len(x)):
                dist = 999
                for k in self.association_map.keys():
                    if abs(k-feedback) < dist:
                        feedback = k
                        dist = abs(k-feedback)
                        
                weight_idx = self.association_map[feedback]

                # Sum the weights in activated cells
                transition = np.sum(self.weights_state[weight_idx : weight_idx + self.generalization_factor])
                prediction = transition + np.sum(self.weights[weight_idx : weight_idx + self.generalization_factor])
                feedback = prediction
                self.predicted.append(prediction)

        return self.predicted

    def Train(self, epochs = 100, learning_rate = 0.01):
        
        #reset the model
        self.weights = np.ones(self.num_weights)
        self.weights_state = np.ones(self.num_weights)
        current_epoch = 0

        prev_err = 0
        error = 99999
        converged = False
        while current_epoch <= epochs and not converged:
            prev_err = error

            for i in range(1,len(self.x)-1):
                weight_index = self.association_map[self.x[i]]

                if(i==1):
                    weight_t_index = 0
                else:
                    weight_t_index = prev_t_op

                output = np.sum(self.weights[weight_index : weight_index + self.generalization_factor])
                output_transition = np.sum(self.weights_state[weight_t_index : weight_t_index + self.generalization_factor])
                error = self.y[i] - output
                prev_t_op = output - output_transition
                error_transition = self.y[i] - prev_t_op
                correction = (learning_rate * error) / self.generalization_factor
                correction_transition = (learning_rate * error_transition) / self.generalization_factor
                
                self.weights[weight_index : weight_index + self.generalization_factor] = \
                    [(self.weights[idx] + correction) \
                    for idx in range(weight_index, (weight_index + self.generalization_factor))]
                
                self.weights_state[weight_index : weight_index + self.generalization_factor] = \
                    [(self.weights[idx] + correction_transition) \
                    for idx in range(weight_index, (weight_index + self.generalization_factor))]

            # predictions = self.Predict(self.test_x)
            # error = mean_squared_error(self.test_y, predictions)
            error =0
            val_accuracy=1-error
            
            if val_accuracy<0:
                val_accuracy=0

            if np.abs(prev_err - error) < 0.000001:
                converged = False
                        
            current_epoch = current_epoch + 1
        print(f'Discrete CMAC: \n  Generalization Factor: {self.generalization_factor} \
        \n  Epoch: {current_epoch} \n  Accuracy: {val_accuracy * 100}%')




if __name__=='__main__':
    x = np.linspace(0, 10, 100)
    y = np.zeros(x.shape)
    for i in range(0,len(x)):
        if x[i]<1:
            y[i]=10
        elif x[i]<2:
            y[i]=9
        elif x[i]<3:
            y[i]=7
        elif x[i]<4:
            y[i]=5
        elif x[i]<5:
            y[i]=4
        elif x[i]<6:
            y[i]=4
        elif x[i]<7:
            y[i]=5
        elif x[i]<8:
            y[i]=6
        elif x[i]<9:
            y[i]=7
  
    generalization_factor = 2 
    num_weights = 35
    test_size =0.3

    dCMAC = DiscreteCMAC(x,y,generalization_factor, num_weights, test_size)    
    dCMAC.Train(1000)

    inp = dCMAC.test_x
    prediction = dCMAC.Predict(inp)
    dCMAC.plot(inp,prediction)
    

    cCMAC = ContinuousCMAC(x,y,generalization_factor, num_weights, test_size)    
    cCMAC.Train(5000)
    inp = cCMAC.test_x
    prediction = cCMAC.Predict(inp)
    cCMAC.plot(inp,prediction)

    # drCMAC = DiscreteRecurrentCMAC(x,y,generalization_factor, num_weights, test_size)    
    # drCMAC.Train(4)

    # inp = np.array([0])
    # prediction = drCMAC.Predict(inp)
    # inp = np.arange(len(prediction))
    # drCMAC.plot(inp,prediction)
    # # print(drCMAC.weights_state)