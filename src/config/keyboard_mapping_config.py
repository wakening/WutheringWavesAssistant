from pydantic import BaseModel, Field

from src.util.keymouse_util import KEYBOARD_VK_MAPPING


class KeyboardMappingConfig(BaseModel):
    mapping: dict[str, int] = Field({})
    support_keys: dict[str, int] = Field(
        KEYBOARD_VK_MAPPING,
        title="支持的按键"
    )

    def is_support_key(self, key: str) -> bool:
        return key.upper() in self.support_keys

    def get_mapping_key(self, reset_key: str, src_key: str | int) -> int:
        return self.mapping.get(reset_key, src_key)
