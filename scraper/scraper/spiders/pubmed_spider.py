#scrapy shell 'https://pubmed.ncbi.nlm.nih.gov/29717108/'

import scrapy

class PubmedSpider(scrapy.Spider):
    name = 'pubmed_spider'
    allowed_domains = ['pubmed.ncbi.nlm.nih.gov']
    start_urls = ['https://pubmed.ncbi.nlm.nih.gov/29717108/']
 
    def parse(self, response):
        # Extract authors names
        author_section = response.css('inline-authors')
        if author_section:
            authors = author_section.xpath('.//a[@class="full-name"]/text()').getall()
            author_names = [author.strip() for author in authors if author.strip()]
            print("Authors:", author_names)
        else:
            print("Aucun élément 'auteur' trouvé")

        # Extract affiliations
        affilations_section = response.xpath('//div[@class="affiliations"]')
        if affilations_section:
            affiliations_blocks = affilations_section.xpath('.//li/text()').getall()
            affiliations_names = list(set([affiliation.strip() for affiliation in affiliations_blocks if affiliation.strip()]))
            print("Affiliations:", affiliations_names)
        else:
            print("Aucun élément 'affiliation' trouvé")

        # Extract abstract
        abs_block = response.xpath('//div[@class="abstract-content"]')
        if abs_block:
            p_abs = abs_block.xpath('.//p/text()').get().strip()
            print("Abstract:", p_abs)
        else:
            print("Aucun élément 'abstract' trouvé")

        # Extract title
        title_block = response.xpath('//h1[@class="heading-title"]/text()').get()
        if title_block:
            p_tit = title_block.strip()
            print("Title:", p_tit)
        else:
            print("Aucun élément 'titre' trouvé")

        # Extract DOI
        doi_section = response.xpath('//span[@class="identifier doi"]')
        doi_block = doi_section.xpath('.//a[@class="id-link"]/text()').get()
        if doi_block:
            p_doi = doi_block.strip()
            print("DOI:", p_doi)
        else:
            print("Aucun élément 'doi' trouvé")

        # Extract journal
        journal_block = response.xpath('//button[@id="full-view-journal-trigger"]/text()').get()
        if journal_block:
            p_journal = journal_block.strip()
            print("Journal:", p_journal)
        else:
            print("Aucun élément 'journal' trouvé")

        # Extract references
        ref_block = response.xpath('//span[@class="cit"]/text()').get()
        if ref_block:
            p_ref = ref_block.strip()
            print("References:", p_ref)
        else:
            print("Aucun élément 'ref' trouvé")
