# pip install accelerate
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b-it")
model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2b-it",
    device_map="auto",
    torch_dtype=torch.bfloat16
)

def gemma_ask(prompt):
    input_ids = tokenizer(prompt, return_tensors="pt").to("mps")

    outputs = model.generate(**input_ids ,max_new_tokens=100)
    return tokenizer.decode(outputs[0])