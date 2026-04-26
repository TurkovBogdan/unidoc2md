"""Цены input/output за 1M токенов из реестра моделей (для payload прогресса)."""


def resolve_llm_registry_prices(
    provider: str,
    model: str,
) -> tuple[float | None, float | None]:
    if not provider or not model:
        return None, None
    try:
        from src.modules.llm_models_registry import LLMModelManager

        rec = LLMModelManager().get_model(f"{provider}@{model}")
    except RuntimeError:
        return None, None
    if rec is None:
        return None, None
    return (
        LLMModelManager.optional_price_per_million(rec.get("price_input")),
        LLMModelManager.optional_price_per_million(rec.get("price_output")),
    )
