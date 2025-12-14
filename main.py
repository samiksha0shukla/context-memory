# from dataclasses import dataclass
# from typing import List
# from datetime import datetime
# from pydantic import BaseModel

# @dataclass
# class MemoryObj:
#     id: str
#     text: str
#     category: str
#     embedding: List[float]
#     metadata: dict
#     created_at: datetime
#     updated_at: datetime


 

from db.database import create_table

if __name__ == "__main__":
    create_table()