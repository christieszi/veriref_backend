import transformers
import torch

model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

def llama_ask_with_assumption(assumption, question):
    pipeline = transformers.pipeline(
        "text-generation",
        model=model_id,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="auto",
    )

    messages = [
        {"role": "system", "content": f"You are a chatbot who knows that {assumption}"},
        {"role": "user", "content": f"Is it true that {question}"},
    ]

    outputs = pipeline(
        messages,
        max_new_tokens=256,
    )
    return outputs[0]["generated_text"][-1]

def llama_instruct_ask(prompt):

    # Load Llama 3 model from Hugging Face
    llama3_model = transformers.pipeline("text-generation", model="meta-llama/Meta-Llama-3.1-8B-Instruct")

    # Generate text using the Llama 3 model
    generated_text = llama3_model(prompt, max_length=50, do_sample=True)

    # Print the generated text
    return generated_text[0]['generated_text']

def llama_ask(prompt):

    # Load Llama 3 model from Hugging Face
    llama3_model = transformers.pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B")

    # Generate text using the Llama 3 model
    generated_text = llama3_model(prompt, max_length=50, do_sample=True)

    # Print the generated text
    return generated_text[0]['generated_text']
