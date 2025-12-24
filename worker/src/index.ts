export default {
  async fetch(
    request: Request,
    env: { R2_BUCKET: R2Bucket },
    ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
        },
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
      headers.set("Access-Control-Allow-Origin", "*");
      headers.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
      headers.set("Access-Control-Allow-Headers", "Content-Type");

      return new Response(obj.body, { headers });
    } catch (error) {
      console.error("Error fetching from R2:", error);
      return new Response("Internal server error", { status: 500 });
    }
  },
};
