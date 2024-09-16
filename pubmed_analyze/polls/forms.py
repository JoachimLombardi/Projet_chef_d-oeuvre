from django import forms
from .models import Authors, Affiliations, Article, Articles_authors_affiliations


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'


# Formulaire combiné pour gérer les auteurs et leurs affiliations
class AuthorAffiliationForm(forms.Form):
    author_name = forms.CharField(label='Nom de l\'auteur', widget=forms.TextInput(attrs={'class': 'form-control'}))
    affiliations = forms.CharField(label='Affiliations', widget=forms.Textarea(attrs={'class': 'form-control'}))


AuthorAffiliationFormSet = forms.formset_factory(AuthorAffiliationForm, extra=0)