# uvicorn app:app --reload

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Définir la base
Base = declarative_base()

# Configurer la connexion à la base de données (utilisez l'URL de votre base de données)
DATABASE_URL = "sqlite:///./test.db"  # Exemple avec SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modèles SQLAlchemy

class Affiliations(Base):
    __tablename__ = 'affiliations'

    id_affiliation = Column(Integer, primary_key=True, index=True)
    name = Column(Text, index=True)

class Authors(Base):
    __tablename__ = 'authors'

    id_author = Column(Integer, primary_key=True, index=True)
    name = Column(String(2000), index=True)

class Article(Base):
    __tablename__ = 'articles'

    id_article = Column(Integer, primary_key=True, index=True)
    title_review = Column(String(2000))
    date = Column(Date)
    title = Column(String(2000))
    abstract = Column(Text)
    pmid = Column(Integer)
    doi = Column(String(200))
    disclosure = Column(Text)
    mesh_terms = Column(Text)
    url = Column(String(200))
    term = Column(String(200))

class Authorship(Base):
    __tablename__ = 'authorships'

    id_authorship = Column(Integer, primary_key=True, index=True)
    id_article = Column(Integer, ForeignKey('articles.id_article'))
    id_author = Column(Integer, ForeignKey('authors.id_author'))
    id_affiliation = Column(Integer, ForeignKey('affiliations.id_affiliation'))

    article = relationship("Article", back_populates="authorships")
    author = relationship("Authors", back_populates="authorships")
    affiliation = relationship("Affiliations", back_populates="authorships")

Article.authorships = relationship("Authorship", back_populates="article")
Authors.authorships = relationship("Authorship", back_populates="author")
Affiliations.authorships = relationship("Authorship", back_populates="affiliation")
