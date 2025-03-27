from pydantic import BaseModel, Field

from src.config.app_config import AppConfig
from src.config.echo_config import EchoModel
from src.config.gui_config import GuiConfig
from src.config.keyboard_mapping_config import KeyboardMappingConfig


class Config(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    app: AppConfig = Field(default_factory=AppConfig.build, title="应用配置")
    echo: EchoModel = Field(default_factory=EchoModel.build, title="声骸词条配置",
                            description="配置声骸合成和锁定需要的词条")
    keyboard_mapping: KeyboardMappingConfig = Field(default_factory=KeyboardMappingConfig, title="游戏内按键映射")
    gui: GuiConfig = Field(default_factory=GuiConfig.build, title="图形用户界面配置")
