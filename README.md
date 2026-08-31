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

Sobre Chave API:
  Não pude deixar a minha chave API pessoal pois esse repositório tem que ser público e não seria seguro.
  Caso queira testar, adicione uma chave API de um projeto do google AI studio.
  Esse código utiliza apenas o modelo Gemini 3.5 Flash Lite, que tem 500 interações grátis por dia.

  Alternativamente, mande um email para mim:
  thiagolmbalaguer@gmail.com ou thiagolmbalaguer@usp.br
  pedindo a minha chave API
