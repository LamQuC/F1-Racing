
# NO USE !!

import yaml
import os

# Đường dẫn đến file settings.yaml
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'settings.yaml')

def load_config():
    with open(CONFIG_PATH, 'r') as file:
        return yaml.safe_load(file)

settings = load_config()