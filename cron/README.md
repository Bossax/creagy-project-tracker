# Scheduling weekly reports

The weekly reporting CLI in `scripts/generate_weekly_reports.py` can be
scheduled via `cron` or any other automation tooling. The example below runs
the Markdown, CSV, and email digests every Monday at 07:00.

```
0 7 * * 1 cd /path/to/creagy-project-tracker \
  && python -m venv .venv \
  && ./.venv/bin/python -m pip install -r requirements.txt \
  && ./.venv/bin/python scripts/generate_weekly_reports.py \
       --output reports/weekly.md \
       --csv reports/weekly.csv \
       --email reports/weekly-email.txt
```

For environments where the dashboard export is used instead of direct database
access, provide the `--source export --export-path /path/to/export.json`
options. Ensure the command runs with permissions to create or update files in
the `reports/` directory.
