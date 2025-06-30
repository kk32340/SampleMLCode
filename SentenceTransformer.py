from sentence_transformers import SentenceTransformer, util

from sentence_transformers import SentenceTransformer
from huggingface_hub import snapshot_download

# Download model
model_path = snapshot_download("sentence-transformers/all-MiniLM-L6-v2")

model = SentenceTransformer(model_path)

# Encode two sentences
embedding1 = model.encode("my friend")
embedding2 = model.encode("my son")
print("test")
# Compute similarity
similarity = util.cos_sim(embedding1, embedding2)
print("Cosine similarity:", similarity.item())
