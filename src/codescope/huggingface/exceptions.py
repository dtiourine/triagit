class HuggingFaceClientError(Exception):
    pass


class ModelNotAccessibleError(HuggingFaceClientError):
    pass
