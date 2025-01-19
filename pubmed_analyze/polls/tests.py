# python manage.py test
# python manage.py test polls.tests.ArticleCRUDTest.test_article_list_view 

from datetime import date
import json
from pathlib import Path
import unittest
from django.conf import settings
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.urls import reverse
import numpy as np
from polls.models import Article, Affiliations, Authors, Authorship
from unittest.mock import MagicMock, patch
from polls.views import rag_articles
from polls.business_logic import article_json_to_database, scrap_article_to_json
from django.contrib.auth import get_user_model


class ExtractArticlesTest(TestCase):
    def test_scrap_article_to_json(self):
        mock_soup_1 = MagicMock()
        mock_soup_1.select_one.side_effect = lambda x: {
            'button.journal-actions-trigger': MagicMock(title='Lancet (London, England)'),
        }.get(x, None) 
        mock_soup_2 = MagicMock()
        mock_soup_2.select_one.side_effect = lambda x: {
            'button.journal-actions-trigger': MagicMock(title= 'Medicine (Baltimore)'),
        }.get(x, None) 
        pubmed_url= ['https://pubmed.ncbi.nlm.nih.gov/37949093','https://pubmed.ncbi.nlm.nih.gov/38394496']
        scrap_article_to_json(url=pubmed_url, suffix_article="test")
        # Vérifiez que le fichier JSON a été créé
        expected_json_path = Path(settings.EXPORT_JSON_DIR + "/multiple_sclerosis_2024_test.json")
        self.assertTrue(expected_json_path.exists())
        # Charger le contenu du fichier JSON pour vérification
        with expected_json_path.open('r', encoding='utf-8') as f:
            json_data = json.load(f)
        # Vérifiez la structure des données JSON
        self.assertIsInstance(json_data, list)
        self.assertGreater(len(json_data), 0)  # Vérifiez qu'il y a des articles
        self.assertIn('title_review', json_data[0])  # Vérifiez que le champ title_review est présent
        self.assertIn('date', json_data[0])  # Vérifiez que le champ date est présent
        self.assertIn('title', json_data[0])  # Vérifiez que le champ title est présent
        self.assertIn('abstract', json_data[0])  # Vérifiez que le champ abstract est présent
        self.assertIn('pmid', json_data[0])  # Vérifiez que le champ pmid est présent
        self.assertIn('doi', json_data[0])  # Vérifiez que le champ doi est présent
        self.assertIn('disclosure', json_data[0])  # Vérifiez que le champ disclosure est présent
        self.assertIn('mesh_terms', json_data[0])  # Vérifiez que le champ mesh_terms est présent
        self.assertIn('url', json_data[0])  # Vérifiez que le champ url est présent
        self.assertIn('authors_affiliations', json_data[0])  # Vérifiez que le champ authors_affiliations est présent
        self.assertIn('2024-01-13', json_data[0]["date"])  # Vérifiez que le champ authors estzellé
        self.assertIn('Lancet (London, England)', json_data[0]["title_review"])  
        self.assertIn('Multiple sclerosis', json_data[0]["title"])  # Vérifiez que le champ affiliations estzellé
        self.assertIn('37949093', json_data[0]["pmid"]) 
        self.assertIn('https://doi.org/10.1016/S0140-6736(23)01473-3', json_data[0]["doi"]) 


    def test_article_json_to_database(self):
        # Chemin du fichier JSON de test
        term = "multiple_sclerosis"
        filter = "2024"
        output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + "_test.json")
        # Vérifier que le fichier JSON existe
        self.assertTrue(output_path.exists(), f"Le fichier {output_path} doit exister pour ce test.")
        # Appel direct de la fonction à tester (en utilisant le fichier réel)
        response = article_json_to_database()
        # Vérifie que l'article a été créé
        created_articles = Article.objects.filter(title="Multiple sclerosis")
        # Vérifie les détails de l'article
        article = created_articles[0]
        self.assertEqual(article.title, "Multiple sclerosis")
        self.assertEqual(article.abstract, "Multiple sclerosis remains one of the most common causes of neurological disability in the young adult population (aged 18-40 years). Novel pathophysiological findings underline the importance of the interaction between genetics and environment. Improvements in diagnostic criteria, harmonised guidelines for MRI, and globalised treatment recommendations have led to more accurate diagnosis and an earlier start of effective immunomodulatory treatment than previously. Understanding and capturing the long prodromal multiple sclerosis period would further improve diagnostic abilities and thus treatment initiation, eventually improving long-term disease outcomes. The large portfolio of currently available medications paved the way for personalised therapeutic strategies that will balance safety and effectiveness. Incorporation of cognitive interventions, lifestyle recommendations, and management of non-neurological comorbidities could further improve quality of life and outcomes. Future challenges include the development of medications that successfully target the neurodegenerative aspect of the disease and creation of sensitive imaging and fluid biomarkers that can effectively predict and monitor disease changes.")
        self.assertEqual(article.date, date(2024, 1, 13))
        self.assertEqual(article.pmid, 37949093)
        self.assertEqual(article.doi, "https://doi.org/10.1016/S0140-6736(23)01473-3")
        self.assertEqual(article.mesh_terms, "Review, Research Support, Non-U.S. Gov't, Humans, Life Style, Multiple Sclerosis* / drug therapy, Multiple Sclerosis* / therapy, Quality of Life, Treatment Outcome, Young Adult")
        self.assertEqual(article.disclosure, "Declaration of interests DJ has received consulting fees from AstraZeneca; and serves as an Associate Editor for Clinical Neurology and Neurosurgery and is compensated by Elsevier. SB has received funding support for this manuscript by the German Research Foundation (CRC-TR-128 and CRC-TR-355) and the Hermann and Lilly Schilling Foundation; and consulting fees, payments, or honoraria from Merck Healthcare, Sanofi, Novartis, Roche, Biogen, TEVA, and Bristol Myers Squibb. RZ has received funding support from Mapi Pharma, EMD Serono, Novartis, Bristol Myers Squibb, Octave, V-VAWE Medical, and Protembis; and consulting fees, payments, or honoraria from EMD Serono, 415 Capital, Sanofi, Novartis, Janssen, and Bristol Myers Squibb. RHBB has received funding support from Biogen, Bristol Myers Squibb, Celgene, Genzyme, Genentech, Latin American Committee for Treatment and Research in Multiple Sclerosis, Novartis, and Verasci; royalties from the Psychological Assessment Resources; and consulting fees, payments, or honoraria from Biogen, Accorda, EMD Serono, Novartis, Bristol Myers Squibb, Immunic Therapeutics, Merck, Roche, and Sanofi. SAM has received funding support from the Multiple Sclerosis Society of Canada, Canadian Institutes of Health Research, EMD Serono, Roche, Novartis, Sanofi, Biogen, and Bristol Myers Squibb; and consulting fees, payments, or honoraria from Biogen, Bristol Myers Squibb, EMD Serono, Novartis, Roche, and Sanofi. FZ has received funding support by the German Research Foundation, German Federal Ministry of Education and Research, Novartis Cyprus, and Progressive Multiple Sclerosis Alliance; consulting fees from Actelion, Biogen, Bristol Meyers Squibb, Celgene, Janssen, Max Planck Society, Merck Serono, Novartis, Roche, Sanofi, Genzyme, and Sandoz. BW-G has received funding from Biogen, Bristol Myers Squibb, Celgene, Genentech, and Novartis; and consulting fees from Biogen, Bayer, Bristol Myers Squibb, Janssen, Horizon Therapeutics, Genzyme, and Sanofi; and payment or honoraria as a speaker from Biogen and Janssen.")
        self.assertEqual(article.title_review, "Lancet (London, England)")
        # Compte le nombre d'auteurs pour un article
        self.assertEqual(article.authors.count(), 7)
        author_1 = Authors.objects.get(name="Dejan Jakimovski")
        author_2 = Authors.objects.get(name="Stefan Bittner")
        self.assertEqual(author_1.name, "Dejan Jakimovski")
        self.assertEqual(author_2.name, "Stefan Bittner")
        # Vérifie les affiliations
        affiliation_author_1 = Authorship.objects.filter(author=author_1, article=article)
        affiliation_author_2 = Authorship.objects.filter(author=author_2, article=article)
        self.assertEqual(affiliation_author_1.count(), 1)
        self.assertEqual(affiliation_author_2.count(), 1)
        # Check name of affiliation from authorship
        affiliation = affiliation_author_1[0].affiliation
        self.assertEqual(affiliation.name, "Buffalo Neuroimaging Analysis Center, Department of Neurology, Jacobs School of Medicine and Biomedical Sciences, State University of New York at Buffalo, Buffalo, NY, USA; Jacobs Comprehensive MS Treatment and Research Center, Department of Neurology, Jacobs School of Medicine and Biomedical Sciences, State University of New York at Buffalo, Buffalo, NY, USA.")
        # Vérifie que la réponse est correcte
        self.assertEqual(response.status_code, 200)
        self.assertIn("Article, authors and affiliations added to database with success.", response.content.decode())


