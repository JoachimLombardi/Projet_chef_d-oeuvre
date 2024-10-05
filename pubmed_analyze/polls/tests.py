from django.test import TestCase
from django.urls import reverse
from .models import Article, Authors, Affiliations, Authorship

class ArticleListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Création d'une affiliation
        affiliation = Affiliations.objects.create(name='Affiliation Test')

        # Création d'un auteur
        author = Authors.objects.create(name='Author Test')

        # Création d'un article
        cls.article = Article.objects.create(  # Utilisez cls pour définir l'article comme attribut de classe
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
        # Effectuer une requête GET sur la vue de la liste d'articles
        response = self.client.get(reverse('article_list'))
        
        # Vérifiez que la réponse est réussie
        self.assertEqual(response.status_code, 200)
        
        # Vérifiez que le bon template est utilisé
        self.assertTemplateUsed(response, 'polls/article_list.html')  # Remplacez par le chemin de votre template

        # Vérifiez que le titre de l'article est présent dans la réponse
        self.assertContains(response, "Test Article")
        self.assertContains(response, "Review Title Test")
        self.assertContains(response, "13 janvier 2024")
        self.assertContains(response, "http://example.com/test-article")

        # Vérifiez que les auteurs et affiliations sont présents
        self.assertContains(response, "Author Test")
        self.assertContains(response, "Affiliation Test")

        # Vérifiez que les liens de modification et de suppression sont présents
        self.assertContains(response, reverse('update_article', args=[self.article.id]))  # Utilisez l'ID de l'article
        self.assertContains(response, reverse('delete_article', args=[self.article.id]))  # Utilisez l'ID de l'article
