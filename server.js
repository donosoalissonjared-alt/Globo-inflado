const TelegramBot = require("node-telegram-bot-api");
const express = require("express");
const app = express();

const TOKEN = "8406005292:AAFmxJcpRYEi5D5J7fRQXyccqjhL7oSdufo";
const bot = new TelegramBot(TOKEN, { polling: true });

let users = [];

// biar glitch tetap hidup
app.get("/", (req, res) => {
  res.send("Bot is running!");
});
app.listen(3000);

// simpan user yg start bot
bot.onText(/\/start/, (msg) => {
  const id = msg.chat.id;

  if (!users.includes(id)) users.push(id);

  bot.sendMessage(id, "Bot aktif bang!\nGunakan:\n/bc pesan");
});

// broadcast
bot.onText(/\/bc (.+)/, (msg, match) => {
  const pengirim = msg.chat.id;
  const teks = match[1];

  users.forEach((u) => {
    bot.sendMessage(u, teks).catch(() => {});
  });

  bot.sendMessage(pengirim, "Broadcast terkirim bang!");
});
