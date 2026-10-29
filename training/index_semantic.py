"""Index approved reference photos with locally installed licensed CLIP weights.
Install PyTorch/Transformers and set RELIV_SEMANTIC_MODEL_DIR first.
Does not train a model or measure accuracy. Users still confirm candidates.
"""
import json
from app.semantic_retrieval import update_embedding_index
if __name__=='__main__':print(json.dumps(update_embedding_index(),indent=2))
