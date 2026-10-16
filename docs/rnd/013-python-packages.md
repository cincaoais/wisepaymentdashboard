# 013 – Python packages and how to record them
Date: 3 October 2026
Roadmap step: Step 1.2 (Install packages)

## Question
- "Install these with `uv pip install`. For each one, open its docs and write one line on what it does": `psycopg[binary]`, `django-environ`, `requests`, `pytest-django`, `responses`.
- "Then record your dependencies in a `requirements.txt` file. R&D: how does `uv pip freeze` help?"
- Extra: latest version and release date of each; does each support Python 3.14 and Django 6.1? Why does the dependency list have more than five lines? Why does zsh say "no matches found"? `psycopg[binary]` or build from source? How does uv's project mode (`pyproject.toml` + `uv.lock`) compare?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | psycopg on PyPI | https://pypi.org/project/psycopg/ | pypi.org | official doc | 3.3.6 released 2026-09-18 | Latest version; Requires Python >=3.10; classifiers 3.10–3.15 |
| S2 | django-environ on PyPI | https://pypi.org/project/django-environ/ | pypi.org | official doc | 0.14.0 released 2026-06-18 | Latest version; classifiers Python 3.9–3.14, Django 2.2–6.0 (no 6.1) |
| S3 | requests on PyPI | https://pypi.org/project/requests/ | pypi.org | official doc | 2.34.2 released 2026-05-14 | Latest version; classifiers 3.10–3.15 |
| S4 | pytest-django on PyPI | https://pypi.org/project/pytest-django/ | pypi.org | official doc | 4.14.0 released 2026-08-10 | Latest version; classifiers Python 3.10–3.14, Django 5.2 and 6.0 |
| S5 | responses on PyPI | https://pypi.org/project/responses/ | pypi.org | official doc | 0.26.3 released 2026-08-26 | Latest version; Requires Python >=3.8; classifiers stop at 3.13 |
| S6 | Psycopg 3 documentation | https://www.psycopg.org/psycopg3/docs/ | psycopg.org | official doc | accessed 2026-10-03 (docs 3.3.7.dev1) | "a newly designed PostgreSQL database adapter for the Python programming language" |
| S7 | Psycopg 3: Installation | https://www.psycopg.org/psycopg3/docs/basic/install.html | psycopg.org | official doc | accessed 2026-10-03 (docs 3.3.7.dev1) | Binary vs local vs pure Python install; quoted `pip install "psycopg[binary]"`; local install is "the preferred way ... for a production site"; supports Python 3.10–3.15, PostgreSQL 10–18 |
| S8 | Databases: PostgreSQL notes (Django 6.1) | https://docs.djangoproject.com/en/6.1/ref/databases/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | Django needs psycopg 3.1.12+ (or psycopg2 2.9.9+); PostgreSQL 15+; psycopg2 "likely to be deprecated" |
| S9 | django-environ documentation | https://django-environ.readthedocs.io/en/latest/ | django-environ.readthedocs.io | official doc | accessed 2026-10-03 (page shows v0.13.0) | Configures Django from environment variables and a `.env` file (Twelve-factor) |
| S10 | django-environ CHANGELOG | https://raw.githubusercontent.com/joke2k/django-environ/main/CHANGELOG.rst | github.com | official GitHub | v0.14.0 dated 18 June 2026 | No mention of Django 6.1 |
| S11 | Requests documentation | https://requests.readthedocs.io/en/latest/ | requests.readthedocs.io | official doc | accessed 2026-10-03 (Release v2.34.2) | "an elegant and simple HTTP library for Python"; "officially supports Python 3.10+" |
| S12 | pytest-django documentation | https://pytest-django.readthedocs.io/en/latest/ | pytest-django.readthedocs.io | official doc | accessed 2026-10-03 | "a plugin for pytest that provides a set of useful tools for testing Django applications" |
| S13 | pytest-django changelog | https://raw.githubusercontent.com/pytest-dev/pytest-django/main/docs/changelog.rst | github.com | official GitHub | accessed 2026-10-03 | 4.12.0: official Python 3.14 and Django 6.0 support; "v4.15.0 (unreleased): Official Django 6.1 support" |
| S14 | getsentry/responses README | https://github.com/getsentry/responses | github.com | official GitHub | accessed 2026-10-03 | "A utility library for mocking out the `requests` Python library"; Python 3.8+, requests >= 2.30.0 |
| S15 | responses CHANGES | https://raw.githubusercontent.com/getsentry/responses/master/CHANGES | github.com | official GitHub | accessed 2026-10-03 | "Added Python 3.14 support" is under **Unreleased**, after 0.26.3 |
| S16 | uv: The pip interface | https://docs.astral.sh/uv/pip/ | docs.astral.sh | official doc | 2024-08-08 | `uv pip` gives "low-level commands"; other uv commands "operate at a higher level of abstraction" and manage the venv automatically |
| S17 | uv: Inspecting environments | https://docs.astral.sh/uv/pip/inspection/ | docs.astral.sh | official doc | 2025-06-10 | `uv pip freeze` lists all packages "in a `requirements.txt` format" |
| S18 | uv: Locking environments | https://docs.astral.sh/uv/pip/compile/ | docs.astral.sh | official doc | 2026-07-23 | Why lock exact versions: to reproduce the environment; without it versions change over time |
| S19 | uv: Creating projects | https://docs.astral.sh/uv/concepts/projects/init/ | docs.astral.sh | official doc | 2026-10-01 | `uv init --bare` skips README, `.python-version`, source folders and git; only `pyproject.toml` |
| S20 | uv: Managing dependencies | https://docs.astral.sh/uv/concepts/projects/dependencies/ | docs.astral.sh | official doc | 2026-08-14 | `uv add` writes `project.dependencies`, updates the lockfile and the env; `--dev` writes `[dependency-groups] dev`; dev group synced by default; dev deps are local-only |
| S21 | uv: Locking and syncing | https://docs.astral.sh/uv/concepts/projects/sync/ | docs.astral.sh | official doc | 2026-08-05 | Locking and syncing are automatic; `uv sync` is exact by default (removes packages not in the lockfile); `--inexact`; `--all-groups`; `--locked`/`--frozen` |
| S22 | uv: Project structure and files | https://docs.astral.sh/uv/concepts/projects/layout/ | docs.astral.sh | official doc | 2026-07-21 | `uv.lock` is universal (cross-platform), managed by uv, not edited by hand, "should be checked into version control"; don't commit `.venv` |
| S23 | uv: Exporting a lockfile | https://docs.astral.sh/uv/concepts/projects/export/ | docs.astral.sh | official doc | 2026-09-28 | `uv export --format requirements.txt` is for other tools; "we recommend against using both a `uv.lock` and a `requirements.txt` file" |
| S24 | uv: Configuring projects | https://docs.astral.sh/uv/concepts/projects/config/ | docs.astral.sh | official doc | 2026-09-18 | No `[build-system]` → uv installs only the dependencies, not the project; default env is `.venv` in the project root; warning when `VIRTUAL_ENV` points elsewhere |
| S25 | zsh manual: Options | https://zsh.sourceforge.io/Doc/Release/Options.html | zsh.sourceforge.io | official doc | accessed 2026-10-03 | `NOMATCH <C> <Z>`: "If a pattern for filename generation has no matches, print an error"; `<Z>` = on by default in zsh |

