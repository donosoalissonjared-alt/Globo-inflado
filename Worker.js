export default {
  async fetch(request) {
    if (request.method !== "POST") {
      return new Response("Only POST allowed", { status: 405 });
    }

    const data = await request.json();

    const webhook = "https://discord.com/api/webhooks/1449363498189586463/dFR-OKLo9JykIFHdJeJRNfWWIBuH3rGyH_A89ox0n_9OqIEep0ezY0ScEBz0LZydz2-4";

    await fetch(webhook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: `🚨 **New Report**\n👤 Player: ${data.player}\n📝 Reason: ${data.reason}`
      })
    });

    return new Response("OK");
  }
};
