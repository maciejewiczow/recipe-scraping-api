from datetime import datetime
from typing import Annotated
from pydantic import PlainSerializer


SerializableDatetime = Annotated[datetime, PlainSerializer(lambda d: d.isoformat())]