## Experiment (request, response, screenshots – token removed)
Run by Claude on 3 October 2026 with uv 0.12.21, **only in `/tmp`**. The repo's `.venv` was checked before and after: it still holds only `asgiref`, `django`, `sqlparse`. Both temp folders were deleted at the end. uv picked CPython 3.14.3 for the temp environments; the repo's `.venv` has 3.14.2. **Re-run this yourself in `/tmp` before you touch the repo.**

**E1. Background: the pip-style way (`uv pip install` + `uv pip freeze`)**
```text
$ uv venv /tmp/wpd-freeze-test --python 3.14
Using CPython 3.14.3
Creating virtual environment at: /tmp/wpd-freeze-test
Activate with: source /tmp/wpd-freeze-test/bin/activate
$ uv pip install --python /tmp/wpd-freeze-test django 'psycopg[binary]' django-environ requests pytest-django responses
Using Python 3.14.3 environment at: /tmp/wpd-freeze-test
Resolved 19 packages in 150ms
Installed 19 packages in 96ms
[19 lines "+ name==version" cut here: the same list as the freeze output below]
$ uv pip freeze --python /tmp/wpd-freeze-test
Using Python 3.14.3 environment at: /tmp/wpd-freeze-test
asgiref==3.12.1
certifi==2026.7.22
charset-normalizer==3.5.2
django==6.1.1
django-environ==0.14.0
idna==3.20
iniconfig==2.3.0
packaging==26.3
pluggy==1.6.0
psycopg==3.3.6
psycopg-binary==3.3.6
pygments==2.21.0
pytest==9.1.1
pytest-django==4.14.0
pyyaml==6.0.3
requests==2.34.2
responses==0.26.3
sqlparse==0.6.0
urllib3==2.8.0
$ uv pip tree --python /tmp/wpd-freeze-test
Using Python 3.14.3 environment at: /tmp/wpd-freeze-test
django v6.1.1
├── asgiref v3.12.1
└── sqlparse v0.6.0
django-environ v0.14.0
psycopg v3.3.6
psycopg-binary v3.3.6
pytest-django v4.14.0
└── pytest v9.1.1
    ├── iniconfig v2.3.0
    ├── packaging v26.3
    ├── pluggy v1.6.0
    └── pygments v2.21.0
responses v0.26.3
├── pyyaml v6.0.3
├── requests v2.34.2
│   ├── certifi v2026.7.22
│   ├── charset-normalizer v3.5.2
│   ├── idna v3.20
│   └── urllib3 v2.8.0
└── urllib3 v2.8.0
$ /tmp/wpd-freeze-test/bin/python -c "import sys, django, psycopg, environ, requests, pytest_django, responses; print(sys.version.split()[0], 'django', django.__version__, 'psycopg', psycopg.__version__, psycopg.pq.__impl__, 'requests', requests.__version__)"
3.14.3 django 6.1.1 psycopg 3.3.6 binary requests 2.34.2
$ rm -rf /tmp/wpd-freeze-test
```
`binary` = the precompiled psycopg is in use. Its wheel tag was `cp314-cp314-macosx_11_0_arm64` (Python 3.14, Apple Silicon).

