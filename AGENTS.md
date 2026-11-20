# Working on this repo

The public half of **CURVE 35**: the website as served (`public/`), the camera's model (`model/`),
the checks that test the design (`tools/`), the logos (`brand/`) and the small Worker in front of
the site (`worker/`, `wrangler.jsonc`). `README.md` says what each folder holds and how it is hosted.

- **`public/`, `model/` and `tools/` are copies.** They are written from the project's source, which
  is kept elsewhere, so a change made only here is overwritten by the next publish. Report a fault
  or send a patch, and it is carried into the source. `worker/`, `wrangler.jsonc`, `README.md`,
  `LICENSE.md` and this file live only here.
- **A push to `main` is the release.** Cloudflare Workers Builds deploys it to curve35.com in about
  two minutes. Done means the live files match what was pushed.
- **Every claim is true as written,** and each number has one source. Do not edit a figure here.
- **Nothing but the site's own files:** no remote asset, no tracker, no alert, confirm, prompt or
  print; every file under 25 MiB; it works by keyboard, keeps AA contrast and honours reduced motion.
- **The look is judged on a phone first, a tablet second and a desktop last.** The home page has the
  same sections in the same order on every screen.
- **Nothing about costs, suppliers or plans belongs here,** and no vendor is named.
- **Card checkout is switched off** until its switch and key are set in Cloudflare
  (`worker/index.js`). A key never goes in a file.
- **Commits:** Conventional Commits, a body that says why, no AI attribution.
- **Licence:** designs, print files, guides, lessons and films CC BY-NC-SA 4.0; code MIT; the name
  and logos are trademarks (`LICENSE.md`).
