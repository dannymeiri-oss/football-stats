# DIN UPPDATERADE "SVARTA LISTA"
    cols_to_remove = [
        'get', 'parameters.league', 'parameters.season', 'paging.current', 'paging.total',
        'results', 'errors', 'response.fixture.id', 'response.fixture.timezone', 
        'response.fixture.timestamp', 'response.fixture.periods.first', 
        'response.fixture.periods.second', 'response.fixture.status.short', 
        'response.fixture.venue.id', 'response.fixture.status.elapsed', 
        'response.fixture.status.extra', 'response.league.id', 'response.league.logo', 
        'response.league.flag', 'response.league.round', 'response.league.standings',
        'response.teams.home.id', 'response.teams.home.logo', 'response.teams.home.winner',
        'response.teams.away.id', 'response.teams.away.logo', 'response.teams.away.winner',
        'response.score.extratime.home', 'response.score.extratime.away',
        'response.score.penalty.home', 'response.score.penalty.away'
    ]
    
    # Ta bort de exakta namnen ovan
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns])

    # EXTRA RENSNING: Ta bort allt som innehåller "errors." (som errors.1, errors.2 osv)
    df = df.drop(columns=[c for c in df.columns if 'errors.' in c])