**E2. The zsh gotcha** (exit code 1; uv never ran)
```text
$ zsh -c 'uv pip install --python /tmp/wpd-freeze-test psycopg[binary]'
zsh:1: no matches found: psycopg[binary]
```

**E3. The chosen way: uv project mode**
```text
$ mkdir /tmp/wpd-uvproject-test && cd /tmp/wpd-uvproject-test
$ uv init --bare --python 3.14
Initialized project `wpd-uvproject-test`
$ uv add django "psycopg[binary]" django-environ requests
Using CPython 3.14.3
Creating virtual environment at: .venv
Resolved 13 packages in 36ms
Installed 11 packages in 127ms
[11 lines "+ name==version" cut here]
$ uv add --dev pytest-django responses
Resolved 22 packages in 7ms
Installed 8 packages in 22ms
[8 lines "+ name==version" cut here]
$ ls -A
.venv
pyproject.toml
uv.lock
$ cat pyproject.toml
[project]
name = "wpd-uvproject-test"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "django>=6.1.1",
    "django-environ>=0.14.0",
    "psycopg[binary]>=3.3.6",
    "requests>=2.34.2",
]

[dependency-groups]
dev = [
    "pytest-django>=4.14.0",
    "responses>=0.26.3",
]
$ uv sync --all-groups
Resolved 22 packages in 31ms
Checked 19 packages in 5ms
$ uv export --format requirements.txt --no-hashes --all-groups -o requirements.txt
[21 package lines, each with a "# via ..." comment. Two lines that `uv pip freeze` did not have:]
colorama==0.4.6 ; sys_platform == 'win32'
tzdata==2026.4 ; sys_platform == 'win32'
```
`uv.lock` had 22 `[[package]]` entries: the 19 installed packages, `colorama`, `tzdata`, and the project itself.

