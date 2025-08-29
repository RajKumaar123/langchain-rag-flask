"""
BLEU and sacreBLEU evaluation utilities.
"""
import nltk
import sacrebleu
from typing import Dict

# Ensure punkt is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def bleu_nltk(candidate: str, reference: str) -> float:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    ref_tokens = nltk.word_tokenize(reference)
    cand_tokens = nltk.word_tokenize(candidate)
    smoothie = SmoothingFunction().method1
    score = sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smoothie)
    return float(score)

def bleu_sacre(candidate: str, reference: str) -> float:
    return float(sacrebleu.corpus_bleu([candidate], [[reference]]).score)

def evaluate_pair(candidate: str, reference: str) -> Dict[str, float]:
    return {"bleu_nltk": bleu_nltk(candidate, reference), "bleu_sacre": bleu_sacre(candidate, reference)}
