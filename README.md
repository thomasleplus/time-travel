# How Far Is Paris? Two Thousand Years of Travel Time

A book with isochrone maps showing how long it took to travel from Paris, from Roman times to today.

[![CI](https://github.com/thomasleplus/time-travel/actions/workflows/ci.yml/badge.svg)](https://github.com/thomasleplus/time-travel/actions/workflows/ci.yml)

## Requirements

- [Quarto](https://quarto.org) 1.4 or later
- For PDF output, a TeX distribution. The simplest is: `quarto install tinytex`
- Python 3.12 or later with `numpy` and `matplotlib` (only needed to regenerate the maps): `pip install -r requirements.txt`
  (versions are pinned with hashes in `requirements.txt`, which is generated with `uv pip compile`: see its header to update it)

## Build

```sh
quarto render                 # all formats into _book/
quarto render --to html       # website only
quarto render --to pdf        # print version
quarto render --to docx       # Word
quarto preview                # live preview while editing
```

## Layout

| Path                    | What it is                                                                                                                          |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `_quarto.yml`           | Book structure, chapter order and output formats                                                                                    |
| `index.qmd`             | Introduction and conventions                                                                                                        |
| `chapters/*.qmd`        | One file per chapter, the interlude, the comparison and the closing                                                                 |
| `references.bib`        | Every source, once, with a citation key                                                                                             |
| `references.qmd`        | The generated reference list                                                                                                        |
| `styles/numeric.csl`    | Citation style: numbered `[1]` citations in order of first use                                                                      |
| `styles/reference.docx` | Word template (edit its styles to restyle the .docx output)                                                                         |
| `data/travel_times.csv` | Every mapped travel time: era, place, coordinates, hours from Paris, sourced or estimate                                            |
| `data/known_world.json` | Areas reachable at all in the Roman and medieval eras                                                                               |
| `maps/`                 | Map code: `geo.py` (schematic coastlines), `surface.py` and `render.py` (isochrone model and drawing), `make_maps.py` (entry point) |
| `maps/output/`          | The generated maps and comparison chart used by the book                                                                            |

## Everyday tasks

**Change a travel time.** Edit the row in `data/travel_times.csv`, run `python maps/make_maps.py <era>`
(for example `python maps/make_maps.py 1914`, or no argument for everything), then update the chapter's table
text to match. The comparison chart is rebuilt every time.

**Cite a source.** Add an entry to `references.bib` and cite it in the text as `[@key]`, or `[@key1; @key2]`.
Numbering and the reference list are generated automatically.

**Add a chapter.** Create `chapters/NN-name.qmd` starting with a level-1 heading and add it to `_quarto.yml`.

## Notes

- `basis` in the CSV is `sourced` where a map node is anchored to a cited source and `estimate` otherwise.
  A few rows sourced in the text after the maps were drawn (Berlin, St Petersburg and Moscow in 1914)
  are still marked `estimate` in the CSV; update them if you want the map asterisks to match.
- The maps use hand-drawn schematic coastlines, and the travel-time surface is a model: see the introduction.
- The original document numbered sources per chapter; here they are numbered once for the whole book.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Security

Please read [SECURITY.md](SECURITY.md) for details on our security policy and how to report security vulnerabilities.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on our code of conduct.
