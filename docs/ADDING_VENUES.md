# Adding a new venue type

The tracker uses a small **parser registry** so each site layout can have its own HTML parser.

## Steps

1. **Implement `VenueParser`** in `src/worldcup_tracker/parsers/your_site.py`:
   - Subclass `VenueParser` from `parsers/base.py`
   - Implement `parse(html, *, source_url, venue_name) -> list[Fixture]`
   - Map page fields to `Fixture` (teams, date/time labels, `BookingStatus`, optional `booking_url`, `fixture_slug`)

2. **Register the parser** in `src/worldcup_tracker/parsers/__init__.py`:

   ```python
   ParserRegistry.register("your_site", YourSiteParser())
   ```

3. **Add a config entry** in `config.yaml`:

   ```yaml
   venues:
     - name: "My Pub"
       url: "https://example.com/world-cup"
       parser: your_site
   ```

4. **Add tests** under `tests/`:
   - Save a recorded HTML fixture under `tests/fixtures/` (do not rely on live HTTP in CI)
   - Assert team names, dates, and booking status for representative rows
   - Add a diff test for “new fixture” and “booking changed” using edited HTML

## `Fixture.key` and diffs

Diffing keys fixtures by `fixture_slug` when present, otherwise `teams|date|time`. Prefer a stable slug from the site CMS when available.

## Booking status

Use `BookingStatus.BOOKABLE` when users can reserve (real booking URL, no walk-ins-only notice). Use `WALK_INS_ONLY` when the page states walk-ins only or the book button is a placeholder (`#`).

## Plain-text fixture lists (`big_penny`)

Some venues list matches as plain text in a single paragraph, separated by `<br>` tags (see `parsers/big_penny.py`). Find the `FIXTURES` heading, split lines on `<br>`, and parse each line with a regex for `Day DD Mon - time - Teams`. Generate a stable `fixture_slug` prefix (e.g. `big-penny/...`) when the CMS does not provide per-match URLs. Use `BOOKABLE` when the page directs users to book a table without per-match walk-in notices.
