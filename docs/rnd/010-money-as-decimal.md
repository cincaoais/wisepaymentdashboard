# 010 – Money as Decimal, never float
Date: 3 October 2026
Roadmap step: Step 0.5, Q12 (also feeds Step 2.3 "amount precision" and Step 3.1 "`parse_float`")

## Question
- Why must money never be a `float`? Prove it in a Python shell with `0.1 + 0.2`.
- Extra: Django `DecimalField` vs `FloatField`, and PostgreSQL `numeric` vs `double precision`. How do JSON numbers from Wise become `Decimal` instead of `float`, also through `requests`? Currencies have different numbers of decimals: what `decimal_places` do we choose? Which rounding mode?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Floating-Point Arithmetic: Issues and Limitations | https://docs.python.org/3/tutorial/floatingpoint.html | docs.python.org | official doc | 2026-10-02 (Python 3.14.8 docs) | 0.1 has no exact base-2 form; floats are IEEE 754 doubles; `decimal` suits accounting |
| S2 | `decimal` module | https://docs.python.org/3/library/decimal.html | docs.python.org | official doc | 2026-10-02 (Python 3.14.8 docs) | Decimals are exact; errors in floats accumulate; `Decimal(float)` keeps the float's exact binary value; `FloatOperation` trap; `ROUND_HALF_UP` / `ROUND_HALF_EVEN`; default context `prec=28`, `ROUND_HALF_EVEN` |
| S3 | Built-in functions: `sum()` | https://docs.python.org/3/library/functions.html | docs.python.org | official doc | accessed 2026-10-03 | "Changed in version 3.12: Summation of floats switched to an algorithm that gives higher accuracy" |
| S4 | `json` module | https://docs.python.org/3/library/json.html | docs.python.org | official doc | 2026-10-02 (Python 3.14.8 docs) | JSON real → `float`, JSON int → `int`; `parse_float` is called with the number's string and can be `decimal.Decimal` |
| S5 | Requests API: `Response.json()` | https://requests.readthedocs.io/en/latest/api/ | requests.readthedocs.io | official doc | accessed 2026-10-03 (docs for v2.34.2) | `json(**kwargs)`: "Optional arguments that `json.loads` takes" |
| S6 | requests source, `models.py` at v2.34.2 | https://raw.githubusercontent.com/psf/requests/v2.34.2/src/requests/models.py | github.com | official GitHub | 2026-05-14 (v2.34.2 release) | Both code paths call `complexjson.loads(..., **kwargs)` |
| S7 | requests source, `compat.py` at v2.34.2 | https://raw.githubusercontent.com/psf/requests/v2.34.2/src/requests/compat.py | github.com | official GitHub | 2026-05-14 (v2.34.2 release) | requests uses `simplejson` if installed, otherwise the standard `json` |
| S8 | Model field reference (Django 6.1) | https://docs.djangoproject.com/en/6.1/ref/models/fields/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | `DecimalField` = `Decimal`, `max_digits`, `decimal_places`, 999.99 example; `FloatField` = `float` |
| S9 | Validators (Django 6.1) | https://docs.djangoproject.com/en/6.1/ref/validators/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | `DecimalValidator` errors: `max_digits`, `max_decimal_places`, `max_whole_digits` |
| S10 | Model instance reference (Django 6.1) | https://docs.djangoproject.com/en/6.1/ref/models/instances/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | `full_clean()` is not called by `save()`; a `ModelForm`'s `is_valid()` runs it |
| S11 | Django source, PostgreSQL backend `base.py` (stable/6.1.x) | https://raw.githubusercontent.com/django/django/stable/6.1.x/django/db/backends/postgresql/base.py | github.com | official GitHub | accessed 2026-10-03 | `DecimalField` → `numeric(max_digits, decimal_places)`; `FloatField` → `double precision` |
| S12 | Numeric Types (PostgreSQL 18) | https://www.postgresql.org/docs/current/datatype-numeric.html | postgresql.org | official doc | accessed 2026-10-03 (PostgreSQL 18 docs) | `numeric` is exact and "especially recommended for storing monetary amounts"; precision/scale; extra decimals are rounded, too many whole digits is an error; `numeric` rounds ties away from zero; `double precision` is inexact (15 digits) |
| S13 | ISO 4217 List One (current currencies) | https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml | six-group.com | official doc (ISO 4217 maintenance agency) | published 2026-09-17 | Minor units: JPY 0, KRW 0, GBP 2, EUR 2, USD 2, KWD 3, BHD 3; CLF and UYW (fund codes) 4; values used: 0, 2, 3, 4, N.A. |
| S14 | SIX: Data Standards (ISO 4217) | https://www.six-group.com/en/products-services/financial-information/data-standards.html | six-group.com | official doc | accessed 2026-10-03 | "SIX is the official Maintenance Agency of these currency codes under ISO 4217" |
| S15 | Wise API reference: Quote | https://docs.wise.com/api-reference/quote | docs.wise.com | official doc | accessed 2026-10-03 | `rate`, `sourceAmount`, `targetAmount` are JSON numbers; example `"rate": 1.30445`, `"sourceAmount": 100`, `"targetAmount": 129.24` |

