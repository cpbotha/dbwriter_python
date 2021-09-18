# start this with:
# poetry install
# poetry run uvicorn main:app --reload

from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlmodel import create_engine, Field, Session, SQLModel

# we need multiple models so that schema is correctly interpreted between
# database, POST and GET, each of these sometimes with different optional /
# required fields. See
# https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/
class SampleBase(SQLModel):
    name: str
    timestamp: datetime
    v0: Optional[float] = None
    v1: Optional[float] = None

class Sample(SampleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class SampleCreate(SampleBase):
    pass

class SampleRead(SampleBase):
    id: int

db_path = Path(__file__).parent / "bleh.db"
engine = create_engine(f"sqlite:///{db_path}", echo=True)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/")
async def APIRoot():
    """Root of the API"""
    return {"data": "Hello, World!"}

@app.get("/samples", response_model=list[SampleRead])
def get_samples(session: Session = Depends(get_session)):
    result = session.execute(select(Sample))
    samples = result.scalars().all()
    return samples


@app.post("/samples")
def add_sample(sample: SampleCreate, session: Session = Depends(get_session)):
    db_sample = Sample.from_orm(sample)
    session.add(db_sample)
    session.commit()
    session.refresh(db_sample)
    return db_sample

@app.get("/samples/{sample_id}", response_model=SampleRead)
def read_item(sample_id: int, session: Session = Depends(get_session)):
    statement = select(Sample).where(Sample.id == sample_id)
    sample = session.exec(statement).first()
    if sample is None:
        raise HTTPException(status_code=404, detail=f"sample with id {sample_id} not found")
    return sample