Exact-sync test (an earlier run of the same steps, same day):
```text
$ uv pip install --python /tmp/wpd-uvproject-test/.venv six
Using Python 3.14.3 environment at: /tmp/wpd-uvproject-test/.venv
Resolved 1 package in 93ms
Installed 1 package in 2ms
 + six==1.17.0
$ uv sync --all-groups
Resolved 22 packages in 3ms
Uninstalled 1 package in 0.61ms
 - six==1.17.0
```
In that earlier run the repo's `.venv` was active in Claude's shell, so uv printed ``warning: `VIRTUAL_ENV=/Users/snapdec/Documents/workspace/wisepaymentdashboard/.venv` does not match the project environment path `.venv` and will be ignored`` and left the repo alone [S24]. In the repo root both paths are the same, so you should see no warning.

## Finding (in your own words)
**How does `uv pip freeze` help?** It prints every package in the environment, each with its exact version, in `requirements.txt` format [S17]. Saving that output pins the whole environment, so you or another machine can rebuild the same versions later. Without pinning, versions drift over time [S18]. Its limits, seen in E1 and E3: it copies whatever is installed, including leftovers you forgot. It doesn't show which packages you asked for. It only lists what this Mac needs, so Windows-only packages like `tzdata` are missing.

**Remember: you ask for 6 packages and get 19. The other 13 are dependencies of your dependencies. `uv.lock` records all of them for you.**

| You asked for | It pulled in (E1 tree) |
|---|---|
| `django` | `asgiref`, `sqlparse` |
| `psycopg[binary]` | `psycopg-binary` (the `[binary]` extra) |
| `requests` | `certifi`, `charset-normalizer`, `idna`, `urllib3` |
| `pytest-django` | `pytest`, which pulls `iniconfig`, `packaging`, `pluggy`, `pygments` |
| `responses` | `pyyaml`, `requests`, `urllib3` |
| `django-environ` | nothing |

**The five packages**

| Package | What it does in this project | Official docs | Latest on PyPI | Python 3.14? | Django 6.1? |
|---|---|---|---|---|---|
| `psycopg[binary]` | The driver Django uses to talk to PostgreSQL [S6] | https://www.psycopg.org/psycopg3/docs/ | 3.3.6, 18 Sep 2026 [S1] | Yes [S1][S7] | Yes: Django 6.1 needs psycopg 3.1.12+ [S8] |
| `django-environ` | Reads `SECRET_KEY`, database settings and the Wise token from `.env` [S9] | https://django-environ.readthedocs.io/en/latest/ | 0.14.0, 18 Jun 2026 [S2] | Yes [S2] | **Unclear**: classifiers stop at 6.0 [S2]; changelog silent [S10] |
| `requests` | Makes the HTTP calls to the Wise API [S11] | https://requests.readthedocs.io/en/latest/ | 2.34.2, 14 May 2026 [S3] | Yes [S3][S11] | Not applicable (does not use Django) |
| `pytest-django` | Lets `pytest` run Django tests (settings, test database) [S12] | https://pytest-django.readthedocs.io/en/latest/ | 4.14.0, 10 Aug 2026 [S4] | Yes, since 4.12.0 [S13] | **Not official yet**: PyPI lists 5.2 and 6.0 [S4]; 6.1 is in the unreleased 4.15.0 [S13] |
| `responses` | Fakes the Wise HTTP calls in tests, so tests never hit the network [S14] | https://github.com/getsentry/responses | 0.26.3, 26 Aug 2026 [S5] | **Unclear**: classifiers stop at 3.13 [S5]; 3.14 support is "Unreleased" [S15] | Not applicable (does not use Django) |

- "Supported" here means the project says so. All six imported fine on Python 3.14.3 (E1). That is a good sign, not a promise.
- django-environ's "latest" docs still show v0.13.0 [S9], one release behind PyPI [S2].

**zsh "no matches found"**: in zsh, `[...]` is a filename pattern. zsh looks for a file matching `psycopg[binary]` and finds none. The `NOMATCH` option is on by default in zsh, so zsh prints an error and does not run the command [S25] (E2). Fix: quote it, `"psycopg[binary]"`, as the psycopg docs do [S7]. The same applies to `uv add`.

