export default {
  async fetch(
    request: Request,
    env: { R2_BUCKET: R2Bucket },
    ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);

    // Only handle /images/* paths
    if (!url.pathname.startsWith("/images/")) {
      return new Response("Not found", { status: 404 });
    }

    // Extract R2 key (remove leading /images/)
    const key = url.pathname.slice(1); // "images/2025/12/22/..."

    try {
      // Fetch object from R2
      const obj = await env.R2_BUCKET.get(key);

      if (!obj) {
        return new Response("Not found", { status: 404 });
      }

      // Prepare headers
      const headers = new Headers();

      // Set Content-Type from R2 metadata or default
      const contentType =
        obj.httpMetadata?.contentType || "application/octet-stream";
      headers.set("Content-Type", contentType);

      // Set cache headers (images are immutable)
      headers.set("Cache-Control", "public, max-age=31536000, immutable");

      // Optional: Set ETag if available
      if (obj.httpEtag) {
        headers.set("ETag", obj.httpEtag);
      }

      // Return the object body with headers
      return new Response(obj.body, { headers });
    } catch (error) {
      console.error("Error fetching from R2:", error);
      return new Response("Internal server error", { status: 500 });
    }
  },
};
