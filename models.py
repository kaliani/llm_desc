from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class MetadataItem(BaseModel):
    sub_question: str
    answer: str


class DataItem(BaseModel):
    Name: str = Field(description="First and Last Name")
    Position: str | None = Field(description="always returns the word empty")
    Country: str = Field(description="Country of origin")
    BirthDate: str = Field(description="Date of birth")
    Childhood: str = Field(description="Childhood information: for example, city of birth, secondary education")
    Education: str = Field(
        description="Education information: for example, higher education, years of study, specialty"
    )
    Career: str = Field(description="Career information: for example, positions, years of work, companies")
    PoliticalActivity: str = Field(
        description="Political activity information: for example, party, years of activity, positions"
    )
    Family: str = Field(description="Family information: for example, family, parents, brothers, sisters, children")
    ReturningSources: str = Field(description="always returns the word empty")
    PictureSource: str | None = Field(description="always returns the word empty")
    Citizenship: str | None = Field(description="always returns the word empty")
    PoliticalParty: str | None = Field(description="always returns the word empty")
    Facebook: list[str] = Field(description="always returns the word empty")
    Instagram: list[str] = Field(description="always returns the word empty")
    Twitter: list[str] = Field(description="always returns the word empty")


class PoliticanDocs(BaseModel):
    id: str
    wikidataid: str
    title: str
    type: int
    data: DataItem
    metadata: List[MetadataItem]
    createdAt: datetime
    updatedAt: datetime


class PoliticianRequest(BaseModel):
    name: str
    wikidataid: str
