# pip install accelerate

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
set_seed(1234)

# identify which checkpoint we want, this is the repository on huggingface
# that we'll pull the model from,
model_checkpoint = "google/gemma-7b-it"

# load in the tokenizer,
# just in case you aren't familiar with llms the tokenizer takes the raw text
# and converts it into a vector that can be processed by our model,
# so basically it's a converter to convert english into numbers for our model
# to compute on
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)


# load the model using torch.bfloat16 to take up less space on the gpu
#model = AutoModelForCausalLM.from_pretrained(model_checkpoint, torch_dtype=torch.bfloat16, device_map="cuda")


# load the model in it's default torch.float32 datatype, be sure to identify
# the device map as cuda to tell huggingface to put the model on the gpu
# you could still run it on the cpu, but it will be SLOW,
model = AutoModelForCausalLM.from_pretrained(model_checkpoint, device_map="mps")

# create a completion prompt that leaves plenty of room for the model to generate
# new text
prompt = "Dr.Pepper is the best soda because"
# convert our prompt to tokens and send it to the gpu.
token_inputs = tokenizer(prompt, return_tensors="pt").to('mps')
# just to see what the tokens look like for our prompt, we'll print them
token_outputs = model.generate(input_ids=token_inputs['input_ids'], max_new_tokens=150, do_sample=True, temperature=0.5)
# since this is exploratory we'll decode special tokens as well. for this prompt
# it will be the beginning <bos> token and the ending <eos> tokens.
decoded_output = tokenizer.decode(token_outputs[0], skip_special_tokens=False)
print(decoded_output)