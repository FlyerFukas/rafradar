# Contributing

Thanks for taking a look. This project is small and the bar for contributing is
low — bug reports and new channel adapters are especially welcome.

## Licensing of contributions

**Read this before opening a pull request.**

RafRadar is dual-licensed: free for noncommercial use under the
[PolyForm Noncommercial License 1.0.0](LICENSE), and available under a separate
paid license for commercial use ([COMMERCIAL.md](COMMERCIAL.md)).

That model only works if the project owner can license the whole codebase
commercially. If a contributed line cannot be included in a commercial license,
the model breaks for everyone.

So, by opening a pull request you confirm that:

1. The contribution is your own work, and you have the right to submit it.
2. You grant Furkan Akduman a perpetual, worldwide, irrevocable, royalty-free
   right to use, modify, sublicense and **relicense** your contribution —
   including as part of a paid commercial license — without further permission
   or compensation.
3. Your contribution does not include third-party code under a license
   incompatible with the above (copyleft code, in particular, cannot be merged).

You keep authorship of your work and remain credited in the commit history.
This is not an assignment of your copyright; it is the permission the project
needs to license the combined work.

If that is not acceptable to you, please open an issue describing the change
instead of a pull request — a described fix is still a real contribution and is
genuinely welcome.

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

## Questions about commercial use

If you want to use RafRadar inside a business, for a client, or in a product,
that needs a commercial license — see [COMMERCIAL.md](COMMERCIAL.md). Asking is
free and gets a quick answer.
