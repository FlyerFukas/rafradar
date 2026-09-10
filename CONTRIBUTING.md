# Contributing

Thanks for taking a look. This project is small and the bar for contributing is
low — bug reports and new channel adapters are especially welcome.

## Before you start

Run the tests. They are plain `unittest`, no extra tooling:

```bash
python -m unittest discover -s testler -p "test_*.py" -v
```

Validate that a configuration loads:

```bash
RAFRADAR_AYAR=yapilandirma/ornek-takviye.json python src/ayarlar.py
```

## Adding a sales channel

This is the most useful contribution. A channel adapter is a module with one
public function:

```python
def ara(kelime):
    return {
        "kanal": "site_adi",
        "arama": kelime,
        "urunler": [
            {
                "sira": 1,                 # rank in the result list
                "organik_sira": 1,         # rank among organic results, None if sponsored
                "marka": "Brand",
                "ad": "Product title",
                "fiyat": 249.90,           # float or None
                "sponsorlu": False,        # is this a paid placement?
                "url": "https://…",
            },
        ],
    }
```

Register it in `src/topla.py` and add its name to the `kanallar` list in a
configuration file. Two things matter more than anything else:

**Separate sponsored placements from organic results.** If a site shows carousel
or promoted cards, mark them `sponsorlu: True` and leave `organik_sira` as `None`.
Counting paid space as shelf inflates every metric downstream.

**Read prices from DOM elements, not with a regex over card text.** Cards routinely
show a sale price, a strikethrough price and a per-unit price together. Ask
yourself which one a shopper actually pays, and take that one.

Please add a test in `testler/test_kanallar.py` with a small HTML fragment for
whatever parsing rule you write. Every test there exists because a real page broke
something.

## Code style

The codebase is written in Turkish (identifiers, comments, docstrings) because it
was built for the Turkish market. Please keep new code consistent with the file
you are editing rather than switching languages mid-module. User-facing English
lives in `README.md`; Turkish lives in `README.tr.md`.

Beyond that: standard library where possible, no new dependencies without a reason,
and comments that explain *why* rather than restate the code.

## Reporting bugs

Open an issue with what you ran, what you expected and what happened. If a site's
markup changed and parsing broke, a snippet of the HTML that broke it is worth more
than a screenshot.

Security issues go through [SECURITY.md](SECURITY.md), not public issues.
