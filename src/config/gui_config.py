from pydantic import BaseModel


class GuiConfig(BaseModel):

    def __str__(self):
        return self.model_dump_json(indent=4)

    @staticmethod
    def build(self):
        return GuiConfig()
