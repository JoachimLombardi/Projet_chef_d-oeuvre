from django import forms
from .models import Authors, Affiliations, Article


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


    def save_article_with_authors(self, author_affiliation_data, commit=True):
        article = self.save(commit=commit)
        for author_data in author_affiliation_data:
            author_name = author_data['author_name']
            affiliations = author_data['affiliations']
            # Check if the author already exists
            author, created = Authors.objects.get_or_create(name=author_name)
            # Clear existing affiliations to update
            author.affiliations.clear()
            # Process each affiliation for the author
            affiliation_list = [aff.strip() for aff in affiliations.split(';')]
            for aff_name in affiliation_list:
                # Check if the affiliation already exists
                affiliation, created = Affiliations.objects.get_or_create(name=aff_name)
                # Create the relationship in the intermediate table
                author.affiliations.add(affiliation)
            article.authors.add(author)


class AuthorForm(forms.Form):
    author_name = forms.CharField(label="Nom de l'auteur", widget=forms.TextInput(attrs={'class': 'form-control'}))
    affiliations = forms.CharField(
        label="Affiliations (séparées par des points-virgules)", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

AuthorAffiliationFormSet = forms.formset_factory(AuthorForm, extra=0)