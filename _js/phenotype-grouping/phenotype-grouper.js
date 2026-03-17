/**
 * PhenotypeGrouper - Groups phenotypes by their top-level HPO categories
 *
 * Uses the pre-generated hpo_categories.json (v2 format) to look up
 * category assignments for phenotypes.
 */
var PhenotypeGrouper = (function() {
  var cacheData = null;
  var cachePromise = null;

  /**
   * Load the HPO categories data from JSON file
   */
  function loadCache() {
    if (cachePromise) return cachePromise;

    var basePath = document.querySelector('meta[name="baseurl"]');
    var baseUrl = basePath ? basePath.content : '';
    var jsonPath = baseUrl + '/assets/data/hpo_categories.json';

    cachePromise = fetch(jsonPath)
      .then(function(response) {
        if (!response.ok) {
          throw new Error('Failed to load HPO categories: ' + response.status);
        }
        return response.json();
      })
      .then(function(data) {
        if (data.version !== 2) {
          console.warn('Unexpected HPO categories version:', data.version);
        }
        cacheData = {
          categories: data.categories || {},
          phenotypeToCategory: data.phenotypeToCategory || {}
        };
        return cacheData;
      })
      .catch(function(err) {
        console.error('Error loading HPO categories:', err);
        cacheData = { categories: {}, phenotypeToCategory: {} };
        return cacheData;
      });

    return cachePromise;
  }

  /**
   * Group an array of phenotypes by their top-level HPO category
   *
   * @param {Array} phenotypes - Array of {hpo_id, name} objects
   * @returns {Promise<Array>} - Array of groups, each with {parent: {id, label}, phenotypes: [...]}
   */
  function groupPhenotypes(phenotypes) {
    return loadCache().then(function(cache) {
      var grouped = {};

      phenotypes.forEach(function(phenotype) {
        var categoryId = cache.phenotypeToCategory[phenotype.hpo_id] || 'uncategorized';
        var categoryInfo = cache.categories[categoryId] || null;

        if (!grouped[categoryId]) {
          grouped[categoryId] = {
            parent: categoryInfo
              ? { id: categoryId, label: categoryInfo.label }
              : { id: null, label: 'Uncategorized' },
            phenotypes: []
          };
        }

        grouped[categoryId].phenotypes.push(phenotype);
      });

      // Sort groups by parent label, with Uncategorized last
      var sortedGroups = Object.values(grouped).sort(function(a, b) {
        if (a.parent.id === null) return 1;
        if (b.parent.id === null) return -1;
        return a.parent.label.localeCompare(b.parent.label);
      });

      // Sort phenotypes within each group by name
      sortedGroups.forEach(function(group) {
        group.phenotypes.sort(function(a, b) {
          return (a.name || '').localeCompare(b.name || '');
        });
      });

      return sortedGroups;
    });
  }

  return {
    groupPhenotypes: groupPhenotypes,
    loadCache: loadCache
  };
})();
