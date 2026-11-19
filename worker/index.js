// Sends www.curve35.com and curve35.org (and its www) to https://curve35.com;
// everything else is the static site in ./public.
const REDIRECT_HOSTS = new Set(["www.curve35.com", "curve35.org", "www.curve35.org"]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (REDIRECT_HOSTS.has(url.hostname)) {
      return Response.redirect("https://curve35.com" + url.pathname + url.search, 301);
    }
    return env.ASSETS.fetch(request);
  },
};
