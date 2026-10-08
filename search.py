def build_search_query(term, category, availability, sort_selection):
    """
    Constructs parameterized SQL clauses for multi-criteria book search.
    """
    clauses = []
    params = []

    term = term.strip()
    if term:
        clauses.append("(b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)")
        pat = f"%{term}%"
        params.extend([pat, pat, pat])

    if category and category != "All Departments":
        clauses.append("b.category=?")
        params.append(category)

    if availability == "Available Only":
        clauses.append("""(b.copies - (
            SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'
        )) > 0""")
    elif availability == "Currently Borrowed":
        clauses.append("""EXISTS (
            SELECT 1 FROM loans l WHERE l.book_id=b.id AND l.status='Borrowed'
        )""")

    where = " WHERE " + " AND ".join(clauses) if clauses else ""

    sort_options = {
        "Title A–Z": "b.title COLLATE NOCASE ASC",
        "Title Z–A": "b.title COLLATE NOCASE DESC",
        "Author A–Z": "b.author COLLATE NOCASE ASC",
        "Year newest": "b.year DESC",
        "Year oldest": "b.year ASC"
    }
    sort = sort_options.get(sort_selection, "b.title COLLATE NOCASE ASC")

    return where, params, sort