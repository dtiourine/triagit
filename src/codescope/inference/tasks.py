from celery.utils.log import get_task_logger
from src.llm_inference.exceptions import ModelNotAccessibleError, ModelNotFoundError
from src.llm_inference.service import LLMInferenceService
from src.worker import celery_app

logger = get_task_logger(__name__)

_service_cache: dict[str, LLMInferenceService] = {}


def _get_service(model_id: str) -> LLMInferenceService:
    if model_id not in _service_cache:
        logger.info(f"Loading model {model_id} into worker memory")
        _service_cache[model_id] = LLMInferenceService(model_id=model_id)
    return _service_cache[model_id]


@celery_app.task(
    bind=True,
    name="llm_inference.generate",
    autoretry_for=(ConnectionError,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def generate_text_task(
    self,
    model_id: str,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
) -> dict:
    try:
        service = _get_service(model_id)
        text = service.generate(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        return {"text": text, "model_id": model_id}
    except (ModelNotAccessibleError, ModelNotFoundError) as e:
        logger.warning(f"Task {self.request.id} failed permanently: {e}")
        raise
