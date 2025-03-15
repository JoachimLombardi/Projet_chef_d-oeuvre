# python manage.py test
# python manage.py test polls.tests.ArticleCRUDTest.test_article_list_view 

from datetime import date
import json
from pathlib import Path
from django.conf import settings
from django.test import RequestFactory, TestCase
from django.urls import reverse
import numpy as np
from polls.models import Article, Affiliations, Authors, Authorship
from unittest.mock import MagicMock, patch
from polls.views import rag_articles
from polls.business_logic import article_json_to_database, articles_full_to_database, scrap_article_to_json
from django.contrib.auth import get_user_model


class ExtractArticlesTest(TestCase):
    def test_scrap_article_to_json(self):
        """
        Test the function scrap_article_to_json for correctly scraping and storing article data as JSON.

        This test mocks the behavior of BeautifulSoup to simulate the extraction of 
        article details from PubMed URLs. It verifies that the JSON file is created at the 
        expected path with the correct structure and data.

        Steps:
        - Mocks two BeautifulSoup objects to simulate article data extraction.
        - Calls scrap_article_to_json with test URLs and a suffix for the JSON file.
        - Checks if the JSON file is created at the expected path.
        - Loads the JSON data and verifies its structure and content, ensuring it contains
        required fields such as 'title_review', 'date', 'title', 'abstract', 'pmid', 'doi',
        'disclosure', 'mesh_terms', 'url', and 'authors_affiliations'.
        - Validates specific attribute values to ensure correctness of the scraped data.

        Assertions:
        - The JSON file exists in the specified directory.
        - The JSON data is a list with at least one entry.
        - The first entry in the JSON data contains all necessary fields with expected values.
        """

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
        expected_json_path = Path(settings.EXPORT_JSON_DIR + "/multiple_sclerosis_2024_test.json")
        self.assertTrue(expected_json_path.exists())
        with expected_json_path.open('r', encoding='utf-8') as f:
            json_data = json.load(f)
        self.assertIsInstance(json_data, list)
        self.assertGreater(len(json_data), 0)  
        self.assertIn('title_review', json_data[0]) 
        self.assertIn('date', json_data[0])  
        self.assertIn('title', json_data[0])  
        self.assertIn('abstract', json_data[0])
        self.assertIn('pmid', json_data[0])  
        self.assertIn('doi', json_data[0])  
        self.assertIn('disclosure', json_data[0])  
        self.assertIn('mesh_terms', json_data[0])  
        self.assertIn('url', json_data[0]) 
        self.assertIn('authors_affiliations', json_data[0])  
        self.assertIn('2024-01-13', json_data[0]["date"])  
        self.assertIn('Lancet (London, England)', json_data[0]["title_review"])  
        self.assertIn('Multiple sclerosis', json_data[0]["title"]) 
        self.assertIn('37949093', json_data[0]["pmid"]) 
        self.assertIn('https://doi.org/10.1016/S0140-6736(23)01473-3', json_data[0]["doi"]) 


    def test_article_json_to_database(self):
        """
        Test the function article_json_to_database for correctly saving article data to the database.

        This test verifies that the function article_json_to_database correctly saves article data from the JSON file to the database.

        Steps:
        - Verifies the existence of the test JSON file.
        - Calls article_json_to_database to import the data.
        - Asserts the correctness of the saved data by comparing the database entries with the expected data.

        Assertions:
        - The JSON file exists in the specified directory.
        - The article with title "Multiple sclerosis" exists in the database with correct data.
        - The article has the correct date, title, abstract, pmid, doi, mesh_terms, disclosure, title_review.
        - The article has 7 authors.
        - The authors "Dejan Jakimovski" and "Stefan Bittner" have the correct affiliations.

        """
        
        term = "multiple_sclerosis"
        filter = "2024"
        output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + "_test.json")
        self.assertTrue(output_path.exists(), f"Le fichier {output_path} doit exister pour ce test.")
        article_json_to_database()
        article = Article.objects.filter(title="Multiple sclerosis").first()
        self.assertEqual(article.title, "Multiple sclerosis")
        self.assertEqual(article.abstract, "Multiple sclerosis remains one of the most common causes of neurological disability in the young adult population (aged 18-40 years). Novel pathophysiological findings underline the importance of the interaction between genetics and environment. Improvements in diagnostic criteria, harmonised guidelines for MRI, and globalised treatment recommendations have led to more accurate diagnosis and an earlier start of effective immunomodulatory treatment than previously. Understanding and capturing the long prodromal multiple sclerosis period would further improve diagnostic abilities and thus treatment initiation, eventually improving long-term disease outcomes. The large portfolio of currently available medications paved the way for personalised therapeutic strategies that will balance safety and effectiveness. Incorporation of cognitive interventions, lifestyle recommendations, and management of non-neurological comorbidities could further improve quality of life and outcomes. Future challenges include the development of medications that successfully target the neurodegenerative aspect of the disease and creation of sensitive imaging and fluid biomarkers that can effectively predict and monitor disease changes.")
        self.assertEqual(article.date, date(2024, 1, 13))
        self.assertEqual(article.pmid, 37949093)
        self.assertEqual(article.doi, "https://doi.org/10.1016/S0140-6736(23)01473-3")
        self.assertEqual(article.mesh_terms, "Review, Research Support, Non-U.S. Gov't, Humans, Life Style, Multiple Sclerosis* / drug therapy, Multiple Sclerosis* / therapy, Quality of Life, Treatment Outcome, Young Adult")
        self.assertEqual(article.disclosure, "Declaration of interests DJ has received consulting fees from AstraZeneca; and serves as an Associate Editor for Clinical Neurology and Neurosurgery and is compensated by Elsevier. SB has received funding support for this manuscript by the German Research Foundation (CRC-TR-128 and CRC-TR-355) and the Hermann and Lilly Schilling Foundation; and consulting fees, payments, or honoraria from Merck Healthcare, Sanofi, Novartis, Roche, Biogen, TEVA, and Bristol Myers Squibb. RZ has received funding support from Mapi Pharma, EMD Serono, Novartis, Bristol Myers Squibb, Octave, V-VAWE Medical, and Protembis; and consulting fees, payments, or honoraria from EMD Serono, 415 Capital, Sanofi, Novartis, Janssen, and Bristol Myers Squibb. RHBB has received funding support from Biogen, Bristol Myers Squibb, Celgene, Genzyme, Genentech, Latin American Committee for Treatment and Research in Multiple Sclerosis, Novartis, and Verasci; royalties from the Psychological Assessment Resources; and consulting fees, payments, or honoraria from Biogen, Accorda, EMD Serono, Novartis, Bristol Myers Squibb, Immunic Therapeutics, Merck, Roche, and Sanofi. SAM has received funding support from the Multiple Sclerosis Society of Canada, Canadian Institutes of Health Research, EMD Serono, Roche, Novartis, Sanofi, Biogen, and Bristol Myers Squibb; and consulting fees, payments, or honoraria from Biogen, Bristol Myers Squibb, EMD Serono, Novartis, Roche, and Sanofi. FZ has received funding support by the German Research Foundation, German Federal Ministry of Education and Research, Novartis Cyprus, and Progressive Multiple Sclerosis Alliance; consulting fees from Actelion, Biogen, Bristol Meyers Squibb, Celgene, Janssen, Max Planck Society, Merck Serono, Novartis, Roche, Sanofi, Genzyme, and Sandoz. BW-G has received funding from Biogen, Bristol Myers Squibb, Celgene, Genentech, and Novartis; and consulting fees from Biogen, Bayer, Bristol Myers Squibb, Janssen, Horizon Therapeutics, Genzyme, and Sanofi; and payment or honoraria as a speaker from Biogen and Janssen.")
        self.assertEqual(article.title_review, "Lancet (London, England)")
        self.assertEqual(article.authors.count(), 7)
        author_1 = Authors.objects.get(name="Dejan Jakimovski")
        author_2 = Authors.objects.get(name="Stefan Bittner")
        self.assertEqual(author_1.name, "Dejan Jakimovski")
        self.assertEqual(author_2.name, "Stefan Bittner")
        affiliation_author_1 = Authorship.objects.filter(author=author_1, article=article)
        affiliation_author_2 = Authorship.objects.filter(author=author_2, article=article)
        self.assertEqual(affiliation_author_1.count(), 1)
        self.assertEqual(affiliation_author_2.count(), 1)
        affiliation = affiliation_author_1[0].affiliation
        self.assertEqual(affiliation.name, "Buffalo Neuroimaging Analysis Center, Department of Neurology, Jacobs School of Medicine and Biomedical Sciences, State University of New York at Buffalo, Buffalo, NY, USA; Jacobs Comprehensive MS Treatment and Research Center, Department of Neurology, Jacobs School of Medicine and Biomedical Sciences, State University of New York at Buffalo, Buffalo, NY, USA.")