## Experiment (request, response, screenshots – token removed)
Run by Claude on 3 October 2026, from the repo root, with the repo's `.venv` (Python 3.14.2) and the local PostgreSQL 18.4. No token is involved. **Re-run every command yourself**, then type the same lines into the interactive `python` shell.

**E1. Float vs Decimal, and the `Decimal(float)` trap**
```text
$ .venv/bin/python -c "print(0.1 + 0.2); print(0.1 + 0.2 == 0.3)"
0.30000000000000004
False
$ .venv/bin/python -c "from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2')); print(Decimal('0.1') + Decimal('0.2') == Decimal('0.3'))"
0.3
True
$ .venv/bin/python -c "from decimal import Decimal; print(Decimal(0.1)); print(Decimal(0.1) + Decimal(0.2) == Decimal('0.3'))"
0.1000000000000000055511151231257827021181583404541015625
False
```

**E2. Adding 0.10 ten times** (`sum()` hides the error; a normal loop shows it)
```text
$ .venv/bin/python -c "from decimal import Decimal; print(sum([0.10] * 10)); print(sum([Decimal('0.10')] * 10))"
1.0
1.00
$ .venv/bin/python -c "t = 0.0
for _ in range(10): t += 0.10
print(t, t == 1.0)"
0.9999999999999999 False
$ .venv/bin/python -c "from decimal import Decimal
t = Decimal('0')
for _ in range(10): t += Decimal('0.10')
print(t, t == 1)"
1.00 True
```

