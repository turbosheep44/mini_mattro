from pdqn_agent import HIDDEN_LAYERS
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

HIDDEN_LAYERS = [256, 128]


class QValueModel(nn.Module):
    def __init__(self, input_size,  output_size, device):
        super().__init__()
        self.device = device

        # create layers
        self.layers = nn.ModuleList()
        self.layers.append(nn.Linear(input_size, HIDDEN_LAYERS[0]).to(self.device))
        for i in range(1, len(HIDDEN_LAYERS)):
            self.layers.append(nn.Linear(HIDDEN_LAYERS[i - 1], HIDDEN_LAYERS[i]).to(self.device))
        self.layers.append(nn.Linear(HIDDEN_LAYERS[-1], output_size).to(self.device))

    def forward(self, x):
        for layer in self.layers:
            x = F.relu(layer(x))
        return x

    def save(self, file_name='model.pth'):
        model_folder_path = './model'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)
