# Party roles in `entity_offices.csv`

**Status: applied 2026-11-01.** The project decision is that **political affiliation is not
published**. The enrichment had left party posts in `entity_offices.csv` (free text);
the user decided to delete all of them and keep public offices (minister, MP, mayor,
assembly), which are public functions, not affiliation. Source rows pointing to a party
website were removed too.

The row-by-row review list was removed from the repository before publication, because it
named the people and their party posts.
