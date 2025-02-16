from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas  

app = FastAPI()

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.post("/authors/", response_model=schemas.AuthorsBase)
def create_author(author: schemas.AuthorsCreate, db: Session = Depends(get_db)):
    db_author = models.Authors(name=author.name)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


@app.post("/affiliations/", response_model=schemas.AffiliationsBase)
def create_affiliation(affiliation: schemas.AffiliationsCreate, db: Session = Depends(get_db)):
    db_affiliation = models.Affiliations(name=affiliation.name)
    db.add(db_affiliation)
    db.commit()
    db.refresh(db_affiliation)
    return db_affiliation


@app.post("/articles/", response_model=schemas.ArticleBase)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    db_article = models.Article(**article.model_dump())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


@app.post("/authorships/", response_model=schemas.AuthorshipBase)
def create_authorship(authorship: schemas.AuthorshipCreate, db: Session = Depends(get_db)):
    db_authorship = models.Authorship(**authorship.model_dump())
    db.add(db_authorship)
    db.commit()
    db.refresh(db_authorship)
    return db_authorship


@app.get("/articles/{article_id}", response_model=schemas.ArticleWithAuthors)
def get_article(article_id: int, db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id_article == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    authors = db.query(models.Authors).join(models.Authorship).filter(models.Authorship.id_article == article_id).all()
    article_with_authors = schemas.ArticleWithAuthors(**db_article.__dict__)
    article_with_authors.authors = [author.name for author in authors]
    return article_with_authors
