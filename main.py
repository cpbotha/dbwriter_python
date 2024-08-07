# develop on this with:
# poetry env use 3.9
# poetry install
# poetry run uvicorn main:app --reload

# run in prod with something like:
# poetry run uvicorn main:app --workers 12 --log-level warning

from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, Column, DateTime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine, Field, Session, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# async_db (with postgres) gives around 30% more RPS than sync_db
DB = "postgres"
ASYNC_DB = True


# we need four models so that schema is correctly interpreted between database,
# POST and GET requests. Each of these has different optional / required fields.
# See https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/
class SampleBase(SQLModel):
    name: str
    # just datetime type by default will get you a timezone-less timestamp
    # so we have to pass in the Column definition with tz-capable DateTime type
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    # test field description. this only comes up in the schema it seems.
    v0: Optional[float] = Field(
        None, description="v0 is the first optional sensor value"
    )
    v1: Optional[float] = None


# table=True is passed to the parent __init__subclass__()
# https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__
class Sample(SampleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class SampleCreate(SampleBase):
    """Test docstring for SampleCreate"""

    pass


class SampleRead(SampleBase):
    id: int


if DB == "sqlite":
    db_path = Path(__file__).parent / "bleh.db"
    # disabling sqlite's same thread check because this is a toy, and I'm only
    # benchmarking reads, and in the meantime I've switched to postgresql.
    # https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
    # echo=True for developing, False otherwise
    if ASYNC_DB:
        aengine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
elif DB == "postgres":
    if ASYNC_DB:
        aengine = create_async_engine(
            "postgresql+asyncpg://dbwriter:blehbleh@localhost:5432/dbwriter_python"
        )
    else:
        engine = create_engine(
            "postgresql://dbwriter:blehbleh@localhost:5432/dbwriter_python"
        )

app = FastAPI()


@app.get("/")
async def APIRoot():
    """Root of the API"""
    return {"data": "Hello, World!"}


if ASYNC_DB:

    @app.on_event("startup")
    async def on_startup_async():
        print("ASYNC startup")
        async with aengine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    @app.get("/samples", response_model=list[SampleRead])
    async def get_samples_async():
        async with AsyncSession(aengine) as session:
            result = await session.execute(select(Sample))
            samples = result.scalars().all()
            return samples

    @app.post("/samples")
    async def add_sample_async(sample: SampleCreate):
        """Add a single sample to the database."""
        db_sample = Sample.from_orm(sample)
        async with AsyncSession(aengine) as session:
            session.add(db_sample)
            await session.commit()
            await session.refresh(db_sample)
            return db_sample

    @app.get("/samples/{sample_id}", response_model=SampleRead)
    async def get_sample_async(sample_id: int):
        """Retrieve a single sample from the database.

        ```python
        # code block rendered as verbatim
        v = 42
        process_val(v)
        ```
        """
        async with AsyncSession(aengine) as session:
            sample = await session.get(Sample, sample_id)
            if sample is None:
                raise HTTPException(
                    status_code=404, detail=f"sample with id {sample_id} not found"
                )
            return sample

else:
    # to be used as injected arg "session: Session = Depends(get_session)" in sync mode
    def get_session():
        with Session(engine) as session:
            yield session

    @app.on_event("startup")
    def on_startup():
        print("SYNC startup")
        SQLModel.metadata.create_all(engine)

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
        sample = session.get(Sample, sample_id)
        if sample is None:
            raise HTTPException(
                status_code=404, detail=f"sample with id {sample_id} not found"
            )
        return sample
