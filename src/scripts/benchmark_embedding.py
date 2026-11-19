import sys
import time

sys.path.insert(0, "src")

from rag.config import FASTEMBED_CACHE_DIR
from fastembed import TextEmbedding


MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def rss():
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 2)


print(f"RSS inicial: {rss()} MB")

inicio = time.time()

modelo = TextEmbedding(
    model_name=MODEL,
    cache_dir=FASTEMBED_CACHE_DIR,
)

print(f"RSS após carregar modelo: {rss()} MB")
print(f"Tempo de carregamento: {time.time() - inicio:.2f}s")

inicio = time.time()

vetores = list(modelo.embed([
    "Como funciona a pesca comercial em Pernambuco?",
    "Quais são os principais equipamentos utilizados na pesca?",
    "Como funciona a cadeia de distribuição de pescado?",
]))

print(f"RSS após inferência: {rss()} MB")
print(f"Tempo de inferência: {time.time() - inicio:.2f}s")
print(f"Quantidade de vetores: {len(vetores)}")
print(f"Dimensão: {len(vetores[0])}")
