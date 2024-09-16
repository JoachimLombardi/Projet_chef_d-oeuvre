from django import forms
from .models import Authors, Affiliations, Article, Articles_authors_affiliations


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'


    def save_article_with_authors(self, author_affiliation_data, commit=True):
            article = self.save(commit=commit)
            for author_data in author_affiliation_data:
                author_name = author_data['author_name']
                affiliations = author_data['affiliations']
                # Check if the author already exists
                author, created = Authors.objects.get_or_create(name=author_name)
                # Process each affiliation for the author
                affiliation_list = [aff.strip() for aff in affiliations.split(',')]
                for aff_name in affiliation_list:
                    # Check if the affiliation already exists
                    affiliation, created = Affiliations.objects.get_or_create(name=aff_name)
                    # Create the relationship in the intermediate table
                    Articles_authors_affiliations.objects.create(article=article, author=author, affiliation=affiliation)
            return article
    
class AuthorForm(forms.ModelForm):
    class Meta:
        model = Authors
        fields = '__all__'


class AffiliationForm(forms.ModelForm):
    class Meta:
        model = Affiliations
        fields = '__all__'


class AuthorAffiliationForm(forms.Form):
    author_name = forms.CharField(label='Nom de l\'auteur', widget=forms.TextInput(attrs={'class': 'form-control'}))
    affiliations = forms.CharField(label='Affiliations (séparées par des virgules)', widget=forms.Textarea(attrs={'class': 'form-control'}))
    

AuthorAffiliationFormSet = forms.formset_factory(AuthorAffiliationForm, extra=0)