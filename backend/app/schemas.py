from pydantic import BaseModel, Field
from typing import List, Optional

class Point(BaseModel):
    x: float
    y: float

class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

class RotatedBox(BaseModel):
    cx: float
    cy: float
    w: float
    h: float
    angle: float

class DetectionItem(BaseModel):
    polygon: List[Point] = Field(default_factory=list)
    area: float
    bbox: BoundingBox
    rbox: RotatedBox
    touches_edge: bool

class DetectResponse(BaseModel):
    width: int
    height: int
    item: Optional[DetectionItem] = None
