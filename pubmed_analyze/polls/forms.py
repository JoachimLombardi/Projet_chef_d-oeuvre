import pdb
from django import forms
from django.shortcuts import get_object_or_404
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
        updated_fields = False
        if article_id:
            article_initial = get_object_or_404(Article, id=article_id)
            Authorship.objects.filter(article=article_initial).all().delete()
        article_obj, created = Article.objects.update_or_create(
            id=article_id, 
            defaults={key: value for key, value in self.cleaned_data.items()})
        if not created:
            # pdb.set_trace() 
            for field, new_value in self.cleaned_data.items():
                current_value = getattr(article_initial, field, None)
                if current_value != new_value:
                    updated_fields = True
        existing_authors = {author.name: author for author in Authors.objects.all()}
        existing_affiliations = {affiliation.name: affiliation for affiliation in Affiliations.objects.all()}
        new_authors = []
        new_affiliations = []
        new_autorship = []
        author_in_form = set()
        affiliation_in_form = set()
        for author_data in author_affiliation_data:
            author_name = author_data.get('author_name')
            author_name_obj = Authors(name=author_name)
            if author_name not in existing_authors and author_name not in author_in_form:
                new_authors.append(author_name_obj)
                author_in_form.add(author_name)
            affiliations = author_data.get('affiliations')
            for affiliation in affiliations.split('|'):
                affiliation_obj = Affiliations(name=affiliation)
                if affiliation not in existing_affiliations and affiliation not in affiliation_in_form:
                    new_affiliations.append(affiliation_obj)
                    affiliation_in_form.add(affiliation)
        with transaction.atomic():
            if new_authors:
                Authors.objects.bulk_create(new_authors)
                existing_authors.update({author.name: author for author in Authors.objects.all()})
            if new_affiliations:
                Affiliations.objects.bulk_create(new_affiliations)
                existing_affiliations.update({affiliation.name: affiliation for affiliation in Affiliations.objects.all()})
        for author_data in author_affiliation_data:
            author_name = author_data.get('author_name')
            affiliations = author_data.get('affiliations')
            author_name_obj = existing_authors.get(author_name)
            for affiliation in affiliations.split('|'):
                affiliation_obj = existing_affiliations.get(affiliation)
                new_autorship.append(Authorship(article=article_obj, author=author_name_obj, affiliation=affiliation_obj))
        with transaction.atomic():
            if new_autorship:
                Authorship.objects.bulk_create(new_autorship)
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
        ('all', 'All'),
        ('multiple_sclerosis_2024', 'Multiple Sclerosis'),
        ('herpes_zoster_2024', 'Herpes Zoster'),
    ]

    LLM_CHOICE = [
        ("mistral", "mistal 7b"),
         ("llama3.2", "llama 3.2")
    ]

    query = forms.CharField(label="Poser une question", widget=forms.TextInput(attrs={'class': 'form-control'}))
    index_choice = forms.ChoiceField(choices=INDEX_CHOICE, label="Choisissez un index", 
                                   widget=forms.Select(attrs={'class': 'form-select'}), 
                                   required=True)
    llm_choice = forms.ChoiceField(choices=LLM_CHOICE, label="Choisissez un llm", 
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

    MODELS_GENERATION = [('mistrallite', 'Mistrallite'),
                         ('mistral-nemo', 'Mistral Némo'),
                         ('mistral', 'Mistral 7B'),
                         ('mixtral:8x7b', 'Mixtral 8x7B'),
                         ('mistral-small', 'Mistral small')]
    
    MODELS_EVALUATION = [('gpt-4o', 'GPT-4')]

    METHOD_CHOICES = [
        ('hand_made', 'Custom'),
        ('deep_eval', 'Deep Eval'),
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

    choose_eval_method = forms.ChoiceField(
        label="Choose Evaluation Method",
        choices=METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
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

class GeneForm(forms.Form):
    gene_name = forms.CharField(label="Recherche  un gène", widget=forms.TextInput(attrs={'class': 'form-control'}))
   
