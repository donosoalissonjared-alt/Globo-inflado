export default {
  async fetch(request, env, ctx) {
    if (request.method === "POST" && new URL(request.url).pathname === "/webhook") {
      const data = await request.json();
      console.log("📞 Incoming call data:", data);

      return new Response(
        JSON.stringify({ message: "Webhook received successfully", data }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response("✅ Voice Bot Bridge Running on Edge!", {
      headers: { "Content-Type": "text/plain" },
    });
  },
};
