from django import forms
from .models import Authors, Affiliations, Article, Authorship
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title_review', 'date', 'title', 'abstract', 'pmid', 'doi', 'disclosure', 'mesh_terms', 'url']

    title_review = forms.CharField(
        label="Title of Review", 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date = forms.DateTimeField(
        label="Date of Publication",
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d']
    )
    title = forms.CharField(
        label="Title of Article",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    abstract = forms.CharField(
        label="Abstract",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    pmid = forms.IntegerField(
        label="PubMed ID", 
        required=False, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    doi = forms.CharField(
        label="DOI",
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    disclosure = forms.CharField(
        label="Disclosure",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    mesh_terms = forms.CharField(
        label="Mesh Terms",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    url = forms.CharField(
        label="URL",
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )


    def save_article_with_authors(self, author_affiliation_data, article_id=None):
        updated_fields = []
        article = None
        # Ouvrir une transaction atomique
        with transaction.atomic():
            if article_id is not None:
            # Vérifier si l'article existe déjà
                article = Article.objects.filter(id=article_id).first()
            if article:
                # Si l'article existe, mettez à jour ses champs si nécessaire
                for field, new_value in self.cleaned_data.items():
                    current_value = getattr(article, field)
                    if current_value != new_value:
                        setattr(article, field, new_value)
                        updated_fields.append((field, current_value, new_value))
                article.save()
                created = False
            else:
                # Si l'article n'existe pas, créez un nouvel article
                article, created = Article.objects.get_or_create(**self.cleaned_data)
            # Traiter les données des auteurs et de leurs affiliations
            for author_data in author_affiliation_data:
                author_name = author_data['author_name']
                affiliations = author_data['affiliations']
                # Vérifiez si l'auteur existe déjà
                author, author_created = Authors.objects.update_or_create(
                    name=author_name,
                    defaults={}  # Vous pouvez ajouter des valeurs par défaut si nécessaire
                )
                # Traitez les affiliations
                if affiliations:
                    affiliation_list = [aff.strip() for aff in affiliations.split('|')]
                else:
                    affiliation_list = []
                for aff_name in affiliation_list:
                    # Vérifiez si l'affiliation existe déjà
                    affiliation, aff_created = Affiliations.objects.update_or_create(
                        name=aff_name,
                        defaults={}  # Valeurs par défaut si nécessaire
                    )
                    # Créez ou mettez à jour l'instance Authorship
                    authorship, authorship_created = Authorship.objects.update_or_create(
                        article=article,
                        author=author,
                        affiliation=affiliation,
                        defaults={}
                    )
        return created, updated_fields


class AuthorForm(forms.Form):
    author_name = forms.CharField(label="Nom de l'auteur", widget=forms.TextInput(attrs={'class': 'form-control'}))
    affiliations = forms.CharField(
        label="Affiliations (séparées par des points)", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

AuthorAffiliationFormSet = forms.formset_factory(AuthorForm, extra=0)


class RAGForm(forms.Form):
    INDEX_CHOICE = [
        ('', 'All'),
        ('multiple_sclerosis_2024', 'Multiple Sclerosis'),
        ('herpes_zoster_2024', 'Herpes Zoster'),
    ]

    query = forms.CharField(label="Poser une question", widget=forms.TextInput(attrs={'class': 'form-control'}))
    index_choice = forms.ChoiceField(choices=INDEX_CHOICE, label="Choisissez un index", 
                                   widget=forms.Select(attrs={'class': 'form-select'}), 
                                   required=True)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    email = forms.EmailField(required=True, help_text="Requis. Veuillez entrer une adresse e-mail valide.")


    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    

class EvaluationForm(forms.Form):

    RESEARCH_TYPE_CHOICES = [
        ('hybrid', 'recherche hybride'),
        ('text', 'recherche par mot'),
        ('neural', 'recherche neuronale'),
    ]

    MODELS_GENERATION = [('mistral', 'Mistral 7B'),
              ('mistral-small', 'Mistral 22B'),
            ]
    
    MODELS_EVALUATION = [('mistral-small', 'Mistral 22B'),
                         ('gpt-4o', 'GPT-4')
                        ]

    research_type = forms.ChoiceField(
        label="Type de recherche",
        choices=RESEARCH_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}))

    model_generation = forms.ChoiceField(
        label="Modele de génération",
        choices=MODELS_GENERATION,
        widget=forms.Select(attrs={'class': 'form-select'}))
    
    model_evaluation = forms.ChoiceField(
        label="Modele d'évaluation",
        choices=MODELS_EVALUATION,
        widget=forms.Select(attrs={'class': 'form-select'}))
    
    number_of_results = forms.IntegerField(
        widget=forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 100}),
        label="Number of Results"
    )
    number_of_articles = forms.IntegerField(
        widget=forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 5000}),
        label="Number of Articles"
    )
    title_weight = forms.FloatField(
        widget=forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1}),
        label="Title Weight"
    )
    abstract_weight = forms.FloatField(
        widget=forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1}),
        label="Abstract Weight"
    )
    rank_scaling_factors = forms.FloatField(
        widget=forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 60, 'step': 1}),
        label="Rank Scaling Factors"
    )

    