**`psycopg[binary]` vs building from source** [S7]
- Binary: ready-made C code with the PostgreSQL client library inside. No compiler needed. "Recommended for most users" and the quickest way to start developing. Builds for a new Python appear only once the build machines support it; for 3.14 on this Mac one exists (E1).
- Local (`psycopg[c]`): builds from source. Needs a C compiler, Python headers, PostgreSQL headers and `pg_config`. It links to the system's libraries, so system updates reach it. "The preferred way to install Psycopg for a production site."
- Pure Python (`psycopg`): slow, and needs `libpq` on the machine.

**uv project mode**
- `uv init --bare` writes only `pyproject.toml` [S19] (E3).
- `uv add` writes to `[project].dependencies` and updates `uv.lock` and `.venv`. `uv add --dev` writes to `[dependency-groups] dev`. Dev packages are left out if the project is ever published; the `dev` group is still installed by default [S20][S21].
- `uv.lock` is cross-platform, managed by uv, never edited by hand, and **committed**. `.venv` is not committed [S22].
- `uv sync` is **exact**: it removes anything not in `uv.lock` (E3: `six` was removed). `--inexact` turns this off [S21].
- With no `[build-system]` (as with `--bare`), uv installs only the dependencies, not the project itself [S24]. That suits a Django site.
- `uv pip` is the "low-level" interface; project commands manage the environment for you [S16]. uv advises against keeping both `uv.lock` and `requirements.txt` [S23].

Roadmap correction: Step 1.2's plan ("install these with `uv pip install`", then "record your dependencies in a `requirements.txt` file", i.e. `uv pip freeze > requirements.txt`) is **replaced by uv project mode**: `uv init --bare`, `uv add`, `uv add --dev`, then commit `pyproject.toml` and `uv.lock` [S19][S20][S22]. "Done when: Requirements file committed" becomes "`pyproject.toml` and `uv.lock` committed".

Roadmap correction: Section 3 says "Install with `uv pip install <package>`". After the switch, use `uv add <package>`. Anything installed with `uv pip install` is removed by the next `uv sync` [S21].

## Decision (what you will do and why)
1. **Use uv project mode in the repo root** (the folder with `.venv`): `uv init --bare --python 3.14`, then `uv add django "psycopg[binary]" django-environ requests`, then `uv add --dev pytest-django responses`. Why: uv records what we asked for in `pyproject.toml` and every exact version in `uv.lock`, automatically [S20][S21].
2. **Add `django` explicitly**, even though it is already in `.venv`. Why: `uv sync` is exact and would remove it if it were missing from `uv.lock` [S21].
3. **Test packages go in the `dev` group.** Why: they are for development only [S20].
4. **Commit `pyproject.toml` and `uv.lock`; never `.venv`** (already in `.gitignore`). Why: [S22].
5. **Rebuild the environment with `uv sync`** (the `dev` group is included by default; `--all-groups` also adds any future groups) [S21]. **From now on, add or remove packages only with `uv add` / `uv remove`.** Why: exact sync removes anything else.
6. **Always quote `"psycopg[binary]"`** in zsh. Why: E2 [S25].
7. **Use `psycopg[binary]`.** Why: a learning project on one Mac, no compiler setup needed [S7]. Revisit if this ever goes to a production server.
8. **No `requirements.txt` by default.** If a tool needs one: `uv export --format requirements.txt --no-hashes --all-groups -o requirements.txt`, and treat the file as generated. Why: [S23].
9. **Keep pytest-django 4.14.0 for now**; upgrade when 4.15.0 (official Django 6.1 support) is released [S13].

## Open questions
- django-environ does not declare Django 6.1 support yet [S2][S10]. Watch for problems in Step 1.4 and check its changelog.
- `responses` lists Python 3.14 support as unreleased [S15]. Watch for the next release.
- Should we add a `.python-version` file (`uv python pin 3.14`)? `--bare` skips it [S19], and `requires-python = ">=3.14"` would also accept 3.15 later.
- Should `pyproject.toml` cap Django below 6.2, so a future `uv lock --upgrade` cannot jump a feature release by accident?
