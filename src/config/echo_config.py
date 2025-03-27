# -*- coding: utf-8 -*-
"""
@software: PyCharm
@file: echo.py
@time: 2024/6/20 下午10:14
@author RoseRin0
"""
from pydantic import BaseModel, Field

# 定义通用属性列表
common_attributes = ["攻击", "防御", "生命"]
special_attributes_cost3 = ["共鸣效率", "冷凝伤害加成", "热熔伤害加成", "导电伤害加成", "气动伤害加成", "衍射伤害加成",
                            "湮灭伤害加成"]
special_attributes_cost4 = ["治疗效果加成", "暴击", "暴击伤害"]


class EchoModel(BaseModel):
    echoSetName: list[str] = Field(
        [
            "凝夜白霜", "熔山裂谷", "彻空冥雷", "啸谷长风", "浮星祛暗", "沉日劫明", "隐世回光", "轻云出月", "不绝余音",
            "凌冽决断之心", "此间永驻之光", "幽夜隐匿之帷", "高天共奏之曲", "无惧浪涛之勇",
        ],
        title="声骸套装名称"
    )
    echoSetNameReg: list[str] = Field(
        [
            "凝夜白霜", "熔山裂谷", "彻空冥雷", "啸谷长风", "浮星祛暗", "沉日劫明", "隐世回光", "轻云出月", "不绝余音",
            "凌冽决断之心", "此间永驻之光", "幽夜隐匿?之帷?", "高天共奏之曲", "无惧浪涛之勇",
        ],
        title="声骸套装名称，正则，防止有些生僻字识别不准"
    )
    echoCost: list[str] = Field(
        [
            "1", "3", "4",
        ],
        title="声骸Cost数量"
    )
    echoCost1MainStatus: list[str] = Field(
        common_attributes,
        title="1Cost声骸主属性",
    )
    echoCost3MainStatus: list[str] = Field(
        common_attributes + special_attributes_cost3,
        title="3Cost声骸主属性",
    )
    echoCost4MainStatus: list[str] = Field(
        common_attributes + special_attributes_cost4,
        title="4Cost声骸主属性",
    )

    def __str__(self):
        return self.model_dump_json(indent=4)

    @staticmethod
    def build():
        return EchoModel()
