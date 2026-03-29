"""Этап discovery: обход документов проекта."""

from __future__ import annotations

from src.modules.file_discovery import (
    DiscoveryService,
    FileDiscoveryPathNotFoundError,
    HashSidecarService,
)
from src.modules.file_discovery.models import DiscoveredDocument, DiscoveryConfig
from src.modules.file_extract import get_supported_extensions
from ..base import BasePipelineStage
from ...models import (
    PipelineContext,
    StageResult,
)


class DiscoveryStage(BasePipelineStage):
    """Обход документов: ``result`` — список DiscoveredDocument; ``payload`` — ``[found_count]``."""

    @property
    def stage_id(self) -> str:
        return "discovery"

    def run(self, context: PipelineContext, input_result: object) -> StageResult:
        _ = input_result
        context.logger.info("Discovery: scanning documents")
        documents = self._execute(context)
        found_count = len(documents)
        if context.cancel_event is not None and context.cancel_event.is_set():
            context.logger.info("Discovery: stopped")
            return StageResult.ok(documents, payload=[found_count])
        context.logger.info("Discovery: found %s files", found_count)
        return StageResult.ok(documents, payload=[found_count])

    def _execute(self, context: PipelineContext) -> list[DiscoveredDocument]:
        extensions = get_supported_extensions()
        if not extensions:
            extensions = {"*"}
        discovery_config = DiscoveryConfig(
            path=str(context.config.paths.docs),
            extensions=extensions,
            hash=True,
            recursive_search=context.config.discovery.get("recursive_search", False),
        )
        discovery_service = DiscoveryService()
        hash_sidecar_service = HashSidecarService()
        try:
            result = discovery_service.discover_files(
                discovery_config, cancel_event=context.cancel_event
            )
            if discovery_config.hash:
                hash_sidecar_service.ensure_hashes(
                    result, cancel_event=context.cancel_event
                )
        except FileDiscoveryPathNotFoundError:
            context.logger.warning("Discovery: docs directory not found")
            return []
        return result
