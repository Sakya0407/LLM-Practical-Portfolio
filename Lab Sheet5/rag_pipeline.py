# Lab 5 - terminal chat
from rag_core import answer
while True:
    q = input("\nAsk a university question (or exit): ")
    if q.strip().lower() == "exit": break
    a, s = answer(q); print("\nAnswer:", a, "\nSources:", ", ".join(s))
