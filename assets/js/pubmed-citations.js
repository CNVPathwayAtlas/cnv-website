/**
 * Fetches PubMed citation data using NCBI E-utilities API and displays Harvard-style citations.
 */
(function() {
  'use strict';

  const NCBI_API_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils';

  /**
   * Format authors in Harvard style
   * For 3+ authors, use "FirstAuthor et al."
   */
  function formatAuthorsHarvard(authors) {
    if (!authors || authors.length === 0) {
      return 'Unknown';
    }

    if (authors.length === 1) {
      return authors[0];
    }

    if (authors.length === 2) {
      return authors[0] + ' and ' + authors[1];
    }

    // 3 or more authors: use "et al."
    return authors[0] + ' <em>et al.</em>';
  }

  /**
   * Extract year from PubMed date string
   */
  function extractYear(dateStr) {
    if (!dateStr) return 'n.d.';
    const match = dateStr.match(/\d{4}/);
    return match ? match[0] : 'n.d.';
  }

  /**
   * Format a citation in Harvard style from PubMed data
   */
  function formatHarvardCitation(article) {
    const authorList = article.AuthorList;
    let authors = [];
    
    if (authorList && authorList.Author) {
      const authorArray = Array.isArray(authorList.Author) 
        ? authorList.Author 
        : [authorList.Author];
      
      authors = authorArray.map(author => {
        if (author.CollectiveName) {
          return author.CollectiveName;
        }
        const lastName = author.LastName || '';
        const initials = author.Initials || '';
        return initials ? `${lastName}, ${initials.split('').join('.')}` : lastName;
      }).filter(Boolean);
    }

    const formattedAuthors = formatAuthorsHarvard(authors);
    
    // Get publication date
    const pubDate = article.Journal?.JournalIssue?.PubDate;
    let year = 'n.d.';
    if (pubDate) {
      year = pubDate.Year || extractYear(pubDate.MedlineDate) || 'n.d.';
    }

    const title = article.ArticleTitle || 'Untitled';
    const journal = article.Journal?.Title || article.Journal?.ISOAbbreviation || '';
    const volume = article.Journal?.JournalIssue?.Volume || '';
    const issue = article.Journal?.JournalIssue?.Issue || '';
    const pagination = article.Pagination?.MedlinePgn || '';

    let citation = `${formattedAuthors} (${year}) '${title}'`;
    
    if (journal) {
      citation += `, <em>${journal}</em>`;
      if (volume) {
        citation += `, ${volume}`;
        if (issue) {
          citation += `(${issue})`;
        }
      }
      if (pagination) {
        citation += `, pp. ${pagination}`;
      }
    }
    
    citation += '.';
    return citation;
  }

  /**
   * Fetch citation data for a PubMed ID using NCBI E-utilities
   */
  async function fetchPubMedCitation(pmid) {
    try {
      const url = `${NCBI_API_BASE}/efetch.fcgi?db=pubmed&id=${pmid}&retmode=xml`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const xmlText = await response.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xmlText, 'text/xml');

      const article = xmlDoc.querySelector('PubmedArticle MedlineCitation Article');
      if (!article) {
        throw new Error('Article not found');
      }

      // Parse XML to structured data
      const articleData = {
        ArticleTitle: article.querySelector('ArticleTitle')?.textContent || '',
        AuthorList: parseAuthors(article.querySelector('AuthorList')),
        Journal: parseJournal(article.querySelector('Journal')),
        Pagination: {
          MedlinePgn: article.querySelector('Pagination MedlinePgn')?.textContent || ''
        }
      };

      return {
        success: true,
        citation: formatHarvardCitation(articleData)
      };
    } catch (error) {
      console.error(`Error fetching citation for PMID ${pmid}:`, error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Parse authors from XML
   */
  function parseAuthors(authorList) {
    if (!authorList) return { Author: [] };
    
    const authors = authorList.querySelectorAll('Author');
    const authorArray = Array.from(authors).map(author => ({
      LastName: author.querySelector('LastName')?.textContent || '',
      Initials: author.querySelector('Initials')?.textContent || '',
      CollectiveName: author.querySelector('CollectiveName')?.textContent || ''
    }));

    return { Author: authorArray };
  }

  /**
   * Parse journal info from XML
   */
  function parseJournal(journal) {
    if (!journal) return {};
    
    const journalIssue = journal.querySelector('JournalIssue');
    const pubDate = journalIssue?.querySelector('PubDate');

    return {
      Title: journal.querySelector('Title')?.textContent || '',
      ISOAbbreviation: journal.querySelector('ISOAbbreviation')?.textContent || '',
      JournalIssue: {
        Volume: journalIssue?.querySelector('Volume')?.textContent || '',
        Issue: journalIssue?.querySelector('Issue')?.textContent || '',
        PubDate: {
          Year: pubDate?.querySelector('Year')?.textContent || '',
          MedlineDate: pubDate?.querySelector('MedlineDate')?.textContent || ''
        }
      }
    };
  }

  /**
   * Initialize citations for all PubMed IDs on the page
   */
  async function initCitations() {
    const citationItems = document.querySelectorAll('[data-pubmed-id]');
    
    if (citationItems.length === 0) {
      return;
    }

    // Process citations sequentially to avoid rate limiting
    for (const item of citationItems) {
      const pmid = item.getAttribute('data-pubmed-id');
      const citationContainer = item.querySelector('.citation-text');
      const loadingIndicator = item.querySelector('.citation-loading');
      
      if (!citationContainer) continue;

      try {
        const result = await fetchPubMedCitation(pmid);
        
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
        
        if (result.success) {
          citationContainer.innerHTML = result.citation;
          citationContainer.style.display = 'block';
        } else {
          citationContainer.innerHTML = `<span class="citation-error">Unable to load citation</span>`;
          citationContainer.style.display = 'block';
        }
      } catch (error) {
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
        citationContainer.innerHTML = `<span class="citation-error">Unable to load citation</span>`;
        citationContainer.style.display = 'block';
      }

      // Small delay between requests to be nice to NCBI servers
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCitations);
  } else {
    initCitations();
  }
})();
