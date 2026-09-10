# Security Policy

## Reporting a vulnerability

If you find a security issue in RafRadar, please report it privately rather than
opening a public issue.

- Open a [private security advisory](https://github.com/FlyerFukas/rafradar/security/advisories/new)
  on this repository, or
- contact the maintainer through the GitHub profile [@FlyerFukas](https://github.com/FlyerFukas)

Please include what you found, how to reproduce it, and what an attacker could do
with it. You can expect a first response within a few days. If the report is valid
you will be credited in the fix unless you prefer otherwise.

## Supported versions

This is a single-branch project. Fixes land on `main`; there are no maintained
release branches.

| Version | Supported |
|---|---|
| `main` | ✅ |
| older commits | ❌ |

## Security-relevant design notes

Some properties of this tool are worth stating explicitly, because they shape what
a vulnerability would mean here.

**The control panel binds to localhost only.** `src/panel.py` listens on
`127.0.0.1`, so it is not reachable from the network. It has no authentication by
design — do not expose it through a tunnel, reverse proxy or port forward. Anyone
who can reach the panel can execute the pipeline steps on that machine.

**The panel runs a fixed set of commands.** Steps are defined in a hardcoded
dictionary and the requested step name is checked against it; a request cannot
supply an arbitrary command. Requests are also serialised, so a run cannot be
started while another is in progress.

**Configuration files are trusted input.** `yapilandirma/*.json` is read as
configuration, not as untrusted data. Do not run a configuration file you did not
write or review — the search terms it contains are sent to third-party sites.

**Scraped content is treated as data, never as instructions.** Product titles,
brand fields and prices are parsed and escaped before being rendered into the HTML
dashboard. If you extend the templating, keep escaping anything that came from a
scraped page.

**No credentials are stored in this repository.** The Trendyol channel shells out
to the Firecrawl CLI, which holds its own credentials outside the project. Do not
commit API keys; `yapilandirma/aktif.json` is gitignored precisely because it is
the file users edit locally.

**No personal data is collected.** Only product name, brand, price and rank are
recorded. Reviewer identities, user profiles and seller personal details are not
read or stored. If you extend a channel adapter, keep it that way.

## Responsible use

RafRadar reads publicly visible search result pages. Ensuring that your use of it
complies with the terms of service of the sites being queried, and with applicable
law in your jurisdiction, is your responsibility as the operator. Keep request
volumes modest — the shipped adapters wait between requests for this reason.
