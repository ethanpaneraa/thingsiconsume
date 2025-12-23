export default {
  async fetch(
    request: Request,
    env: { R2_BUCKET: R2Bucket },
    ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);

    // Debug: list some objects to see what bucket this binding points at
    if (url.pathname === "/debug-list") {
      const list = await env.R2_BUCKET.list({
        prefix: "images/2025/12/22",
        limit: 20,
      });
      const keys = list.objects.map((o) => o.key);
      console.log("R2 list result:", keys);
      return new Response(JSON.stringify(keys, null, 2), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (!url.pathname.startsWith("/images/")) {
      return new Response("Not found", { status: 404 });
    }

    const key = url.pathname.slice(1);
    console.log("Fetching key from R2:", key);

    try {
      const obj = await env.R2_BUCKET.get(key);
      if (!obj) {
        console.log("R2 object not found for key:", key);
        return new Response("Not found", { status: 404 });
      }

      const headers = new Headers();
      const contentType =
        obj.httpMetadata?.contentType || "application/octet-stream";
      headers.set("Content-Type", contentType);
      headers.set("Cache-Control", "public, max-age=31536000, immutable");
      if (obj.httpEtag) headers.set("ETag", obj.httpEtag);

      return new Response(obj.body, { headers });
    } catch (error) {
      console.error("Error fetching from R2:", error);
      return new Response("Internal server error", { status: 500 });
    }
  },
};