**E3. JSON from Wise: default vs `parse_float=Decimal`** (values from the Wise quote example [S15])
```text
$ .venv/bin/python -c "import json; d = json.loads('{\"sourceAmount\": 100, \"rate\": 1.30445}'); print(d, type(d['rate']).__name__)"
{'sourceAmount': 100, 'rate': 1.30445} float
$ .venv/bin/python -c "import json; from decimal import Decimal; d = json.loads('{\"sourceAmount\": 100, \"rate\": 1.30445}', parse_float=Decimal); print(d, type(d['rate']).__name__)"
{'sourceAmount': 100, 'rate': Decimal('1.30445')} Decimal
```
`requests` is not in `.venv` yet, so this one ran in a throwaway uv environment in `/tmp` (the repo's `.venv` was not changed). `r._content` is a private attribute, set here only to fake a response body. After Step 1.2 you can run the Python part with `.venv/bin/python`.
```text
$ cd /tmp && env -u VIRTUAL_ENV uv run --no-project --python 3.14 --with requests==2.34.2 python -c "
import requests; from decimal import Decimal
r = requests.models.Response(); r._content = b'{\"sourceAmount\": 100, \"rate\": 1.30445, \"targetAmount\": 129.24}'; r.encoding = 'utf-8'
print(requests.__version__)
print(r.json())
print(r.json(parse_float=Decimal))"
Installed 5 packages in 13ms
2.34.2
{'sourceAmount': 100, 'rate': 1.30445, 'targetAmount': 129.24}
{'sourceAmount': 100, 'rate': Decimal('1.30445'), 'targetAmount': Decimal('129.24')}
```

**E4. Rounding in Python** (columns: input, `ROUND_HALF_UP`, `ROUND_HALF_EVEN`)
```text
$ .venv/bin/python -c "import decimal; print(decimal.getcontext().rounding, decimal.getcontext().prec)"
ROUND_HALF_EVEN 28
$ .venv/bin/python -c "from decimal import Decimal as D, ROUND_HALF_UP as UP, ROUND_HALF_EVEN as EVEN; [print(x, D(x).quantize(D('0.01'), rounding=UP), D(x).quantize(D('0.01'), rounding=EVEN)) for x in ['2.345', '2.355', '-2.345']]"
2.345 2.35 2.34
2.355 2.36 2.36
-2.345 -2.35 -2.34
```

**E5. The same in PostgreSQL** (read-only `SELECT`s in the default `postgres` database; nothing is created)
```text
$ PGCONNECT_TIMEOUT=5 psql -X -d postgres -w -c "SELECT 0.1::double precision + 0.2::double precision AS float_sum, 0.1::numeric + 0.2::numeric AS numeric_sum, (0.1::double precision + 0.2::double precision) = 0.3::double precision AS float_equal, 2.345::numeric(10,2) AS numeric_round_1, 2.355::numeric(10,2) AS numeric_round_2, -2.345::numeric(10,2) AS numeric_round_neg;"
      float_sum      | numeric_sum | float_equal | numeric_round_1 | numeric_round_2 | numeric_round_neg
---------------------+-------------+-------------+-----------------+-----------------+-------------------
 0.30000000000000004 |         0.3 | f           |            2.35 |            2.36 |             -2.35
(1 row)
$ PGCONNECT_TIMEOUT=5 psql -X -d postgres -w -c "SELECT 1000.00::numeric(5,2) AS too_big;"
ERROR:  numeric field overflow
DETAIL:  A field with precision 5, scale 2 must round to an absolute value less than 10^3.
$ PGCONNECT_TIMEOUT=5 psql -X -d postgres -w -c "SELECT 129.24::numeric(19,4) AS stored_amount, 1.30445::numeric(20,10) AS stored_rate;"
 stored_amount | stored_rate
---------------+--------------
      129.2400 | 1.3044500000
(1 row)
```

**E6. Two safety facts**
```text
$ .venv/bin/python -c "import decimal; decimal.getcontext().traps[decimal.FloatOperation] = True; decimal.Decimal(0.1)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import decimal; decimal.getcontext().traps[decimal.FloatOperation] = True; decimal.Decimal(0.1)
                                                                               ~~~~~~~~~~~~~~~^^^^^
decimal.FloatOperation: [<class 'decimal.FloatOperation'>]
$ .venv/bin/python -c "from decimal import Decimal; print(Decimal(1) / Decimal(3)); print(Decimal(1) / Decimal(3) * 3)"
0.3333333333333333333333333333
0.9999999999999999999999999999
```

## Finding (in your own words)
**Direct answer.** A `float` stores a number in base 2. Most decimal fractions, like 0.1, have no exact base-2 form, so Python keeps the closest value it can [S1]. That is why `0.1 + 0.2` printed `0.30000000000000004` and `== 0.3` was `False` (E1). These small errors break equality checks and can add up [S2]. Money must be exact to the cent, so a float is the wrong type.

**The one thing to remember: money is a `Decimal` made from a string (or parsed straight from JSON as `Decimal`). It is never a `float`, not even for one line of code.**

- `Decimal('0.1')` is exact. `Decimal(0.1)` copies the float's error into the Decimal (E1) [S2]. Once a value has been a float, the damage is done.
- The `sum()` demo is misleading in Python 3.12+. `sum()` now adds floats with a more accurate method [S3], so `sum([0.10] * 10)` gave `1.0`. A normal `+=` loop still gave `0.9999999999999999` (E2). Real code adds step by step.
- `Decimal` is exact for base-10 numbers like 0.1 or 129.24. It still rounds results that need more than 28 significant digits, like 1/3 (E6) [S2].

**Django and PostgreSQL**

| | `FloatField` | `DecimalField` |
|---|---|---|
| Python type | `float` [S8] | `Decimal` [S8] |
| PostgreSQL column Django creates | `double precision` [S11] | `numeric(max_digits, decimal_places)` [S11] |
| Exact? | No. About 15 digits, inexact [S12] | Yes. PostgreSQL recommends it for money [S12] |

- `max_digits` = all digits (PostgreSQL calls it *precision*). `decimal_places` = digits after the point (*scale*) [S8][S12]. `max_digits=5, decimal_places=2` holds up to 999.99 [S8].
- Too many decimals: PostgreSQL **rounds silently**. Too many whole digits: **error** [S12] (E5).
- Django's `DecimalValidator` rejects too many digits or decimals [S9]. But validators run in forms (`is_valid()`) and `full_clean()`, **not** in `save()` [S10]. Code that saves without validating gets PostgreSQL's silent rounding.

**JSON and `requests`**
- In JSON, a number with a decimal point becomes a `float` by default. A whole number becomes an `int` [S4]. Wise sends `rate`, `sourceAmount` and `targetAmount` as JSON numbers [S15].
- Fix: `parse_float=Decimal`. `json` gives `Decimal` the number's original text, e.g. `"1.30445"`, so no float is ever made [S4] (E3).
- `requests`: `Response.json(**kwargs)` takes the same options as `json.loads` [S5]. The source passes `**kwargs` to `loads` in both of its code paths [S6]. So `response.json(parse_float=Decimal)` works (E3).
- Whole numbers like `100` stay `int`. That is exact, and `Decimal` + `int` works.
- requests uses `simplejson` instead of `json` if it is installed [S7]. It is not in our package list (see note 013).

**Currencies have different numbers of decimals** (ISO 4217 "minor units" [S13]; SIX maintains ISO 4217 [S14])

| Currency | Decimals |
|---|---|
| JPY, KRW | 0 |
| GBP, EUR, USD | 2 |
| KWD, BHD (also IQD, JOD, LYD, OMR, TND) | 3 |
| CLF, UYW (fund codes, not everyday money) | 4, the highest in the list |

So "2 decimal places" is only true for some currencies.

**Rounding modes**
- `ROUND_HALF_UP`: a tie goes away from zero (2.345 → 2.35). `ROUND_HALF_EVEN`: a tie goes to the even digit (2.345 → 2.34) [S2].
- Python's default is `ROUND_HALF_EVEN` [S2]. PostgreSQL `numeric` rounds ties away from zero, like `ROUND_HALF_UP` [S12]. Same number, two systems, two answers (E4 vs E5).

Roadmap correction: the Glossary says "`Decimal`: Python's exact number type". That is too strong. Better: "exact for decimal numbers such as 0.1; it still rounds results that need more than 28 digits, such as 1/3" [S2]. Q12 itself and the Step 3.1 `parse_float` hint are correct.

## Decision (what you will do and why)
1. **Amounts** (amount, fee, balance): `DecimalField`, `max_digits=19`, `decimal_places=4`, which becomes `numeric(19,4)`. Why: 4 is the most decimals any ISO 4217 code uses [S13], so PostgreSQL never has to round a real amount [S12]. 15 whole digits is plenty, even for large 0-decimal amounts like JPY. One shape for every amount means one rule to remember.
2. **A currency column next to every amount** (3-letter ISO 4217 code). Why: the code says how many decimals are valid and how to show the amount. Roadmap Step 2.3 already asks for this.
3. **Rates**: `DecimalField`, `max_digits=20`, `decimal_places=10`, which becomes `numeric(20,10)`. Why: a rate is not money. Wise's example already has 5 decimals [S15], and small rates need more. Check real rates first (Open questions).
4. **No `FloatField`** for any amount, fee or rate. Why: inexact [S8][S12].
5. **Parse every Wise response with `parse_float=Decimal`**, inside the single Wise client (Step 3.1). Why: a float must never exist, even briefly [S2][S4][S5].
6. **Make Decimals from strings**, like `Decimal('0.10')`, never from floats. Why: E1 [S2].
7. **Rounding**: store Wise's numbers exactly as sent. Reject user input with more decimals than its currency allows; do not round it. When the app must round (for example, for display), round in Python and always name the mode: `ROUND_HALF_UP`. Why: PostgreSQL `numeric` uses the same rule [S12], so Python and the database agree. Python's default would differ without warning [S2].
8. **Display** with the currency's decimals, not the column's. The column gives back `129.2400` (E5); show `129.24 GBP`.

## Open questions
- How many decimals do real sandbox rates have? Check in Postman (Step 0.6). Widen the rate column before the first migration if needed.
- Does Wise send any amount as a JSON **string**, e.g. in balances or transfers? `parse_float` only handles numbers.
- Should tests switch on the `FloatOperation` trap, so an accidental float fails loudly (E6) [S2]?
- If the dashboard ever totals many amounts, is `ROUND_HALF_EVEN` better there? Decide then.
