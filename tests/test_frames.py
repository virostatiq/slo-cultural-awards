from kulturne_nagrade import frames


def test_roles_join_keeps_every_role():
    all_roles = frames.roles(entity_types=None)
    assert len(all_roles) == len(frames.table("roles"))
    assert all_roles["award"].notna().all()


def test_roles_person_filter_and_age():
    r = frames.roles()
    assert set(r["entity_type"]) == {"person"}
    sourced = r.dropna(subset=["year_birth"])
    assert (sourced["age"] == sourced["year"] - sourced["year_birth"]).all()
    assert r["age_any"].notna().sum() >= r["age"].notna().sum()


def test_period_filter():
    r = frames.roles(min_year=2000, max_year=2010)
    assert r["year"].between(2000, 2010).all()


def test_coverage_shares_are_bounded():
    cov = frames.coverage()
    assert len(cov) == len(frames.awards())
    assert cov["history_share"].between(0, 1).all()
    assert cov["jury_share"].between(0, 1).all()
    assert cov["jury_known"].sum() == frames.table("editions")["jury_known"].sum() > 0


def test_shared_jury_counted_once():
    r = frames.roles()
    s = frames.jury_sittings()
    assert len(s) < (r["role"] == "jury").sum()
    assert not s.duplicated(["sitting_id", "entity_id"]).any()
    pres = s[s["awards"].apply(lambda a: "presernov-sklad" in a)]
    assert pres["awards"].apply(lambda a: "presernova-nagrada" in a).mean() > 0.9


def test_posthumous_has_no_age():
    r = frames.roles()
    assert r.loc[r["posthumous"], "age"].isna().all()


def test_entity_geography_categories():
    g = frames.entity_geography()
    assert g["entity_id"].is_unique
    placed = g[g["placed"]]
    # every placed entity is exactly one of: Ljubljana only, Ljubljana and elsewhere,
    # outside Ljubljana only
    assert ((placed["lj_only"].astype(int) + placed["prov_only"].astype(int)
             + (placed["lj"] & ~placed["lj_only"]).astype(int)) == 1).all()
    assert not (g["foreign_only"] & g["placed"]).any()
    assert (g.loc[g["lj_only"], "n_si_units"] == 1).all()


def test_places_cover_locations_and_regions_cover_units():
    places = frames.table("places")
    assert set(frames.table("entity_locations")["place"]) <= set(places["place"])
    lj = places[places["is_ljubljana"].astype(bool)]
    assert (lj["si_region"] == "Osrednjeslovenska").all()
    units = set(frames.entity_geography()["units"].explode().dropna())
    assert units <= set(frames.table("regions")["region"])


def test_one_person_jury_is_not_merged():
    s = frames.jury_sittings()
    ids = frames._sitting_ids()
    roles = frames.table("roles").query("role == 'jury'")
    size = roles.groupby("edition_id").size()
    singles = size[size == 1].index.intersection(ids.index)
    merged = ids.groupby(ids).size()
    assert (merged[ids[singles]] == 1).all()
    assert not s["awards"].apply(lambda a: "bert" in a and "presernova-nagrada" in a).any()
