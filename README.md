Bibliotecas do python utilizadas:

import json
import os
import tkinter as tk
from tkinter import messagebox
from google import genai
from pydantic import BaseModel, Field
import threading

O JSON do cliente defini sua (base de dados).
Por conta do tempo, não pode ser totalmente customizável,
mas é possível modificála para criar diferentes tipos de clientes
