"""Табы экрана настроек проекта."""

from src.gui.screens.project.discovery_settings_tab import DiscoverySettingsTab
from src.gui.screens.project.extract_settings_tab import ExtractSettingsTab
from src.gui.screens.project.image_processing_settings_tab import ImageProcessingSettingsTab
from src.gui.screens.project.markdown_generation_settings_tab import MarkdownGenerationSettingsTab
from src.gui.screens.project.pipeline_settings_tab import PipelineSettingsTab
from src.gui.screens.project.tagging_settings_tab import TaggingSettingsTab

__all__ = [
    "DiscoverySettingsTab",
    "ExtractSettingsTab",
    "ImageProcessingSettingsTab",
    "MarkdownGenerationSettingsTab",
    "PipelineSettingsTab",
    "TaggingSettingsTab",
]
