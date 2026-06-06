from __future__ import annotations

from collections import defaultdict
from typing import Any


class TokenAligner:
    """Сопоставление токенов между двумя версиями текста."""

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    _semantic_model = None

    @classmethod
    def _load_semantic_model(cls):
        if cls._semantic_model is None:
            from sentence_transformers import SentenceTransformer

            cls._semantic_model = SentenceTransformer(cls.MODEL_NAME)
        return cls._semantic_model

    @staticmethod
    def _normalize_text(token: dict[str, Any]) -> str:
        text = token.get("lemma") or token.get("text")
        pos = token.get("pos")
        return f"{text} ({pos})" if pos else str(text)

    @classmethod
    def align_by_features(
        cls,
        source_tokens: list[dict],
        target_tokens: list[dict],
        use_semantic: bool = False,
        semantic_threshold: float = 0.65,
    ) -> list[dict]:
        """Выравнивание по нескольким стратегиям с опциональным семантическим слоем."""
        alignment: list[dict] = []
        target_exact = {
            (token["lemma"], token["pos"], token["idx"]): token["idx"]
            for token in target_tokens
        }
        fallback = defaultdict(list)
        for token in target_tokens:
            fallback[(token["lemma"], token["pos"])].append(token["idx"])

        used_target: set[int] = set()
        matched_source: set[int] = set()

        for src in source_tokens:
            exact_key = (src["lemma"], src["pos"], src["idx"])
            if exact_key in target_exact:
                target_idx = target_exact[exact_key]
                alignment.append({"source_idx": src["idx"], "target_idx": target_idx, "method": "exact", "score": 1.0})
                used_target.add(target_idx)
                matched_source.add(src["idx"])
                continue

            simple_key = (src["lemma"], src["pos"])
            candidates = [idx for idx in fallback.get(simple_key, []) if idx not in used_target]
            if candidates:
                target_idx = min(candidates, key=lambda idx: abs(idx - src["idx"]))
                alignment.append({"source_idx": src["idx"], "target_idx": target_idx, "method": "lemma_pos", "score": 1.0})
                used_target.add(target_idx)
                matched_source.add(src["idx"])

        if use_semantic:
            # Semantic matching for remaining tokens
            model = cls._load_semantic_model()
            remaining_source = [token for token in source_tokens if token["idx"] not in matched_source]
            remaining_target = [token for token in target_tokens if token["idx"] not in used_target]
            if remaining_source and remaining_target:
                source_texts = [cls._normalize_text(token) for token in remaining_source]
                target_texts = [cls._normalize_text(token) for token in remaining_target]
                source_emb = model.encode(source_texts, convert_to_tensor=True)
                target_emb = model.encode(target_texts, convert_to_tensor=True)

                scores = (source_emb @ target_emb.T).cpu().numpy()
                pairs = []
                for i, src in enumerate(remaining_source):
                    for j, tgt in enumerate(remaining_target):
                        score = float(scores[i][j])
                        if score >= semantic_threshold:
                            pairs.append((score, src["idx"], tgt["idx"]))
                pairs.sort(reverse=True, key=lambda item: item[0])
                used_source = set()
                for score, src_idx, tgt_idx in pairs:
                    if src_idx in used_source or tgt_idx in used_target:
                        continue
                    used_source.add(src_idx)
                    used_target.add(tgt_idx)
                    alignment.append({"source_idx": src_idx, "target_idx": tgt_idx, "method": "semantic", "score": score})
        return alignment
