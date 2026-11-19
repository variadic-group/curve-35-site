# CURVE 35

A 35 mm film camera you print and build yourself: nine pieces, no tools, no glue, ages 14 and up.
Free lessons explain every part. **Site: [curve35.com](https://curve35.com)**

Made by Variadic Group LLC. Build-it-yourself learning kits; CURVE 35 is the first.

## What is here

| Folder | What it holds |
|---|---|
| `public/` | The whole website, as served: pages, lessons, simulations, films |
| `public/downloads/` | Print files (STL), the OpenSCAD model, the printed guide and print sheets (PDF) |
| `model/` | The OpenSCAD source of the camera (`one135.scad`) and its motion study |
| `tools/` | The Python checks that test the design: light, fit, motion, printing and sound |
| `brand/` | The logos (trademarks; see below) |

## Print one

1. Download the STL files from `public/downloads/` (or from [curve35.com/files](https://curve35.com/files)).
2. Print them at 0.2 mm layers with no supports, about 9 hours in all. The print sheets PDF lists each part.
3. Add one lens and follow the guide: [curve35.com/start](https://curve35.com/start).

## Change it

Open `model/one135.scad` in OpenSCAD. Share your remix with credit: "CURVE 35 by Variadic Group LLC,
curve35.com". Post it at [curve35.com/builds](https://curve35.com/builds) or tag #curve35.

## Licence

- **Designs, print files, guides, lessons and films:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
  Print, change, remix and teach with them, with credit, sharing alike. Not for selling.
- **Code** (the site's code and `tools/`): MIT.
- **The CURVE 35 name and logos** are trademarks and are not licensed.

Want to sell kits or printed copies? Email hello@curve35.com. Full terms: [LICENSE.md](LICENSE.md).

## Hosting

Cloudflare Workers static assets serve `public/` (`wrangler.jsonc`), deployed by Workers Builds on
every push to `main`. `public/_redirects` holds the short links the printed guide's QR codes use;
`public/_headers` sets the security headers.

## Contact

hello@curve35.com · support@curve35.com · schools@curve35.com · (209) 528-9554
Variadic Group LLC, 2108 N St #18255, Sacramento, CA 95816
