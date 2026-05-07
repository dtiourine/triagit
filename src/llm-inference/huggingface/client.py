from transformers import AutoModelForCausalLM, AutoTokenizer

from .exceptions import ModelNotAccessibleError
from .utils import is_accessible_model


class HuggingFaceClient:
    def __init__(self, model_id: str):
        if not is_accessible_model(model_id):
            raise ModelNotAccessibleError(
                f"Model {model_id} not found or requires permission to access"
            )

        self.model_id = model_id

        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype="auto", device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

    def generate(self, prompt: str, max_tokens: str, temperature: float) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        prompt_len = inputs["input_ids"].shape[1]
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
        )
        new_tokens = outputs[0][prompt_len:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)