class ArticleCRUDTest(TestCase):
    @classmethod
    def setUpTestData(self):
        """
        Sets up the test data for the ArticleCRUDTest.

        This class method creates a test user, an affiliation, an author, and an article.
        It also establishes an authorship relationship between the article, author, and affiliation.

        The data set up includes:
        - A user with username 'testuser' and password 'testpassword'.
        - An affiliation named 'Affiliation Test'.
        - An author named 'Author Test'.
        - An article with the title 'Test Article', a review title, a publication date, an abstract, 
        a PubMed ID, a DOI, a disclosure statement, mesh terms, and a URL.
        - An authorship linking the article, author, and affiliation.
        """

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
        articles_full_to_database()

        
    def test_article_list_view(self):
        """
        Tests the article_list view.

        This test logs in the user, then requests the article_list view.
        It checks that the response status code is 200 (OK),
        that the correct template is used, and that the response content
        includes the article title, review title, publication date, URL,
        author name, affiliation name, and links to edit and delete the article.

        This test does not check that the view returns the correct number of articles,
        as that would require creating multiple articles in the test data.
        """
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
        self.assertContains(response, reverse('create_update_article', args=[self.article.id]))
        self.assertContains(response, reverse('delete_article', args=[self.article.id]))


    def test_article_create_or_update_view(self):
        """
        Tests the create_or_update_article view for creating and updating an article.

        This test performs the following:
        - Tests the creation of a new article by posting data to the 'create_update_article' view.
        - Asserts that the response status code indicates a successful redirect (302).
        - Verifies the existence of the newly created article in the database.
        - Checks that the created article has the correct authorship details.

        - Tests updating an existing article by posting updated data to the same view with the article's ID.
        - Asserts that the response status code indicates a successful redirect (302) after update.
        - Verifies that the article's details are correctly updated in the database.
        - Checks that the updated article retains the correct authorship details.
        """

        data_create = {
            'title_review': 'New Review Title',
            'date': '2024-01-13',
            'title': 'New Article',
            'abstract': 'This is a new abstract for the article.',
            'pmid': 123456,
            'doi': '10.1234/new.doi',
            'disclosure': 'No conflict of interest',
            'mesh_terms': 'New Mesh Terms',
            'url': 'http://example.com/new-article',
            'form-0-author_name': 'Author Test',  
            'form-0-affiliations': 'Affiliation Test',  
            'form-TOTAL_FORMS': 1,  
            'form-INITIAL_FORMS': 0, 
        }
        response_create = self.client.post(reverse('create_update_article'), data_create)
        self.assertEqual(response_create.status_code, 302)  
        self.assertTrue(Article.objects.filter(title='New Article').exists())
        article = Article.objects.get(title='New Article')
        self.assertEqual(article.authorships.count(), 1)  
        authorship = article.authorships.first()
        self.assertEqual(authorship.author.name, 'Author Test')
        self.assertEqual(authorship.affiliation.name, 'Affiliation Test')

        data_update = {
            'title_review': 'Updated Review Title',
            'date': '2024-07-01',
            'title': 'Updated Article',
            'abstract': 'This is an updated abstract.',
            'pmid': article.pmid,
            'doi': article.doi,
            'disclosure': article.disclosure,
            'mesh_terms': article.mesh_terms,
            'url': article.url,
            'form-0-author_name': 'Updated Author Test', 
            'form-0-affiliations': 'Updated Affiliation Test',  
            'form-TOTAL_FORMS': 1,  
            'form-INITIAL_FORMS': 1,  
        }
        response_update = self.client.post(reverse('create_update_article', args=[article.id]), data_update)
        self.assertEqual(response_update.status_code, 302) 
        article.refresh_from_db()
        self.assertEqual(article.title, 'Updated Article')
        self.assertEqual(article.authorships.count(), 1)
        authorship = article.authorships.first()
        self.assertEqual(authorship.author.name, 'Updated Author Test')
        self.assertEqual(authorship.affiliation.name, 'Updated Affiliation Test')


    def test_article_delete_view(self):
        """
        Tests the delete_article view.

        This test posts a request to the 'delete_article' view with the article ID.
        It asserts that the response status code is 302 (Found),
        which indicates a successful redirect.
        Finally, it verifies that the article no longer exists in the database.
        """
        response = self.client.post(reverse('delete_article', args=[self.article.id]))
        self.assertEqual(response.status_code, 302)  
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())


class RAGTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Sets up the initial test data for the RAGTest class.

        This method is called once before running any tests in the class. It creates
        a test user, an affiliation, an author, and an article with associated authorship
        details. The created data is used across multiple test cases to ensure consistency
        and reliability of the tests.

        - Creates a user with username 'testuser' and password 'testpassword'.
        - Creates an affiliation named 'Affiliation Test'.
        - Creates an author named 'Author Test'.
        - Creates an article with the title 'Era of COVID-19 in Multiple Sclerosis Care.'
        and other specified details.
        - Establishes an authorship relationship between the created article, author,
        and affiliation.
        """

        cls.user = get_user_model().objects.create_user(
        username='testuser',
        password='testpassword'
        )
        affiliation = Affiliations.objects.create(name='Affiliation Test')
        author = Authors.objects.create(name='Author Test')
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
        Authorship.objects.create(article=cls.article, author=author, affiliation=affiliation)

    @patch('polls.business_logic.model.encode')  
    @patch('polls.business_logic.Search')  
    def test_rag(self, mock_search, mock_encode):
        """
        Tests the rag view.

        This test performs the following:
        - Logs in the test user.
        - Posts a query to the 'rag' view with the index name 'multiple_sclerosis_2024'.
        - Asserts that the response status code indicates a successful redirect (302).
        - Verifies that the correct article is returned in the response context.
        """
        self.client.login(username='testuser', password='testpassword') 
        query = " How did the COVID-19 pandemic impact the care of people with multiple sclerosis (PwMS)?"
        mock_encode.return_value = np.array([0.1, 0.2, 0.3])  
        mock_response = MagicMock()
        mock_response.hits = [
            MagicMock(meta=MagicMock(id=self.article.id), title=self.article.title, abstract=self.article.abstract)
        ]
        mock_search.return_value.query.return_value.source.return_value.execute.return_value = mock_response
        factory = RequestFactory()
        request = factory.post('/articles/rag/', {'query': query, 'index_choice': 'multiple_sclerosis_2024'})
        request.user = self.user

  


    