# forms.py
from django import forms
from .models import Article, Articles_authors_affiliations, Authors, Affiliations
from django.forms import inlineformset_factory


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Authors
        fields = '__all__'


class AffiliationForm(forms.ModelForm):
    affiliation = forms.CharField(widget=forms.Textarea, required=False)
    class Meta:
        model = Affiliations
        fields = '__all__'


class AuthorAffiliationForm(forms.ModelForm):
    author = forms.CharField(widget=forms.Textarea, required=False)
    class Meta:
        model = Articles_authors_affiliations
        fields = ['author', 'affiliation']


# Formset pour gérer plusieurs auteurs et affiliations liés à un article
AuteurAffiliationFormSet = inlineformset_factory(
    Article,  
    Articles_authors_affiliations, 
    form=AuthorAffiliationForm,  # Formulaire utilisé pour chaque entrée
    extra=1  # Nombre de formulaires vides à afficher
)
