# develop on this with:
# poetry install
# poetry run uvicorn main:app --reload

# run in prod with something like:
# poetry run uvicorn main:app --workers 12 --log-level warning

# async example: https://github.com/tiangolo/sqlmodel/issues/54

# example wrk2:
# ./wrk -t10 -c100 -d20s -R1000 http://localhost:8000/samples/1

from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
#from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine, Field, Session, SQLModel
#from sqlmodel.ext.asyncio.session import AsyncSession

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
# disabling sqlite's same thread check because this is a toy, and I'm only
# benchmarking reads.
# https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
# echo=True for developing, False otherwise
engine = create_engine(f"sqlite:///{db_path}", echo=False, connect_args={"check_same_thread": False})
# async:
#engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False, connect_args={"check_same_thread": False})

# to be used as injected arg "session: Session = Depends(get_session)"
def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # sync code
    SQLModel.metadata.create_all(engine)
    # ASYNC:
    # async with engine.begin() as conn:
    #     await conn.run_sync(SQLModel.metadata.create_all)    


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
def get_sample(sample_id: int, session: Session = Depends(get_session)):
    # async with AsyncSession(engine) as session:
        # sample = await session.get(Sample, sample_id)
    sample = session.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail=f"sample with id {sample_id} not found")
    return sample