class ArticleCRUDTest(TestCase):
    @classmethod
    def setUpTestData(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        affiliation = Affiliations.objects.create(name='Affiliation Test')
        author = Authors.objects.create(name='Author Test')
        self.article = Article.objects.create(
            title_review='Review Title Test',
            date='2024-01-13',
            title='Test Article',
            abstract='This is a test abstract for the article.',
            pmid=123456,
            doi='10.1234/test.doi',
            disclosure='No conflict of interest',
            mesh_terms='Test Mesh Terms',
            url='http://example.com/test-article',
        )
        Authorship.objects.create(article=self.article, author=author, affiliation=affiliation)


    def test_article_list_view(self):
        self.client.login(username='testuser', password='testpassword') 
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
            'date': '2024-01-13',
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
        cls.user = get_user_model().objects.create_user(
        username='testuser',
        password='testpassword'
        )
        affiliation = Affiliations.objects.create(name='Affiliation Test')
        author = Authors.objects.create(name='Author Test')

        # Create an article
        cls.article = Article.objects.create(
            title_review='Review Title Test',
            date='2024-01-13',
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

    @patch('polls.business_logic.model.encode')  # Mock the model used for encoding the query
    @patch('polls.business_logic.Search')  # Mock the Search class
    def test_rag(self, mock_search, mock_encode):
        self.client.login(username='testuser', password='testpassword') 
        # Sample query
        query = " How did the COVID-19 pandemic impact the care of people with multiple sclerosis (PwMS)?"
        mock_encode.return_value = np.array([0.1, 0.2, 0.3])  # Mock the encoded vector returned by the model
        # Create a mock response for the search
        mock_response = MagicMock()
        mock_response.hits = [
            MagicMock(meta=MagicMock(id=self.article.id), title=self.article.title, abstract=self.article.abstract)
        ]
        mock_search.return_value.query.return_value.source.return_value.execute.return_value = mock_response
        factory = RequestFactory()
        request = factory.post('/articles/rag/', {'query': query, 'index_choice': 'multiple_sclerosis_2024'})
        request.user = self.user
        response = rag_articles(request)
        self.assertEqual(response.status_code, 200)

  


    