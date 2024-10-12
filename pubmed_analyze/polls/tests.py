# python manage.py test
# python manage.py test polls.tests.ArticleCRUDTest.test_article_list_view 

import json
import unittest
from django.test import TestCase
from django.urls import reverse
import numpy as np
from polls.models import Article, Affiliations, Authors, Authorship
from unittest.mock import MagicMock, patch
from polls.views import search_articles, rag_articles

class ArticleCRUDTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Création d'une affiliation
        affiliation = Affiliations.objects.create(name='Affiliation Test')

        # Création d'un auteur
        author = Authors.objects.create(name='Author Test')

        # Création d'un article
        cls.article = Article.objects.create(
            title_review='Review Title Test',
            date='2024-01-13 00:00:00+00:00',
            title='Test Article',
            abstract='This is a test abstract for the article.',
            pmid=123456,
            doi='10.1234/test.doi',
            disclosure='No conflict of interest',
            mesh_terms='Test Mesh Terms',
            url='http://example.com/test-article',
        )

        # Association de l'article avec l'auteur et l'affiliation
        Authorship.objects.create(article=cls.article, author=author, affiliation=affiliation)


    def test_article_list_view(self):
        # Test de la vue de la liste d'articles (READ)
        response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'polls/article_list.html')
        self.assertContains(response, "Test Article")
        self.assertContains(response, "Review Title Test")
        self.assertContains(response, "13 janvier 2024")
        self.assertContains(response, "http://example.com/test-article")
        self.assertContains(response, "Author Test")
        self.assertContains(response, "Affiliation Test")
        self.assertContains(response, reverse('update_article', args=[self.article.id]))
        self.assertContains(response, reverse('delete_article', args=[self.article.id]))


    def test_article_create_view(self):
        # Test de la création d'un nouvel article (CREATE)
        data = {
            'title_review': 'New Review Title',
            'date': '2024-01-13 00:00:00+00:00',
            'title': 'New Article',
            'abstract': 'This is a new abstract for the article.',
            'pmid': 123456,
            'doi': '10.1234/new.doi',
            'disclosure': 'No conflict of interest',
            'mesh_terms': 'New Mesh Terms',
            'url': 'http://example.com/new-article',
            'form-0-author_name': 'Author Test',  # Auteur
            'form-0-affiliations': 'Affiliation Test',  # Affiliations
            'form-TOTAL_FORMS': 1,  # Nombre total de formulaires dans le formset
            'form-INITIAL_FORMS': 0,  # Initial forms
        }
        response = self.client.post(reverse('create_article'), data)
        self.assertEqual(response.status_code, 302)  # Redirection spécelle de creation
        self.assertTrue(Article.objects.filter(title='New Article').exists())


    def test_article_update_view(self):
        # Test de la mise à jour d'un article (UPDATE)
        data = {
            'title_review': 'Updated Review Title',
            'date': '2024-07-01',
            'title': 'Updated Article',
            'abstract': 'This is an updated abstract.',
            'pmid': self.article.pmid,
            'doi': self.article.doi,
            'disclosure': self.article.disclosure,
            'mesh_terms': self.article.mesh_terms,
            'url': self.article.url,
            'form-0-author_name': 'Author Test',  # Auteur
            'form-0-affiliations': 'Affiliation Test',  # Affiliations
            'form-TOTAL_FORMS': 1,  # Nombre total de formulaires dans le formset
            'form-INITIAL_FORMS': 0,  # Initial forms
        }
        response = self.client.post(reverse('update_article', args=[self.article.id]), data)
        self.assertEqual(response.status_code, 302)  # Redirection après mise à jour
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Article')


    def test_article_delete_view(self):
        # Test de la suppression d'un article (DELETE)
        response = self.client.post(reverse('delete_article', args=[self.article.id]))
        self.assertEqual(response.status_code, 302)  # Redirection après suppression
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())


class RAGTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an affiliation
        affiliation = Affiliations.objects.create(name='Affiliation Test')

        # Create an author
        author = Authors.objects.create(name='Author Test')

        # Create an article
        cls.article = Article.objects.create(
            title_review='Review Title Test',
            date='2024-01-13 00:00:00+00:00',
            title='Era of COVID-19 in Multiple Sclerosis Care.',
            abstract='The unprecedented scope of the coronavirus disease 2019 (COVID-19) pandemic resulted in numerous disruptions to daily life, including for people with multiple sclerosis (PwMS). This article reviews how disruptions in multiple sclerosis (MS) care prompted innovations in delivery of care (eg, via telemedicine) and mobilized the global MS community to rapidly adopt safe and effective practices. We discuss how our understanding of the risks of COVID-19 in PwMS has evolved along with recommendations pertaining to disease-modifying therapies and vaccines. With lessons learned during the COVID-19 pandemic, we examine potential questions for future research in this new era of MS care.',
            pmid=123456,
            doi='10.1234/test.doi',
            disclosure='No conflict of interest',
            mesh_terms='Test Mesh Terms',
            url='http://example.com/test-article',
        )

        # Associate the article with the author and affiliation
        Authorship.objects.create(article=cls.article, author=author, affiliation=affiliation)

    @patch('polls.views.model.encode')  # Mock the model used for encoding the query
    @patch('polls.views.Search')  # Mock the Search class
    @patch('polls.views.ollama.chat')  # Mock the LLM chat function
    def test_rag(self, mock_chat, mock_search, mock_encode):
        # Sample query
        query = " How did the COVID-19 pandemic impact the care of people with multiple sclerosis (PwMS)?"
        mock_encode.return_value = np.array([0.1, 0.2, 0.3])  # Mock the encoded vector returned by the model
        
        # Create a mock response for the search
        mock_response = MagicMock()
        mock_response.hits = [
            MagicMock(meta=MagicMock(id=self.article.id), title=self.article.title, abstract=self.article.abstract)
        ]
        
        mock_search.return_value.query.return_value.source.return_value.execute.return_value = mock_response

        class Request:
            GET = {'query': query}

        request = Request()

        # Call the rag_articles function
        context = rag_articles(request)
  
        # Assertions for search results
        self.assertIn("Abstract n°1", context)  # Ensure that the context includes the abstract
        self.assertIn(self.article.title, context)  # Ensure the title is part of the context
        self.assertIn(self.article.abstract, context)  # Ensure the abstract is part of the context

if __name__ == '__main__':
    unittest.main()
  


    