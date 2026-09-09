/**
 * ballistics.ge — tiny Cloudflare Worker that serves robots.txt and
 * sitemap.xml (Streamlit cannot serve files at the site root) and passes
 * everything else through to Railway untouched.
 *
 * Setup: Cloudflare → Workers & Pages → Create → paste this → Deploy.
 * Then Workers Routes for the zone ballistics.ge:
 *   ballistics.ge/robots.txt   -> this worker
 *   ballistics.ge/sitemap.xml  -> this worker
 * (Only those two routes; do NOT route "/*" or you'll proxy the websocket.)
 */
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/robots.txt") {
      return new Response(
        "User-agent: *\nAllow: /\nDisallow: /_stcore/\nSitemap: https://ballistics.ge/sitemap.xml\n",
        { headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "public, max-age=86400" } }
      );
    }
    if (url.pathname === "/sitemap.xml") {
      const today = new Date().toISOString().slice(0, 10);
      const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://ballistics.ge/</loc><lastmod>${today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>
</urlset>`;
      return new Response(xml, {
        headers: { "content-type": "application/xml; charset=utf-8", "cache-control": "public, max-age=86400" },
      });
    }
    return fetch(request);
  },
};
