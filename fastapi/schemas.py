from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime 

class AffiliationsBase(BaseModel):
    name: str

class AffiliationsCreate(AffiliationsBase):
    pass

class AuthorsBase(BaseModel):
    name: str

class AuthorsCreate(AuthorsBase):
    pass

class ArticleBase(BaseModel):
    title_review: Optional[str] = None
    date: Optional[datetime] = None
    title: str
    abstract: Optional[str] = None
    pmid: Optional[int] = None
    doi: Optional[str] = None
    disclosure: Optional[str] = None
    mesh_terms: Optional[str] = None
    url: Optional[str] = None
    term: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class AuthorshipBase(BaseModel):
    id_article: int
    id_author: int
    id_affiliation: int

class AuthorshipCreate(AuthorshipBase):
    pass

class ArticleWithAuthors(ArticleBase):
    authors: List[AuthorsBase] = []
