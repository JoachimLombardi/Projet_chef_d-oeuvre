from django.test import TestCase
from django.urls import reverse
from polls.models import Article, Affiliations, Authors, Authorship

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
            'date': '2024-06-01',
            'title': 'New Article',
            'abstract': 'This is a new test abstract for the article.',
            'pmid': 654321,
            'doi': '10.6543/test.doi.new',
            'disclosure': 'No conflict of interest',
            'mesh_terms': 'New Test Mesh Terms',
            'url': 'http://example.com/new-article',
        }
        response = self.client.post(reverse('create_article'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après création
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
