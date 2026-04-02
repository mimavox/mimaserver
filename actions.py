from pydantic import BaseModel, ConfigDict, model_validator

class Actions(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    left: bool = False
    right: bool = False
    forward: bool = False
    backward: bool = False
    jump: bool = False

    _exclusive_fields = ('left', 'right', 'forward', 'backward', 'jump')

    def __setattr__(self, name, value):
        if name in self._exclusive_fields:
            v = bool(value)
            if v:
                # Turn off all others
                for f in self._exclusive_fields:
                    if f != name:
                        super().__setattr__(f, False)
            return super().__setattr__(name, v)
        return super().__setattr__(name, value)

    @model_validator(mode='after')
    def _enforce_exclusive_on_init(self):
        # Ensure only one True after construction
        trues = [f for f in self._exclusive_fields if getattr(self, f)]
        if len(trues) > 1:
            keep = trues[0]
            for f in self._exclusive_fields:
                object.__setattr__(self, f, f == keep)
        return self
    
'''
response = Actions()
response.left = True
print(response) => Only left is set to true
response.right = True
print(response) => Only right is set to true
'''