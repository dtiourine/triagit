from huggingface_hub import HfApi
from huggingface_hub.errors import EntryNotFoundError, RepositoryNotFoundError


def is_accessible_model(model_id: str) -> bool:
    api = HfApi()
    try:
        api.model_info(model_id)
        return True
    except (RepositoryNotFoundError, EntryNotFoundError):
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
